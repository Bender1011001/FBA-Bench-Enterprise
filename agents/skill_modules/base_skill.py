from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class SkillOutcome:
    """
    Minimal SkillOutcome used by OutcomeAnalysisService.

    Fields align with the construction in
    fba_bench_core/services/outcome_analysis_service.py::analyze_tick_outcome().
    """
    action_id: str
    success: bool
    impact_metrics: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    resource_cost: Dict[str, Any] = field(default_factory=dict)
    lessons_learned: List[str] = field(default_factory=list)
    confidence_validation: float = 0.0