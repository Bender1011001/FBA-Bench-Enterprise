"""
Crisis handling logic for multi-domain controller.

Handles emergency protocols, action generation for different crisis types, and priority restoration.
"""

import asyncio
import logging
from datetime import datetime
from typing import List

from .models import BusinessPriority

from agents.skill_modules.base_skill import SkillAction


logger = logging.getLogger(__name__)


class CrisisManager:
    """
    Manager for crisis response and recovery in multi-domain control.

    Handles emergency action generation and priority restoration after crises.
    """

    def __init__(self, controller):
        """
        Initialize the CrisisManager.

        Args:
            controller: The parent MultiDomainController instance for shared state access.
        """
        self.controller = controller

    async def handle_crisis_mode(self, crisis_type: str, severity: str) -> List[SkillAction]:
        """Handle crisis situations with emergency protocols."""
        logger.warning(f"Crisis mode activated: {crisis_type} (severity: {severity})")

        # Temporarily override business priority
        original_priority = self.controller.current_priority
        self.controller.current_priority = BusinessPriority.SURVIVAL

        crisis_actions = []

        if crisis_type == "cash_flow":
            crisis_actions.extend(await self._generate_cash_flow_crisis_actions(severity))
        elif crisis_type == "reputation":
            crisis_actions.extend(await self._generate_reputation_crisis_actions(severity))
        elif crisis_type == "operational":
            crisis_actions.extend(await self._generate_operational_crisis_actions(severity))

        # Log crisis response
        await self.controller.coordination._log_strategic_decision(f"crisis_response_{crisis_type}", [], crisis_actions)

        # Schedule priority restoration
        asyncio.create_task(self._restore_priority_after_crisis(original_priority))

        return crisis_actions

    async def _generate_cash_flow_crisis_actions(self, severity: str) -> List[SkillAction]:
        """Generate emergency cash flow preservation actions."""
        actions = []

        # Immediate cost reduction
        cost_reduction_action = SkillAction(
            action_type="emergency_cost_reduction",
            parameters={
                "reduction_percentage": 0.3 if severity == "critical" else 0.2,
                "protected_categories": ["customer_service"],
                "timeframe": "immediate",
            },
            confidence=0.9,
            reasoning=f"Emergency cost reduction due to {severity} cash flow crisis",
            priority=0.95,
            resource_requirements={},
            expected_outcome={"cash_preservation": 0.8},
            skill_source="crisis_controller",
        )
        actions.append(cost_reduction_action)

        # Freeze non-essential spending
        spending_freeze_action = SkillAction(
            action_type="freeze_discretionary_spending",
            parameters={
                "freeze_categories": ["marketing", "growth_investments"],
                "exceptions": ["customer_critical", "safety_critical"],
            },
            confidence=0.95,
            reasoning="Freeze non-essential spending to preserve cash",
            priority=0.9,
            resource_requirements={},
            expected_outcome={"cash_conservation": 0.6},
            skill_source="crisis_controller",
        )
        actions.append(spending_freeze_action)

        return actions

    async def _generate_reputation_crisis_actions(self, severity: str) -> List[SkillAction]:
        """Generate reputation management crisis actions."""
        actions = []

        # Immediate customer communication
        communication_action = SkillAction(
            action_type="crisis_communication",
            parameters={
                "message_type": "proactive_apology",
                "channels": ["email", "social_media", "website"],
                "urgency": severity,
            },
            confidence=0.8,
            reasoning=f"Proactive communication for {severity} reputation crisis",
            priority=0.9,
            resource_requirements={"budget": 5000},
            expected_outcome={"reputation_recovery": 0.4},
            skill_source="crisis_controller",
        )
        actions.append(communication_action)

        return actions

    async def _generate_operational_crisis_actions(self, severity: str) -> List[SkillAction]:
        """Generate operational crisis response actions."""
        actions = []

        # Emergency operational review
        operational_action = SkillAction(
            action_type="emergency_operational_review",
            parameters={
                "review_scope": "all_operations",
                "focus_areas": ["inventory", "fulfillment", "customer_service"],
                "timeline": "24_hours",
            },
            confidence=0.85,
            reasoning=f"Emergency operational review for {severity} crisis",
            priority=0.85,
            resource_requirements={"urgency": "high"},
            expected_outcome={"operational_stability": 0.7},
            skill_source="crisis_controller",
        )
        actions.append(operational_action)

        return actions

    async def _restore_priority_after_crisis(self, original_priority: BusinessPriority):
        """Restore original business priority after crisis period."""
        await asyncio.sleep(self.controller.crisis_cooldown_seconds)

        logger.info(
            f"Restoring business priority from {self.controller.current_priority.value} to {original_priority.value}"
        )
        self.controller.current_priority = original_priority
        self.controller.resources._update_priority_multipliers()
        await self.controller.resources._reallocate_resources_for_priority()