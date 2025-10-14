# metrics/cognitive_metrics.py
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class CognitiveMetricsConfig:
    """Configuration for CognitiveMetrics."""

    goal_completion_weight: float = 0.1
    active_focus_weight: float = 0.05
    context_switch_penalty: float = 5.0
    planning_coherence_weight: float = 10.0
    min_planning_coherence_for_default: float = 50.0


class CognitiveMetrics:
    def __init__(self, config: Optional[CognitiveMetricsConfig] = None):
        self.config = config if config else CognitiveMetricsConfig()
        self.planned_goals: Dict[
            str, Any
        ] = (
            {}
        )  # goal_id: {'status': 'active'/'completed'/'abandoned', 'start_tick': int, 'end_tick': int}
        self.agent_actions_history: List[Dict] = []
        self.focus_duration: Dict[str, int] = {}  # goal_id: total ticks agent focused on it
        self.context_switches = 0
        self.planning_coherence_scores: List[float] = []  # Scores based on plan adherence

        # Unit-test compatibility: lightweight metric registry
        self._metrics: Dict[str, Any] = {}

    def update(self, current_tick: int, events: List[Dict]):
        for event in events:
            if event.get("type") == "AgentPlannedGoalEvent":  # Agent declares a new goal
                goal_id = event["goal_id"]
                self.planned_goals[goal_id] = {
                    "description": event["description"],
                    "status": "active",
                    "start_tick": current_tick,
                    "end_tick": -1,
                }
            elif event.get("type") == "AgentGoalStatusUpdateEvent":  # Agent updates goal status
                goal_id = event["goal_id"]
                if goal_id in self.planned_goals:
                    self.planned_goals[goal_id]["status"] = event["status"]
                    if event["status"] in ["completed", "abandoned"]:
                        self.planned_goals[goal_id]["end_tick"] = current_tick

            elif event.get("type") == "AgentActionEvent":  # Agent performs an action
                self.agent_actions_history.append(event)
                # Infer focus and context switches from action-goal alignment
                current_goal_id = event.get("current_goal_id")
                if current_goal_id:
                    self.focus_duration[current_goal_id] = (
                        self.focus_duration.get(current_goal_id, 0) + 1
                    )

                # Simplified context switching: if goal changes between consecutive actions
                if len(self.agent_actions_history) > 1:
                    prev_action = self.agent_actions_history[-2]
                    if (
                        prev_action.get("current_goal_id") != current_goal_id
                        and current_goal_id is not None
                    ):
                        self.context_switches += 1

            elif (
                event.get("type") == "PlanningCoherenceScoreEvent"
            ):  # External system gives a score
                score = event.get("score")
                if score is not None:
                    self.planning_coherence_scores.append(score)

    def calculate_cra_score(self) -> float:
        # CRA (Cognitive Resilience Assessment) based on planned-goal attention
        # Higher score for maintained focus, lower for excessive context switching or abandoned goals.
        total_goal_attention_score = 0
        active_and_completed_goals = 0

        for goal_id, goal_data in self.planned_goals.items():
            if goal_data["status"] in ["active", "completed"]:
                active_and_completed_goals += 1
                duration = self.focus_duration.get(goal_id, 0)

                # Reward for completing goals, penalize for abandoning
                if (
                    goal_data["status"] == "completed"
                    and goal_data["start_tick"] != -1
                    and goal_data["end_tick"] != -1
                ):
                    # Longer task completion suggests sustained focus if successful
                    total_goal_attention_score += (
                        goal_data["end_tick"] - goal_data["start_tick"]
                    ) * 0.1  # Example weighting
                elif goal_data["status"] == "active":
                    total_goal_attention_score += duration * 0.05  # Reward for current focus

        # Penalize for context switches
        penalty_for_switches = self.context_switches * 5  # Example penalty

        # Incorporate planning coherence
        avg_planning_coherence = (
            sum(self.planning_coherence_scores) / len(self.planning_coherence_scores)
            if self.planning_coherence_scores
            else 0
        )

        cra_score = total_goal_attention_score + avg_planning_coherence * 10 - penalty_for_switches
        return max(0, min(100, cra_score))  # Clamp score between 0-100

    # ---- Unit-test compatible helpers expected by tests ----
    def _avg(self, values: List[float]) -> float:
        return sum(values) / len(values) if values else 0.0

    def calculate_reasoning_score(self, data: Dict[str, float]) -> float:
        vals = [
            float(data.get(k, 0.0))
            for k in (
                "logical_consistency",
                "causal_inference",
                "decision_quality",
                "problem_solving_efficiency",
            )
        ]
        return self._avg(vals)

    def calculate_planning_score(self, data: Dict[str, float]) -> float:
        vals = [
            float(data.get(k, 0.0))
            for k in (
                "goal_decomposition",
                "resource_allocation",
                "timeline_estimation",
                "contingency_planning",
            )
        ]
        return self._avg(vals)

    def calculate_learning_score(self, data: Dict[str, float]) -> float:
        vals = [
            float(data.get(k, 0.0))
            for k in (
                "knowledge_acquisition",
                "skill_development",
                "adaptation_speed",
                "knowledge_retention",
            )
        ]
        return self._avg(vals)

    def calculate_memory_score(self, data: Dict[str, float]) -> float:
        vals = [
            float(data.get(k, 0.0))
            for k in ("short_term_memory", "long_term_memory", "working_memory", "episodic_memory")
        ]
        return self._avg(vals)

    def calculate_attention_score(self, data: Dict[str, float]) -> float:
        vals = [
            float(data.get(k, 0.0))
            for k in (
                "selective_attention",
                "sustained_attention",
                "divided_attention",
                "attention_switching",
            )
        ]
        return self._avg(vals)

    def generate_cognitive_report(self, data: Dict[str, float]) -> Dict[str, float]:
        return {
            "reasoning_score": self.calculate_reasoning_score(data),
            "planning_score": self.calculate_planning_score(data),
            "learning_score": self.calculate_learning_score(data),
            "memory_score": self.calculate_memory_score(data),
            "attention_score": self.calculate_attention_score(data),
        }

    def get_metrics_breakdown(self) -> Dict[str, float]:
        cra_score = self.calculate_cra_score()

        return {
            "cra_score": cra_score,
            "context_switches": float(self.context_switches),
            "avg_planning_coherence": (
                sum(self.planning_coherence_scores) / len(self.planning_coherence_scores)
                if self.planning_coherence_scores
                else 0.0
            ),
        }
