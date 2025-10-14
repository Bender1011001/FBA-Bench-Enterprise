#!/usr/bin/env python3
from __future__ import annotations

"""
Smoke test runner for ClearML integration.

- Starts a simulation using ScenarioEngine with a short scenario YAML
- ScenarioEngine internally initializes ClearMLTracker (no-op if SDK not installed)
- Per-tick metrics and a final summary are reported to ClearML when credentials are configured

Usage:
  python scripts/smoke_clearml_run.py --scenario configs/clearml_smoketest.yaml --project "FBA-Bench" --task-name "ClearML_SmokeTest"

Environment (recommended):
  CLEARML_API_SERVER=http://localhost:8008
  CLEARML_WEB_SERVER=http://localhost:8080
  CLEARML_FILES_SERVER=http://localhost:8081
  CLEARML_ACCESS_KEY=<your_key>
  CLEARML_SECRET_KEY=<your_secret>
"""

import argparse
import json
import os
import sys
from typing import Any, Dict

# Import ScenarioEngine; it wires ClearMLTracker inside
from scenarios.scenario_engine import ScenarioEngine


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="ClearML Smoke Test Runner")
    p.add_argument(
        "--scenario",
        type=str,
        default="configs/clearml_smoketest.yaml",
        help="Path to scenario YAML (default: configs/clearml_smoketest.yaml)",
    )
    p.add_argument(
        "--project",
        type=str,
        default="FBA-Bench",
        help='ClearML project name (ScenarioEngine uses this default: "FBA-Bench")',
    )
    p.add_argument(
        "--task-name",
        type=str,
        default=None,
        help="Optional task name override (defaults to scenario_name inside YAML).",
    )
    p.add_argument(
        "--print-env",
        action="store_true",
        help="Print relevant CLEARML_* env vars for debugging.",
    )
    p.add_argument(
        "--enqueue",
        action="store_true",
        help="If set, schedule this run on ClearML-Agent (requires CLEARML server/agent).",
    )
    p.add_argument(
        "--queue",
        type=str,
        default="default",
        help="ClearML queue name to enqueue to when --enqueue is set (default: default).",
    )
    return p.parse_args()


def print_clearml_env() -> None:
    keys = [
        "CLEARML_API_SERVER",
        "CLEARML_WEB_SERVER",
        "CLEARML_FILES_SERVER",
        "CLEARML_ACCESS_KEY",
        "CLEARML_SECRET_KEY",
        "CLEARML_CONFIG_FILE",
    ]
    data = {k: os.environ.get(k, "") for k in keys}
    # Do not leak secrets in logs; mask values
    for k in ["CLEARML_ACCESS_KEY", "CLEARML_SECRET_KEY"]:
        if data.get(k):
            data[k] = data[k][:4] + "***" + data[k][-4:]
    print("[ClearML Env]", json.dumps(data, indent=2))


def main() -> int:
    args = parse_args()

    if args.print_env:
        print_clearml_env()

    # If requested, hand off execution to ClearML-Agent by setting env flags
    if getattr(args, "enqueue", False):
        os.environ["CLEARML_EXECUTE_REMOTELY"] = "1"
        if getattr(args, "queue", None):
            os.environ["CLEARML_QUEUE"] = args.queue

    # ScenarioEngine already logs to ClearML in run_simulation()
    engine = ScenarioEngine()

    # Optionally allow overriding the scenario name via --task-name by patching YAML at runtime:
    # We avoid mutating files; instead we rely on ScenarioEngine which uses scenario_name from YAML.
    # The tracker initialization inside ScenarioEngine will use the YAML's scenario_name.
    try:
        # For the reference engine, agents are not actively stepped; we supply an empty registry.
        agent_models: Dict[str, Any] = {}

        print(f"[SmokeTest] Running scenario: {args.scenario}")
        results: Dict[str, Any] = engine.run_simulation(
            scenario_file=args.scenario, agent_models=agent_models
        )

        success = bool(results.get("success")) or (results.get("success_status") == "success")
        print("[SmokeTest] Final results:")
        print(json.dumps(results, indent=2, default=str))

        # Exit code: 0 if success, 1 otherwise
        return 0 if success else 1
    except FileNotFoundError as e:
        print(f"[SmokeTest] Scenario file not found: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"[SmokeTest] Error: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
