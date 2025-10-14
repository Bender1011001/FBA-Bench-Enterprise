"""
LLM Performance Test Script

This script provides a framework for conducting performance tests on Large Language Models (LLMs),
measuring metrics such as response time, token generation rate, and cost efficiency.
"""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List

# Configure basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class LLMClient:
    """
    A mock LLM client for performance testing.
    In a real scenario, this would interact with an actual LLM API.
    """

    def __init__(
        self,
        model_name: str,
        response_time_ms: int = 100,
        tokens_per_second: int = 50,
        cost_per_million_tokens: float = 2.0,
    ):
        self.model_name = model_name
        self._response_time_ms = response_time_ms
        self._tokens_per_second = tokens_per_second
        self._cost_per_million_tokens = cost_per_million_tokens

    async def generate_response(self, prompt: str, max_tokens: int = 50) -> Dict[str, Any]:
        """
        Simulates an LLM response with a configurable delay and token generation.
        """
        await asyncio.sleep(self._response_time_ms / 1000.0)  # Simulate network latency

        generated_tokens = min(len(prompt.split()) + 10, max_tokens)  # Simplified token generation

        # Simulate token generation time
        await asyncio.sleep(generated_tokens / self._tokens_per_second)

        response_text = (
            f"Simulated response for: '{prompt[:30]}...' with {generated_tokens} tokens."
        )

        return {
            "choices": [{"message": {"content": response_text}}],
            "usage": {
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": generated_tokens,
                "total_tokens": len(prompt.split()) + generated_tokens,
            },
            "model": self.model_name,
        }

    def calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculates the simulated cost of tokens."""
        total_tokens = prompt_tokens + completion_tokens
        return (total_tokens / 1_000_000) * self._cost_per_million_tokens


class LLMPerfTester:
    """
    Manages and executes performance tests for LLM clients.
    """

    def __init__(self, clients: Dict[str, LLMClient], output_dir: str = "perf_results"):
        self.clients = clients
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[Dict[str, Any]] = []

    async def _run_single_test(
        self, client_name: str, prompt: str, max_tokens: int
    ) -> Dict[str, Any]:
        """Runs a single test for an LLM client."""
        client = self.clients[client_name]
        start_time = time.perf_counter()

        try:
            response = await client.generate_response(prompt, max_tokens)
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000

            usage = response.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)

            cost = client.calculate_cost(prompt_tokens, completion_tokens)

            tokens_per_second = completion_tokens / (duration_ms / 1000.0) if duration_ms > 0 else 0

            return {
                "client": client_name,
                "model": client.model_name,
                "prompt": prompt,
                "max_tokens": max_tokens,
                "duration_ms": duration_ms,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "tokens_per_second": tokens_per_second,
                "cost": cost,
                "success": True,
                "error": None,
            }
        except Exception as e:
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000
            logger.error(f"Error during test for client {client_name}: {e}")
            return {
                "client": client_name,
                "model": client.model_name,
                "prompt": prompt,
                "max_tokens": max_tokens,
                "duration_ms": duration_ms,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "tokens_per_second": 0,
                "cost": 0,
                "success": False,
                "error": str(e),
            }

    async def run_tests(self, test_scenarios: List[Dict[str, Any]], num_iterations: int = 1):
        """
        Runs a series of performance tests across multiple LLM clients and scenarios.

        Args:
            test_scenarios: A list of dictionaries, each defining a test scenario
                            e.g., {"client": "mock_fast", "prompt": "Once upon a time", "max_tokens": 100}
            num_iterations: Number of times to run each scenario.
        """
        logger.info(
            f"Starting LLM performance tests for {num_iterations} iterations per scenario..."
        )
        all_tasks = []
        for i in range(num_iterations):
            for scenario in test_scenarios:
                client_name = scenario["client"]
                prompt = scenario["prompt"]
                max_tokens = scenario["max_tokens"]

                if client_name not in self.clients:
                    logger.warning(f"Client '{client_name}' not found. Skipping scenario.")
                    continue

                task = asyncio.create_task(self._run_single_test(client_name, prompt, max_tokens))
                all_tasks.append(task)

        self.results = await asyncio.gather(*all_tasks)
        logger.info("LLM performance tests completed.")
        self._save_results()
        self._analyze_results()

    def _save_results(self):
        """Saves the test results to a JSON file."""
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filepath = self.output_dir / f"llm_perf_test_results_{timestamp}.json"
        with open(filepath, "w") as f:
            json.dump(self.results, f, indent=4)
        logger.info(f"Test results saved to {filepath}")

    def _analyze_results(self):
        """Analyzes the collected results and prints a summary."""
        if not self.results:
            logger.warning("No results to analyze.")
            return

        logger.info("\n--- Performance Test Summary ---")

        client_results: Dict[str, List[Dict[str, Any]]] = {}
        for res in self.results:
            client_results.setdefault(res["client"], []).append(res)

        for client_name, results in client_results.items():
            successful_results = [r for r in results if r["success"]]
            if not successful_results:
                logger.warning(f"No successful tests for client: {client_name}")
                continue

            avg_duration = sum(r["duration_ms"] for r in successful_results) / len(
                successful_results
            )
            avg_tps = sum(r["tokens_per_second"] for r in successful_results) / len(
                successful_results
            )
            total_cost = sum(r["cost"] for r in successful_results)
            total_requests = len(results)
            successful_requests = len(successful_results)
            error_rate = (total_requests - successful_requests) / total_requests * 100

            logger.info(f"\nClient: {client_name} (Model: {self.clients[client_name].model_name})")
            logger.info(f"  Total Requests: {total_requests}")
            logger.info(f"  Successful Requests: {successful_requests}")
            logger.info(f"  Error Rate: {error_rate:.2f}%")
            logger.info(f"  Avg Response Time: {avg_duration:.2f} ms")
            logger.info(f"  Avg Tokens/Second: {avg_tps:.2f}")
            logger.info(f"  Total Cost: ${total_cost:.4f}")


# Example Usage
async def main():
    # Define LLM clients for testing
    llm_clients = {
        "mock_fast": LLMClient(
            "FastModel", response_time_ms=50, tokens_per_second=100, cost_per_million_tokens=1.5
        ),
        "mock_medium": LLMClient(
            "MediumModel", response_time_ms=150, tokens_per_second=50, cost_per_million_tokens=2.0
        ),
        "mock_slow": LLMClient(
            "SlowModel", response_time_ms=300, tokens_per_second=20, cost_per_million_tokens=3.0
        ),
    }

    # Define test scenarios
    scenarios = [
        {
            "client": "mock_fast",
            "prompt": "Generate a short story about a brave knight.",
            "max_tokens": 150,
        },
        {
            "client": "mock_medium",
            "prompt": "Write a Python function for quicksort.",
            "max_tokens": 200,
        },
        {
            "client": "mock_slow",
            "prompt": "Explain Quantum Entanglement in simple terms.",
            "max_tokens": 100,
        },
        {
            "client": "mock_fast",
            "prompt": "Summarize the history of AI in 50 words.",
            "max_tokens": 50,
        },
    ]

    # Initialize and run the tester
    tester = LLMPerfTester(llm_clients)
    await tester.run_tests(scenarios, num_iterations=5)


if __name__ == "__main__":
    asyncio.run(main())
