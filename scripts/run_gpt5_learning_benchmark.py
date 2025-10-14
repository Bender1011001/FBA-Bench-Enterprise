#!/usr/bin/env python3
"""
GPT-5 Learning Benchmark Runner

- Runs sequential learning episodes on scenarios/tier_1_moderate.yaml
- Persists episodic outcomes via learning.EpisodicLearningManager
- Emits per-episode JSON artifacts, a metrics CSV, and a summary.json
- Single-process, deterministic by MASTER_SEED for causal learning

Usage:
  python scripts/run_gpt5_learning_benchmark.py --config config_storage/simulations/gpt5_learning_full.yaml --episodes 12 --seed 1337

Notes:
- ScenarioEngine in this repo provides a deterministic simulation suitable for benchmarking. It does not call into external LLMs by default.
- EpisodicLearningManager provides persistence for outcomes and strategy updates. This runner records outcomes per episode.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import datetime
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from learning.episodic_learning import EpisodicLearningManager
from scenarios.scenario_engine import ScenarioEngine

logger = logging.getLogger("gpt5_learning_runner")
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _load_yaml(path: Path) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _derive_episodes(config: Dict[str, Any], override_episodes: Optional[int]) -> List[int]:
    if override_episodes and override_episodes > 0:
        return list(range(1, override_episodes + 1))
    # Try parameter_sweep.episode list
    eps = (config.get("parameter_sweep") or {}).get("episode")
    if isinstance(eps, list) and all(isinstance(x, int) for x in eps):
        return list(eps)
    # Fallback to 12
    return list(range(1, 12 + 1))


def _derive_seed(config: Dict[str, Any], override_seed: Optional[int]) -> int:
    if override_seed is not None:
        return int(override_seed)
    seeds = (config.get("parameter_sweep") or {}).get("seed")
    if isinstance(seeds, list) and len(seeds) > 0 and isinstance(seeds[0], int):
        return int(seeds[0])
    return 0


def _derive_results_dir(
    base_dir_cfg: Optional[str], experiment_name: str, output_dir_override: Optional[str]
) -> Path:
    base = (
        Path(output_dir_override)
        if output_dir_override
        else Path(base_dir_cfg or "results/gpt5_learning_full")
    )
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    out = base / f"{experiment_name}_{timestamp}"
    _ensure_dir(out)
    return out


def _extract_profit(result: Dict[str, Any]) -> float:
    # Primary: metrics.total_profit
    try:
        metrics = result.get("metrics") or {}
        val = metrics.get("total_profit", None)
        if isinstance(val, (int, float)):
            return float(val)
    except Exception:
        pass
    # Fallback: final_state.profit or profit_target
    try:
        fs = result.get("final_state") or {}
        for key in ("profit", "profit_target"):
            v = fs.get(key)
            if isinstance(v, (int, float)):
                return float(v)
    except Exception:
        pass
    return 0.0


def _extract_kpis(result: Dict[str, Any]) -> Dict[str, Any]:
    fs = result.get("final_state") or {}
    metrics = result.get("metrics") or {}
    return {
        "profit": _extract_profit(result),
        "market_share": fs.get("market_share_europe") or fs.get("market_share") or 0.0,
        "inventory_turnover_rate": fs.get("inventory_turnover_rate", 0.0),
        "stock_out_rate": fs.get("stock_out_rate", 0.0),
        "customer_satisfaction": fs.get("customer_satisfaction", 0.0),
        "on_time_delivery_rate": fs.get("on_time_delivery_rate", 0.0),
        "success": bool(result.get("success", result.get("success_status") == "success")),
        "composite_score": metrics.get("composite_score", result.get("composite_score")),
        "bonus_score": metrics.get("bonus_score", result.get("bonus_score")),
        "simulation_duration": int(
            result.get("simulation_duration", fs.get("partnership_duration", 0))
        ),
    }


async def _persist_episode(
    learning_mgr: EpisodicLearningManager, agent_id: str, episode_idx: int, kpis: Dict[str, Any]
) -> None:
    # Minimal episode data for persistence; extend as needed
    episode_data = {
        "episode_index": episode_idx,
        "timestamp": datetime.datetime.now().isoformat(),
    }
    await learning_mgr.store_episode_experience(
        agent_id=agent_id, episode_data=episode_data, outcomes=kpis
    )
    await learning_mgr.track_learning_progress(agent_id=agent_id, metrics=kpis)


def run_episode(
    engine: ScenarioEngine, scenario_file: str, agents: Dict[str, Any]
) -> Dict[str, Any]:
    return engine.run_simulation(scenario_file, agents)


def _write_json(path: Path, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def _append_metrics_csv(csv_path: Path, episode_idx: int, kpis: Dict[str, Any]) -> None:
    header = [
        "episode",
        "profit",
        "market_share",
        "inventory_turnover_rate",
        "stock_out_rate",
        "customer_satisfaction",
        "on_time_delivery_rate",
        "success",
        "composite_score",
        "bonus_score",
        "simulation_duration",
    ]
    exists = csv_path.exists()
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(header)
        row = [
            episode_idx,
            kpis.get("profit", 0.0),
            kpis.get("market_share", 0.0),
            kpis.get("inventory_turnover_rate", 0.0),
            kpis.get("stock_out_rate", 0.0),
            kpis.get("customer_satisfaction", 0.0),
            kpis.get("on_time_delivery_rate", 0.0),
            1 if kpis.get("success") else 0,
            kpis.get("composite_score", ""),
            kpis.get("bonus_score", ""),
            kpis.get("simulation_duration", 0),
        ]
        w.writerow(row)


def _compute_learning_deltas(series: List[float]) -> Dict[str, Any]:
    if not series:
        return {"start": 0.0, "end": 0.0, "delta": 0.0, "pct_change": 0.0}
    start = float(series[0])
    end = float(series[-1])
    delta = end - start
    pct = (delta / start * 100.0) if abs(start) > 1e-9 else 0.0
    return {"start": start, "end": end, "delta": delta, "pct_change": pct}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run GPT-5 Learning Benchmark (episodic)")
    parser.add_argument(
        "--config",
        type=str,
        default="config_storage/simulations/gpt5_learning_full.yaml",
        help="Path to simulation config YAML",
    )
    parser.add_argument(
        "--episodes", type=int, default=None, help="Override total number of episodes to run"
    )
    parser.add_argument("--seed", type=int, default=None, help="Master seed for determinism")
    parser.add_argument(
        "--output-dir", type=str, default=None, help="Override results base directory"
    )
    parser.add_argument(
        "--agent-id",
        type=str,
        default="advanced_agent",
        help="Agent ID used for episodic persistence",
    )
    args = parser.parse_args()

    cfg_path = Path(args.config)
    if not cfg_path.exists():
        logger.error(f"Config not found: {cfg_path}")
        return 2

    cfg = _load_yaml(cfg_path)
    experiment_name = str(cfg.get("experiment_name", "gpt5_learning_full"))
    episodes = _derive_episodes(cfg, args.episodes)
    master_seed = _derive_seed(cfg, args.seed)
    base_params = cfg.get("base_parameters") or {}
    scenario_file = base_params.get("scenario_file")
    if not scenario_file:
        logger.error("Config missing base_parameters.scenario_file")
        return 2
    agents_cfg = base_params.get("agents") or {}
    # In this repo's ScenarioEngine, the agents dict is not consumed by the engine core,
    # but we pass it for completeness.
    agents = agents_cfg

    results_dir = _derive_results_dir(
        (cfg.get("output") or {}).get("base_dir"), experiment_name, args.output_dir
    )
    _ensure_dir(results_dir)
    logger.info(f"Results will be saved under: {results_dir}")

    # Save a copy of the used config
    try:
        with open(results_dir / "used_config.yaml", "w", encoding="utf-8") as f:
            yaml.safe_dump(cfg, f, sort_keys=False)
    except Exception as e:
        logger.warning(f"Failed to persist used config: {e}")

    # Initialize learning manager
    learning_storage = (
        (base_params.get("learning_system") or {}).get("episodic_learning") or {}
    ).get("storage_path", "learning_data/gpt5_learning/")
    learning_mgr = EpisodicLearningManager(storage_dir=learning_storage)

    # Metrics aggregation
    profits: List[float] = []
    summary_runs: List[Dict[str, Any]] = []

    # Single engine instance (sufficient for this deterministic engine)
    engine = ScenarioEngine()

    csv_path = results_dir / "metrics.csv"

    # Run episodes sequentially
    for ep in episodes:
        os.environ["MASTER_SEED"] = str(int(master_seed) + int(ep))
        logger.info(f"--- Episode {ep} (MASTER_SEED={os.environ['MASTER_SEED']}) ---")

        try:
            result = run_episode(engine, scenario_file, agents)
        except Exception as e:
            logger.exception(f"Episode {ep} failed: {e}")
            # Record failure artifact
            fail_path = results_dir / f"run_episode_{ep}.json"
            _write_json(fail_path, {"error": str(e), "episode": ep})
            continue

        # Persist episode artifact
        run_path = results_dir / f"run_episode_{ep}.json"
        _write_json(run_path, result)

        # Extract KPIs and track learning
        kpis = _extract_kpis(result)
        profits.append(kpis.get("profit", 0.0))
        _append_metrics_csv(csv_path, ep, kpis)

        # Persist learning episode (async API)
        try:
            asyncio.run(_persist_episode(learning_mgr, args.agent_id, ep, kpis))
        except Exception as e:
            logger.warning(f"Episodic persistence warning (episode {ep}): {e}")

        summary_runs.append({"episode": ep, "kpis": kpis, "artifact": str(run_path)})

    # Build summary
    summary = {
        "experiment_name": experiment_name,
        "episodes_run": len(summary_runs),
        "results_dir": str(results_dir),
        "profit_series": profits,
        "profit_deltas": _compute_learning_deltas(profits),
        "runs": summary_runs,
    }
    _write_json(results_dir / "summary.json", summary)
    logger.info(f"Summary saved to: {results_dir / 'summary.json'}")
    logger.info(f"Profit progression: {summary['profit_deltas']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
