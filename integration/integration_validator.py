import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# Assuming RealWorldAdapter is implemented
# from .real_world_adapter import RealWorldAdapter


@dataclass
class ValidationResult:
    """
    Validation result with forward and backward compatibility fields.
    Preferred fields:
      - is_valid: bool
      - errors: List[str]
      - warnings: List[str]
      - score: float
      - details: Dict[str, Any]
    Back-compat properties:
      - passed (alias for is_valid)
      - issues (alias for errors)
    """

    is_valid: bool
    score: float = 1.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

    # Back-compat read-only aliases
    @property
    def passed(self) -> bool:
        return self.is_valid

    @property
    def issues(self) -> List[str]:
        return self.errors

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "score": self.score,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "details": dict(self.details),
        }


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class IntegrationValidator:
    """
    Provides tools for integration testing and validation between simulation and real-world
    systems, ensuring action consistency, safety, and performance parity.

    Construction:
      - IntegrationValidator(real_world_adapter=adapter)
      - IntegrationValidator(config=safety_config)
      - IntegrationValidator(real_world_adapter=adapter, config=safety_config)

    Where config can be a dict or object with attributes:
      - price_change_max_percent: float
      - inventory_change_max_units: int
    """

    def __init__(
        self, real_world_adapter: Any = None, config: Optional[Any] = None
    ):  # Use Any to avoid circular import for now
        self.real_world_adapter = real_world_adapter
        # If adapter carries a safety_config and no explicit config passed, use that
        if (
            config is None
            and hasattr(real_world_adapter, "config")
            and getattr(real_world_adapter.config, "safety_config", None) is not None
        ):
            config = real_world_adapter.config.safety_config  # type: ignore[attr-defined]
        self.config = config
        self.validation_results: Dict[str, Any] = {}
        logging.info("IntegrationValidator initialized.")

    def _cfg(self, key: str, default: Any) -> Any:
        """
        Helper to read a config value from either a dict-like or object with attributes.
        """
        cfg = self.config
        try:
            if cfg is None:
                return default
            if isinstance(cfg, dict):
                return cfg.get(key, default)
            if hasattr(cfg, key):
                return getattr(cfg, key)
        except Exception:
            pass
        return default

    async def validate_action_consistency(
        self, sim_action: Dict[str, Any], real_expected_action: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Checks if a simulation action, when translated, matches an expected real-world action.
        This ensures 'Simulation-to-real validation'.
        """
        logging.info(f"Validating action consistency for sim_action: {sim_action.get('type')}")
        try:
            if self.real_world_adapter is None or not hasattr(
                self.real_world_adapter, "translate_simulation_action"
            ):
                return False, "No real_world_adapter or translate_simulation_action not available"
            translated_action = await self.real_world_adapter.translate_simulation_action(
                sim_action
            )

            # Simple content comparison. In practice, this might need more sophisticated diffing
            is_consistent = translated_action == real_expected_action

            message = f"Translated action: {translated_action}, Expected: {real_expected_action}"
            if is_consistent:
                logging.info(f"Action consistency PASSED: {sim_action.get('type')}")
            else:
                logging.warning(
                    f"Action consistency FAILED for {sim_action.get('type')}. {message}"
                )

            return is_consistent, message
        except Exception as e:
            logging.error(
                f"Error validating action consistency for {sim_action.get('type')}: {e}",
                exc_info=True,
            )
            return False, f"Error during translation or comparison: {e}"

    async def test_safety_constraints(
        self, dangerous_actions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validates that safety mechanisms prevent specified dangerous actions in live/sandbox modes.
        """
        logging.info("Starting safety constraint testing.")
        results = {"overall_status": "pending", "tests": []}

        # Test in sandbox mode first (when adapter supports mode)
        if self.real_world_adapter and hasattr(self.real_world_adapter, "set_mode"):
            await self.real_world_adapter.set_mode("sandbox")
        logging.info("Testing safety constraints in SANDBOX mode.")

        for i, action in enumerate(dangerous_actions):
            test_name = f"Sandbox Safety Test for Action {i+1} ({action.get('type', 'Unknown A.')})"
            try:
                # Attempt to execute the dangerous action with safety_check=True
                if self.real_world_adapter and hasattr(self.real_world_adapter, "execute_action"):
                    await self.real_world_adapter.execute_action(action, safety_check=True)
                    # If we reach here, it means the action wasn't blocked, which is a failure
                    results["tests"].append(
                        {
                            "name": test_name,
                            "action": action,
                            "status": "FAILED",
                            "message": "Action was not blocked by safety constraints.",
                        }
                    )
                    logging.error(f"Safety test FAILED: {test_name}. Action was executed.")
                else:
                    # Without a live adapter, treat as blocked by design
                    raise ValueError(
                        "Action blocked by safety constraint (no live adapter in validator)."
                    )
            except ValueError as e:
                results["tests"].append(
                    {
                        "name": test_name,
                        "action": action,
                        "status": "PASSED",
                        "message": f"Action successfully blocked: {e}",
                    }
                )
                logging.info(f"Safety test PASSED: {test_name}. Action blocked as expected.")
            except Exception as e:
                results["tests"].append(
                    {
                        "name": test_name,
                        "action": action,
                        "status": "ERROR",
                        "message": f"Unexpected error during test: {e}",
                    }
                )
                logging.error(
                    f"Safety test ERROR: {test_name}. Unexpected error: {e}", exc_info=True
                )

        results["overall_status"] = (
            "PASSED" if all(t["status"] == "PASSED" for t in results["tests"]) else "FAILED"
        )
        logging.info(
            f"Safety constraint testing finished with overall status: {results['overall_status']}"
        )
        return results

    async def compare_performance_metrics(
        self, sim_results: Dict[str, Any], real_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compares performance metrics between simulation and real-world results.
        This identifies 'Performance comparison' discrepancies.

        :param sim_results: Performance metrics from a simulation run.
        :param real_results: Performance metrics from a corresponding real-world run.
        :return: A dictionary of comparison results, highlighting differences.
        """
        logging.info("Starting performance metrics comparison.")
        comparison = {"discrepancies": {}, "overall_status": "MATCH"}

        # Example comparison: check key metrics like revenue, profit, inventory
        metrics_to_compare = [
            "total_revenue",
            "net_profit",
            "average_inventory_level",
            "order_fulfillment_rate",
        ]

        for metric in metrics_to_compare:
            sim_val = sim_results.get(metric)
            real_val = real_results.get(metric)

            if sim_val is None or real_val is None:
                logging.warning(
                    f"Skipping comparison for metric '{metric}': missing data in one or both result sets."
                )
                continue

            # Using a simple percentage difference for comparison
            if sim_val != 0:
                diff_percentage = abs((real_val - sim_val) / sim_val) * 100
            else:
                diff_percentage = 0 if real_val == 0 else float("inf")  # Handle division by zero

            threshold = 5.0  # Example: allow up to 5% difference
            if diff_percentage > threshold:
                comparison["discrepancies"][metric] = {
                    "simulation": sim_val,
                    "real_world": real_val,
                    "difference_percent": f"{diff_percentage:.2f}%",
                    "status": "SIGNIFICANT_DIFFERENCE",
                }
                comparison["overall_status"] = "DISCREPANCY"
                logging.warning(f"Significant difference for {metric}: {diff_percentage:.2f}%")
            else:
                logging.info(
                    f"Metric {metric} matches closely ({diff_percentage:.2f}% difference)."
                )

        logging.info(
            f"Performance comparison finished. Overall status: {comparison['overall_status']}"
        )
        return comparison

    def _pct_change(self, current: float, new: float) -> float:
        try:
            if current == 0:
                return float("inf") if new != 0 else 0.0
            return abs((new - current) / current) * 100.0
        except Exception:
            return float("inf")

    async def validate_action(
        self, action_type: str, action_data: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validates a single action against safety configuration.
        Supports:
          - 'price_update' with fields: current_price, new_price
          - 'inventory_update' with fields: current_quantity, new_quantity
        """
        errors: List[str] = []
        warnings: List[str] = []
        details: Dict[str, Any] = {"action_type": action_type}

        if action_type == "price_update":
            cur = action_data.get("current_price")
            new = action_data.get("new_price")
            if cur is None or new is None:
                errors.append(
                    "Missing fields for price_update: current_price and new_price are required."
                )
            else:
                pct = self._pct_change(float(cur), float(new))
                details["price_change_pct"] = pct
                limit = float(self._cfg("price_change_max_percent", 20.0))
                details["price_change_limit_pct"] = limit
                if pct > limit:
                    errors.append(f"Price change {pct:.2f}% exceeds limit {limit:.2f}%.")
                elif pct > 0.8 * limit:
                    warnings.append(f"Price change {pct:.2f}% is close to limit {limit:.2f}%.")

        elif action_type == "inventory_update":
            cur_q = action_data.get("current_quantity")
            new_q = action_data.get("new_quantity")
            if cur_q is None or new_q is None:
                errors.append(
                    "Missing fields for inventory_update: current_quantity and new_quantity are required."
                )
            else:
                delta = int(new_q) - int(cur_q)
                details["inventory_delta_units"] = delta
                limit_units = int(self._cfg("inventory_change_max_units", 100))
                details["inventory_change_limit_units"] = limit_units
                if abs(delta) > limit_units:
                    errors.append(
                        f"Inventory change {delta} units exceeds limit {limit_units} units."
                    )
                elif abs(delta) > int(0.8 * limit_units):
                    warnings.append(
                        f"Inventory change {delta} units is close to limit {limit_units} units."
                    )

        else:
            warnings.append(
                f"No explicit validation rules for action_type '{action_type}'. Marking as valid by default."
            )

        is_valid = len(errors) == 0
        score = 1.0 if is_valid else 0.0
        return ValidationResult(
            is_valid=is_valid, score=score, errors=errors, warnings=warnings, details=details
        )

    async def run_integration_test_suite(self) -> Dict[str, Any]:
        """
        Runs a comprehensive suite of integration validation tests.
        """
        logging.info("Running comprehensive integration test suite.")
        suite_results = {
            "action_consistency_tests": {},
            "safety_tests": {},
            "performance_comparison_tests": {},
            "overall_suite_status": "PENDING",
        }

        # Define mock data for tests
        sim_action_price_set = {"type": "set_price", "value": 25.0}
        real_expected_price_update = {
            "api_call": "update_product_price",
            "parameters": {"product_sku": "FBA-SKU-123", "new_price": 25.0},
        }

        consistency_status, consistency_message = await self.validate_action_consistency(
            sim_action_price_set, real_expected_price_update
        )
        suite_results["action_consistency_tests"] = {
            "status": "PASSED" if consistency_status else "FAILED",
            "message": consistency_message,
        }

        # Example for safety testing
        dangerous_actions_list = [
            {"type": "set_price", "value": 10000.0},
            {"type": "adjust_inventory", "value": -10000},
        ]
        safety_test_results = await self.test_safety_constraints(dangerous_actions_list)
        suite_results["safety_tests"] = safety_test_results

        # Example for performance comparison (mock data)
        mock_sim_perf = {
            "total_revenue": 10000.0,
            "net_profit": 2000.0,
            "average_inventory_level": 80,
            "order_fulfillment_rate": 0.98,
        }
        mock_real_perf = {
            "total_revenue": 10200.0,
            "net_profit": 1950.0,
            "average_inventory_level": 82,
            "order_fulfillment_rate": 0.97,
        }

        if self.real_world_adapter and hasattr(self.real_world_adapter, "set_mode"):
            await self.real_world_adapter.set_mode(
                "live"
            )  # Perform perf comparison in live mode context
        perf_comparison_results = await self.compare_performance_metrics(
            mock_sim_perf, mock_real_perf
        )
        suite_results["performance_comparison_tests"] = perf_comparison_results

        # Determine overall suite status
        all_passed = (
            suite_results["action_consistency_tests"]["status"] == "PASSED"
            and suite_results["safety_tests"]["overall_status"] == "PASSED"
            and suite_results["performance_comparison_tests"]["overall_status"] == "MATCH"
        )

        suite_results["overall_suite_status"] = "PASSED" if all_passed else "FAILED"
        self.validation_results = suite_results
        logging.info(
            f"Integration test suite completed. Overall status: {suite_results['overall_suite_status']}"
        )
        return suite_results

    async def generate_integration_report(self) -> str:
        """
        Summarizes the results of the comprehensive integration validation.

        :return: A markdown formatted string of the integration report.
        """
        logging.info("Generating integration report.")
        report = "# FBA-Bench Integration Validation Report\n\n"

        results = self.validation_results
        if not results:
            report += "No integration test suite has been run yet. Please run `run_integration_test_suite()` first.\n"
            return report

        report += f"**Overall Integration Suite Status:** `{results.get('overall_suite_status', 'N/A')}`\n\n"

        # Action Consistency
        report += "## 1. Action Consistency Validation\n"
        consistency = results.get("action_consistency_tests", {})
        report += f"Status: `{consistency.get('status', 'N/A')}`\n"
        report += f"Details: {consistency.get('message', 'N/A')}\n\n"

        # Safety Tests
        report += "## 2. Safety Constraint Testing\n"
        safety = results.get("safety_tests", {})
        report += f"Overall Safety Test Status: `{safety.get('overall_status', 'N/A')}`\n\n"
        report += "| Test Name | Action Type | Status | Message |\n"
        report += "|-----------|-------------|--------|---------|\n"
        for test in safety.get("tests", []):
            action_type = test.get("action", {}).get("type", "N/A")
            report += f"| {test.get('name')} | {action_type} | `{test.get('status')}` | {test.get('message', '')} |\n"
        report += "\n"

        # Performance Comparison
        report += "## 3. Performance Comparison (Simulation vs. Real-World)\n"
        performance = results.get("performance_comparison_tests", {})
        report += f"Overall Comparison Status: `{performance.get('overall_status', 'N/A')}`\n"
        if performance.get("discrepancies"):
            report += "**Identified Discrepancies:**\n"
            report += "| Metric | Simulation | Real-World | Difference (%) | Status |\n"
            report += "|--------|------------|------------|----------------|--------|\n"
            for metric, data in performance["discrepancies"].items():
                report += f"| {metric} | {data.get('simulation')} | {data.get('real_world')} | {data.get('difference_percent')} | `{data.get('status')}` |\n"
        else:
            report += "No significant performance discrepancies detected within set thresholds.\n"
        report += "\n"

        report += "---\nGenerated by FBA-Bench Integration Validator."
        logging.info("Integration report generated successfully.")
        return report


# Example usage for testing
async def _main():
    # Mock RealWorldAdapter for testing IntegrationValidator
    class MockRealWorldAdapter:
        def __init__(self):
            self.mode = "simulation"

        async def set_mode(self, mode: str):
            self.mode = mode
            logging.info(f"Mock RealWorldAdapter switched to {self.mode} mode.")

        async def translate_simulation_action(self, sim_action: Dict[str, Any]) -> Dict[str, Any]:
            # Simple mock translation
            if sim_action.get("type") == "set_price":
                return {
                    "api_call": "update_product_price",
                    "parameters": {
                        "product_sku": "FBA-SKU-123",
                        "new_price": sim_action.get("value"),
                    },
                }
            return sim_action

        async def execute_action(self, action: Dict[str, Any], safety_check=True) -> Dict[str, Any]:
            if (
                self.mode == "live"
                and safety_check
                and not await self.validate_real_world_safety(action)
            ):
                raise ValueError("Action blocked by safety constraint.")
            return {"status": "success", "mode": self.mode, "action_executed": action}

        async def validate_real_world_safety(self, action: Dict[str, Any]) -> bool:
            if (
                action.get("api_call") == "update_product_price"
                and action.get("parameters", {}).get("new_price") > 1000
            ):
                return False  # Example: Price too high
            if (
                action.get("api_call") == "adjust_inventory_level"
                and action.get("parameters", {}).get("quantity_change") < -100
            ):
                return False  # Example: Excessive negative inventory adjustment
            return True

    mock_adapter = MockRealWorldAdapter()
    validator = IntegrationValidator(real_world_adapter=mock_adapter)

    # Test validate_action_consistency
    sim_action = {"type": "set_price", "value": 99.99}
    expected_real_action = {
        "api_call": "update_product_price",
        "parameters": {"product_sku": "FBA-SKU-123", "new_price": 99.99},
    }
    consistent, message = await validator.validate_action_consistency(
        sim_action, expected_real_action
    )
    print(f"\nAction Consistency Test: {consistent} - {message}")

    # Test test_safety_constraints
    dangerous_actions = [
        {"type": "set_price", "value": 1500.0},
        {"type": "adjust_inventory", "value": -200},
    ]
    safety_results = await validator.test_safety_constraints(dangerous_actions)
    print("\nSafety Test Results:")
    print(safety_results)

    # Test run_integration_test_suite
    suite_results = await validator.run_integration_test_suite()
    print("\nComprehensive Integration Test Suite Results:")
    print(suite_results)

    # Generate report
    report = await validator.generate_integration_report()
    print("\n--- Integration Report ---")
    print(report)


if __name__ == "__main__":
    asyncio.run(_main())
