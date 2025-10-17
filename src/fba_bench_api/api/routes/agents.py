from __future__ import annotations

import logging
from typing import Dict

from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/agents", tags=["Agents"])


def get_framework_examples() -> Dict[str, Dict[str, str]]:
    return {
        "diy": {
            "basic_agent": "Basic DIY agent with simple decision making",
            "advanced_agent": "Advanced DIY agent with complex strategies",
            "hybrid_agent": "Hybrid agent combining multiple approaches",
        },
        "crewai": {
            "standard_agent": "Standard CrewAI agent with task delegation",
            "advanced_agent": "Advanced CrewAI agent with role-based agents",
            "hybrid_agent": "Hybrid CrewAI agent integrating tools",
        },
    }
