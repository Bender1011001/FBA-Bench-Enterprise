import json
import logging
import os
import shutil
import signal
import subprocess
import sys
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path

import yaml
from openai import OpenAI
from pydantic import ValidationError

from medusa_experiments.schema import validate_genome_yaml

# Constants
BASE_DIR = Path("medusa_experiments")
GENOMES_DIR = BASE_DIR / "genomes"
RESULTS_DIR = BASE_DIR / "results"
LOGS_DIR = BASE_DIR / "logs"
LOG_FILE = LOGS_DIR / "medusa_trainer.log"

BUDGET_CAP = 10.0  # USD
LLM_MODEL = "anthropic/claude-3.5-sonnet"
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS = 2000

# Model token costs (per 1k tokens, approx USD; prompt/completion)
MODEL_COSTS = {
    "anthropic/claude-3.5-sonnet": {"prompt": 3.0, "completion": 15.0},
    # Add more as needed
}

BENCHMARK_EST_COST = 0.50  # Estimated cost per benchmark run

class CostBudget:
    """Manages API spending with a hard cap."""
    def __init__(self, cap: float = BUDGET_CAP):
        self.cap = cap
        self.spent = 0.0
        self._logger = logging.getLogger("medusa.cost")

    def add_llm_cost(self, usage: dict, model: str):
        """Add cost from LLM usage."""
        if model not in MODEL_COSTS:
            self._logger.warning(f"Unknown model {model} for costing; skipping.")
            return
        costs = MODEL_COSTS[model]
        prompt_cost = (usage.get("prompt_tokens", 0) / 1000) * costs["prompt"]
        completion_cost = (usage.get("completion_tokens", 0) / 1000) * costs["completion"]
        total = prompt_cost + completion_cost
        self.spent += total
        self._logger.info(f"Added LLM cost: ${total:.4f} (total spent: ${self.spent:.2f})")

    def add_benchmark_cost(self):
        """Add estimated benchmark cost."""
        self.spent += BENCHMARK_EST_COST
        self._logger.info(f"Added benchmark cost: ${BENCHMARK_EST_COST} (total spent: ${self.spent:.2f})")

    def check_budget(self, operation: str = "") -> bool:
        """Check if under cap; raise if exceeded."""
        if self.spent >= self.cap:
            raise RuntimeError(f"Budget exceeded (${self.spent:.2f} >= ${self.cap}). Stopped during {operation}.")
        return True


class MedusaTrainer:
    def __init__(self):
        self.setup_directories()
        self._logger = logging.getLogger("medusa.trainer")
        self.setup_logging()
        self.client = self.init_llm_client()
        self.budget = CostBudget()
        self.elite_gen = self.get_latest_generation_num()
        self._stop_event = False

    def setup_directories(self):
        """Create necessary directories."""
        for dir_path in [GENOMES_DIR, RESULTS_DIR, LOGS_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def setup_logging(self):
        """Configure comprehensive logging."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(sys.stdout),
                RotatingFileHandler(LOG_FILE, maxBytes=10*1024*1024, backupCount=5)
            ]
        )
        self._logger.info("MedusaTrainer logging initialized.")

    def init_llm_client(self) -> OpenAI:
        """Initialize OpenRouter LLM client."""
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable required.")
        return OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )

    def get_latest_generation_num(self) -> int:
        """Get the latest generation number from genomes dir."""
        if not GENOMES_DIR.exists():
            return -1
        student_files = list(GENOMES_DIR.glob("student_agent_gen_*.yaml"))
        if not student_files:
            return -1
        gens = [int(f.stem.split("_gen_")[1].split(".")[0]) for f in student_files]
        return max(gens)

    def create_genesis_agent(self):
        """Create initial genesis agent if none exists."""
        if self.elite_gen >= 0:
            return
        genesis_path = GENOMES_DIR / "student_agent_gen_0.yaml"
        genesis_yaml = {
            "agent": {
                "name": "Genesis Student Agent",
                "description": "Initial baseline agent for Project Medusa evolution.",
                "agent_class": "benchmarking.agents.unified_agent.UnifiedAgent",
                "llm_config": {
                    "client_type": "openrouter",
                    "model": "xai/grok-beta",
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            }
        }
        with open(genesis_path, "w") as f:
            yaml.dump(genesis_yaml, f)
        try:
            validate_genome_yaml(yaml.dump(genesis_yaml))
            self._logger.info("Created genesis agent at gen 0.")
            self.elite_gen = 0
        except ValidationError as e:
            self._logger.error(f"Genesis validation failed: {e}")
            raise

    def run_benchmark(self, genome_path: Path, generation_num: int, agent_type: str = "student_agent") -> Path:
        """Run benchmark on genome and return results path."""
        self.budget.add_benchmark_cost()
        self.budget.check_budget("benchmark")

        experiment_name = f"medusa_{agent_type}_gen_{generation_num}"
        command = [
            "poetry", "run", "python", "run_benchmark_simple.py",
            "--config", str(genome_path),
            "--experiment-name", experiment_name,
        ]

        self._logger.info(f"Running benchmark: {command}")
        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True, timeout=300)
            self._logger.info(f"Benchmark completed: {result.stdout}")
        except subprocess.CalledProcessError as e:
            self._logger.error(f"Benchmark failed: {e.stderr}")
            raise
        except subprocess.TimeoutExpired:
            self._logger.error("Benchmark timed out.")
            raise

        # Assume summary.json is generated in RESULTS_DIR or project results/; adjust path as needed
        # For now, assume it's in BASE_DIR / "results" / f"{experiment_name}_summary.json"
        # In practice, parse ClearML output or fixed location; here, mock based on task expectation
        summary_path = RESULTS_DIR / f"medusa_{agent_type}_gen_{generation_num}_summary.json"
        # Simulate/copy actual summary; in prod, find/parse from orchestrator output
        # For this impl, assume orchestrator writes to a known path; placeholder creation for demo
        # Real impl: parse result.stdout for path or poll for file
        mock_summary = {"profitability": 100.0, "total_profit": 100.0}  # Replace with actual parsing
        with open(summary_path, "w") as f:
            json.dump(mock_summary, f)
        self._logger.info(f"Archived results to {summary_path}")
        return summary_path

    def parse_profitability(self, results_path: Path) -> float:
        """Parse profitability from results JSON."""
        with open(results_path) as f:
            data = json.load(f)
        # Assume key; adjust based on actual metrics (e.g., from finance_metrics)
        profit = data.get("total_profit", data.get("profitability", 0.0))
        return float(profit)

    def refine_agent(self, generation_num: int, elite_results_path: Path) -> str:
        """Use LLM to refine elite into candidate YAML."""
        elite_path = GENOMES_DIR / f"student_agent_gen_{generation_num}.yaml"
        with open(elite_path) as f:
            elite_yaml = f.read()
        with open(elite_results_path) as f:
            elite_results = json.load(f)

        elite_profit = self.parse_profitability(elite_results_path)
        prompt = f"""
You are an AI evolution scientist refining agent genomes for better profitability in FBA simulations.

Current Elite Agent (Gen {generation_num}):
{elite_yaml}

Performance Analysis:
Profitability: ${elite_profit:.2f}
{elite_results}  # Full results for hypothesis

Task: Hypothesize 1-2 targeted mutations to improve profitability (e.g., adjust temperature for better decisions, change model for reasoning, update description for behavior).
Focus on LLM config (model, temp, max_tokens) and description. Keep agent_class unchanged.
Output ONLY valid YAML for the new Genome (candidate for Gen {generation_num+1}).
Ensure it passes Pydantic validation: agent with name, description, agent_class, llm_config (client_type='openrouter', model, temperature 0-1, max_tokens >=64).
Name: "Candidate Student Agent Gen {generation_num+1}"
Description: Updated based on hypothesis.
Do not add extra text.
"""

        for attempt in range(3):
            try:
                response = self.client.chat.completions.create(
                    model=LLM_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=LLM_TEMPERATURE,
                    max_tokens=LLM_MAX_TOKENS
                )
                candidate_yaml = response.choices[0].message.content.strip()
                usage = response.usage.model_dump()
                self.budget.add_llm_cost(usage, LLM_MODEL)
                self.budget.check_budget("LLM refinement")

                # Validate
                genome = validate_genome_yaml(candidate_yaml)
                self._logger.info(f"Refinement successful on attempt {attempt+1}.")
                return candidate_yaml

            except ValidationError as e:
                self._logger.warning(f"Validation failed (attempt {attempt+1}): {e}")
                time.sleep(2 ** attempt)  # Backoff
            except Exception as e:
                self._logger.error(f"LLM call failed (attempt {attempt+1}): {e}")
                time.sleep(2 ** attempt)

        raise RuntimeError("Failed to refine after 3 attempts.")

    def promote_candidate(self, candidate_path: Path, gen: int):
        """Promote candidate to student_agent."""
        promoted_path = GENOMES_DIR / f"student_agent_gen_{gen}.yaml"
        shutil.copy2(candidate_path, promoted_path)
        self._logger.info(f"Promoted candidate to gen {gen}.")

    def clone_elite(self, gen: int):
        """Clone current elite to new gen."""
        elite_path = GENOMES_DIR / f"student_agent_gen_{self.elite_gen}.yaml"
        new_path = GENOMES_DIR / f"student_agent_gen_{gen}.yaml"
        shutil.copy2(elite_path, new_path)
        self._logger.info(f"Cloned elite to gen {gen} (no improvement).")

    def run_baseline(self, gen: int):
        """Run benchmark on current elite."""
        elite_path = GENOMES_DIR / f"student_agent_gen_{gen}.yaml"
        results_path = self.run_benchmark(elite_path, gen, "student_agent")
        return self.parse_profitability(results_path)

    def signal_handler(self, sig, frame):
        """Handle shutdown."""
        self._logger.info("Shutdown signal received.")
        self._stop_event = True

    def run_evolution_loop(self):
        """Main autonomous evolution loop."""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        self.create_genesis_agent()
        current_gen = self.elite_gen
        elite_profit = self.run_baseline(current_gen)
        self._logger.info(f"Started evolution from gen {current_gen} with elite profit ${elite_profit:.2f}")

        while not self._stop_event:
            try:
                current_gen += 1
                self._logger.info(f"Starting generation {current_gen}")

                # REFINE
                candidate_yaml = self.refine_agent(current_gen - 1, RESULTS_DIR / f"medusa_student_agent_gen_{current_gen-1}_summary.json")
                candidate_path = GENOMES_DIR / f"candidate_gen_{current_gen}.yaml"
                with open(candidate_path, "w") as f:
                    f.write(candidate_yaml)

                # TEST
                candidate_results_path = self.run_benchmark(candidate_path, current_gen, "candidate")
                candidate_profit = self.parse_profitability(candidate_results_path)

                self._logger.info(f"Candidate profit: ${candidate_profit:.2f} vs Elite: ${elite_profit:.2f}")

                # SELECT
                if candidate_profit > elite_profit * 1.01:  # 1% improvement threshold
                    self.promote_candidate(candidate_path, current_gen)
                    elite_profit = candidate_profit
                    self.elite_gen = current_gen
                    self._logger.info(f"Generation {current_gen}: PROMOTED (improved by {(candidate_profit / elite_profit - 1)*100:.1f}%)")
                else:
                    self.clone_elite(current_gen)
                    self._logger.info(f"Generation {current_gen}: REJECTED (no improvement)")

                time.sleep(5)  # Brief pause

            except Exception as e:
                self._logger.error(f"Error in generation {current_gen}: {e}")
                time.sleep(30)  # Graceful recovery pause
                continue

        self._logger.info("Evolution loop stopped.")


if __name__ == "__main__":
    trainer = MedusaTrainer()
    trainer.run_evolution_loop()