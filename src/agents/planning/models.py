from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List


class PlanPriority(Enum):
    """Priority levels for strategic and tactical plans."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PlanStatus(Enum):
    """Status of plans throughout their lifecycle."""

    DRAFT = "draft"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PlanType(Enum):
    """Types of strategic plans."""

    GROWTH = "growth"
    OPTIMIZATION = "optimization"
    DEFENSIVE = "defensive"
    EXPLORATORY = "exploratory"
    RECOVERY = "recovery"


@dataclass
class StrategicObjective:
    """A high-level strategic objective with measurable outcomes."""

    objective_id: str
    title: str
    description: str
    target_metrics: Dict[
        str, float
    ]  # e.g., {"profit_margin": 0.25, "market_share": 0.15}
    timeframe_days: int
    priority: PlanPriority
    status: PlanStatus
    created_at: datetime
    target_completion: datetime
    progress_indicators: Dict[str, float] = field(default_factory=dict)
    dependencies: List[str] = field(
        default_factory=list
    )  # Other objective IDs this depends on

    def calculate_progress(self, current_metrics: Dict[str, float]) -> float:
        """Calculate overall progress towards objective completion."""
        if not self.target_metrics:
            return 0.0

        progress_scores = []
        for metric, target_value in self.target_metrics.items():
            current_value = current_metrics.get(metric, 0.0)
            if target_value == 0:
                continue

            # Calculate progress as percentage toward target
            progress = min(1.0, current_value / target_value)
            progress_scores.append(progress)

        return sum(progress_scores) / len(progress_scores) if progress_scores else 0.0

    def is_overdue(self, current_time: datetime) -> bool:
        """Check if objective is overdue."""
        return current_time > self.target_completion and self.status not in [
            PlanStatus.COMPLETED,
            PlanStatus.CANCELLED,
        ]


@dataclass
class TacticalAction:
    """A specific action that serves strategic objectives."""

    action_id: str
    title: str
    description: str
    action_type: str  # e.g., "set_price", "place_order", "run_marketing_campaign"
    parameters: Dict[str, Any]
    strategic_objective_id: str
    priority: PlanPriority
    status: PlanStatus
    created_at: datetime
    scheduled_execution: datetime
    estimated_duration_hours: float
    expected_impact: Dict[str, float]  # Expected impact on metrics
    prerequisites: List[str] = field(
        default_factory=list
    )  # Other action IDs that must complete first

    def is_ready_for_execution(
        self, current_time: datetime, completed_actions: List[str]
    ) -> bool:
        """Check if action is ready for execution."""
        if self.status != PlanStatus.ACTIVE:
            return False

        # Check if scheduled time has arrived
        if current_time < self.scheduled_execution:
            return False

        # Check if all prerequisites are completed
        for prereq in self.prerequisites:
            if prereq not in completed_actions:
                return False

        return True
