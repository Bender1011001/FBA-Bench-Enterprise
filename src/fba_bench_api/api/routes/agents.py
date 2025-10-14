
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

import yaml
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from benchmarking.config.pydantic_config import UnifiedAgentRunnerConfig
from fba_bench_api.api.dependencies import get_current_user
from fba_bench_api.core.database_async import get_async_db_session
from fba_bench_api.core.persistence_async import AsyncPersistenceManager
from fba_bench_api.models.agents import (
    AgentConfigurationResponse,
    AgentValidationRequest,
    AgentValidationResponse,
    FrameworksResponse,
)


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
