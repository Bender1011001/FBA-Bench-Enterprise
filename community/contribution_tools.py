import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

# Production manager provides hardened validation, deterministic benchmarks, and packaging/CLI
from community.contribution_tools_production import ProductionContributionManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


@dataclass(frozen=True)
class QualityAssessment:
    """
    Summary of contribution quality used by tests and reports.
    Provides a normalized, single object importable from community.contribution_tools.
    """

    code_quality: float  # 0.0 - 1.0
    test_coverage: float  # 0.0 - 1.0
    documentation_score: float  # 0.0 - 1.0
    security_score: float  # 0.0 - 1.0
    performance_score: float  # 0.0 - 1.0
    passed: bool

    @staticmethod
    def from_results(results: Dict[str, Any]) -> "QualityAssessment":
        """
        Build QualityAssessment from heterogeneous validation/benchmark results.
        Missing fields default to 0.0. 'passed' is derived unless explicitly provided.
        """
        cq = float(results.get("code_quality", results.get("lint_score", 0.0)) or 0.0)
        tc = float(results.get("test_coverage", results.get("coverage", 0.0)) or 0.0)
        ds = float(results.get("documentation_score", results.get("docs_score", 0.0)) or 0.0)
        ss = float(
            results.get("security_score", 1.0 if results.get("security_issues", 0) == 0 else 0.0)
        )
        ps = float(results.get("performance_score", results.get("throughput_score", 0.0)) or 0.0)
        passed = bool(
            results.get(
                "passed", (cq >= 0.7 and tc >= 0.8 and ds >= 0.6 and ss >= 0.8 and ps >= 0.6)
            )
        )
        return QualityAssessment(
            code_quality=cq,
            test_coverage=tc,
            documentation_score=ds,
            security_score=ss,
            performance_score=ps,
            passed=passed,
        )


class ContributionManager:
    """
    Backwards-compatible facade that delegates to the production-grade manager.
    This removes mock/example logic from the runtime path while preserving imports.
    """

    def __init__(self, plugin_manager: Optional[Any] = None):
        self._pm = ProductionContributionManager(plugin_manager=plugin_manager)
        logging.info(
            "ContributionManager (facade) initialized; delegating to ProductionContributionManager."
        )

    async def validate_contribution(
        self, plugin_path: str, tests: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        return await self._pm.validate_contribution(plugin_path, tests)

    async def generate_plugin_docs(self, plugin_module: Any) -> Dict[str, str]:
        return await self._pm.generate_plugin_docs(plugin_module)

    async def benchmark_plugin_performance(
        self, plugin_path: str, scenarios: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        return await self._pm.benchmark_plugin_performance(plugin_path, scenarios)

    async def package_for_distribution(self, plugin_path: str, metadata: Dict[str, Any]) -> str:
        # Allow dist directory override via FBA_PLUGIN_DIST_DIR for CI/customization
        override_dir = os.getenv("FBA_PLUGIN_DIST_DIR")
        if override_dir:
            os.makedirs(override_dir, exist_ok=True)
        return await self._pm.package_for_distribution(plugin_path, metadata)

    async def create_contribution_report(
        self, validation_results: Dict[str, Any], benchmark_results: Dict[str, Any]
    ) -> str:
        return await self._pm.create_contribution_report(validation_results, benchmark_results)
