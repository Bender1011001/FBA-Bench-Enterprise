from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from fba_bench_api.core.database_async import get_async_db_session
from fba_bench_api.core.persistence_async import AsyncPersistenceManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/demo", tags=["Demo"])

# Demo configuration data
DEMO_EXPERIMENTS = [
    {
        "name": "🎮 Quest: Supply Chain Mastery - Level 3",
        "description": "Advanced supply chain optimization using GPT-4 with real-world constraints",
        "agent_id": "gpt-4-turbo-agent",
        "scenario_id": "supply_chain_expert",
        "status": "completed",
        "params": {
            "difficulty": "expert",
            "market_volatility": 0.8,
            "supply_constraints": True,
            "customer_segments": 5,
        },
    },
    {
        "name": "🎮 Quest: Market Expansion - Level 2",
        "description": "International market penetration strategy with Claude-3.5",
        "agent_id": "claude-3.5-sonnet-agent",
        "scenario_id": "market_expansion_intermediate",
        "status": "completed",
        "params": {
            "target_markets": ["EU", "APAC"],
            "budget_limit": 500000,
            "risk_tolerance": "medium",
        },
    },
    {
        "name": "🎮 Quest: International Trade - Level 2",
        "description": "Global trade optimization with Llama-3.1 focusing on efficiency",
        "agent_id": "llama-3.1-405b-agent",
        "scenario_id": "international_trade_intermediate",
        "status": "completed",
        "params": {
            "trade_routes": 8,
            "currency_hedging": True,
            "compliance_strict": True,
        },
    },
    {
        "name": "Customer Satisfaction Challenge",
        "description": "Baseline bot performance on customer service optimization",
        "agent_id": "baseline-bot-v1",
        "scenario_id": "customer_service_baseline",
        "status": "completed",
        "params": {
            "service_channels": 3,
            "response_time_target": 300,
            "satisfaction_threshold": 0.85,
        },
    },
    {
        "name": "Real-Time Inventory Management",
        "description": "Live inventory optimization with dynamic demand patterns",
        "agent_id": "gpt-3.5-turbo-agent",
        "scenario_id": "inventory_realtime",
        "status": "running",
        "params": {
            "warehouse_count": 12,
            "sku_variety": 5000,
            "demand_volatility": 0.6,
        },
    },
    {
        "name": "Risk Management Simulation",
        "description": "Financial risk assessment and mitigation strategies",
        "agent_id": "claude-3-opus-agent",
        "scenario_id": "risk_management_advanced",
        "status": "failed",
        "params": {
            "risk_categories": ["market", "credit", "operational"],
            "stress_test_scenarios": 15,
            "regulatory_compliance": True,
        },
    },
]


class DemoPopulateResponse(BaseModel):
    """Response model for demo population operation."""

    success: bool
    message: str
    experiments_created: int
    experiment_ids: List[str]


def get_pm(db: AsyncSession = Depends(get_async_db_session)) -> AsyncPersistenceManager:
    """Dependency injection for persistence manager."""
    return AsyncPersistenceManager(db)


def _generate_realistic_timestamps() -> tuple[datetime, datetime]:
    """Generate realistic created/updated timestamps for demo experiments."""
    import random
    from datetime import timedelta

    now = datetime.now(timezone.utc)

    # Create experiments over the past 30 days
    days_ago = random.randint(1, 30)
    created_at = now - timedelta(days=days_ago)

    # Updated timestamp is between created and now
    update_delay_hours = random.randint(1, days_ago * 24)
    updated_at = created_at + timedelta(hours=update_delay_hours)

    return created_at, updated_at


async def _clear_existing_demo_data(pm: AsyncPersistenceManager) -> int:
    """
    Clear existing demo experiments to avoid duplicates.

    Args:
        pm: Persistence manager

    Returns:
        Number of experiments cleared
    """
    try:
        existing_experiments = await pm.experiments().list()

        # Identify demo experiments by name patterns
        demo_experiment_ids = []
        for exp in existing_experiments:
            name = exp.get("name", "")
            if any(
                pattern in name
                for pattern in ["🎮 Quest:", "Demo", "Challenge", "Simulation"]
            ):
                demo_experiment_ids.append(exp["id"])

        # Delete demo experiments
        deleted_count = 0
        for exp_id in demo_experiment_ids:
            success = await pm.experiments().delete(exp_id)
            if success:
                deleted_count += 1

        logger.info("Cleared %d existing demo experiments", deleted_count)
        return deleted_count

    except Exception as e:
        logger.warning("Failed to clear existing demo data: %s", e)
        return 0


async def _create_demo_experiments(
    pm: AsyncPersistenceManager,
) -> tuple[int, List[str]]:
    """
    Create demo experiments with realistic data.

    Args:
        pm: Persistence manager

    Returns:
        Tuple of (created_count, experiment_ids)
    """
    created_experiments = []
    created_ids = []

    for demo_config in DEMO_EXPERIMENTS:
        try:
            # Generate unique ID and timestamps
            experiment_id = str(uuid.uuid4())
            created_at, updated_at = _generate_realistic_timestamps()

            # Create experiment record with explicit status
            experiment_data = {
                "id": experiment_id,
                "name": demo_config["name"],
                "description": demo_config["description"],
                "agent_id": demo_config["agent_id"],
                "scenario_id": demo_config["scenario_id"],
                "params": demo_config["params"],
                "status": "draft",  # Create as draft first
                "created_at": created_at,
                "updated_at": updated_at,
            }

            # Persist to database
            created_experiment = await pm.experiments().create(experiment_data)

            # Update status to the intended value (bypassing validation)
            if demo_config["status"] != "draft":
                await pm.experiments().update(
                    experiment_id,
                    {"status": demo_config["status"], "updated_at": updated_at},
                )
            created_experiments.append(created_experiment)
            created_ids.append(experiment_id)

            logger.debug("Created demo experiment: %s", demo_config["name"])

        except Exception as e:
            logger.error(
                "Failed to create demo experiment '%s': %s", demo_config["name"], e
            )
            continue

    logger.info("Created %d demo experiments", len(created_experiments))
    return len(created_experiments), created_ids


@router.post(
    "",
    response_model=DemoPopulateResponse,
    description="Populate demo data (development only)",
)
async def populate_demo_data(
    clear_existing: bool = True, pm: AsyncPersistenceManager = Depends(get_pm)
) -> DemoPopulateResponse:
    """
    Populate the system with demonstration experiments and data.

    This endpoint is intended for development and testing purposes to quickly
    set up realistic sample data for frontend development and demos.

    Args:
        clear_existing: Whether to clear existing demo experiments first
        pm: Injected persistence manager

    Returns:
        Summary of the population operation
    """
    logger.info("Starting demo data population (clear_existing=%s)", clear_existing)

    try:
        # Clear existing demo data if requested
        cleared_count = 0
        if clear_existing:
            cleared_count = await _clear_existing_demo_data(pm)

        # Create new demo experiments
        created_count, experiment_ids = await _create_demo_experiments(pm)

        if created_count > 0:
            message = f"Successfully created {created_count} demo experiments"
            if cleared_count > 0:
                message += f" (cleared {cleared_count} existing)"
        else:
            message = "No demo experiments were created"

        logger.info("Demo data population completed: %s", message)

        return DemoPopulateResponse(
            success=created_count > 0,
            message=message,
            experiments_created=created_count,
            experiment_ids=experiment_ids,
        )

    except Exception as e:
        error_message = f"Failed to populate demo data: {str(e)}"
        logger.error(error_message)

        return DemoPopulateResponse(
            success=False,
            message=error_message,
            experiments_created=0,
            experiment_ids=[],
        )


@router.post(
    "/populate",
    response_model=DemoPopulateResponse,
    description="Alias for demo data population",
)
async def populate_demo_data_alias(
    pm: AsyncPersistenceManager = Depends(get_pm),
) -> DemoPopulateResponse:
    """
    Alias endpoint for demo data population matching frontend expectations.

    This endpoint provides the same functionality as POST /api/v1/demo but matches
    the exact path that the frontend is calling: POST /api/v1/demo/populate
    """
    return await populate_demo_data(clear_existing=True, pm=pm)


@router.delete("", description="Clear all demo data")
async def clear_demo_data(pm: AsyncPersistenceManager = Depends(get_pm)) -> dict:
    """
    Clear all demonstration data from the system.

    This endpoint removes all demo experiments and associated data,
    useful for cleaning up after testing or demos.

    Returns:
        Summary of the cleanup operation
    """
    logger.info("Starting demo data cleanup")

    try:
        cleared_count = await _clear_existing_demo_data(pm)

        message = f"Successfully cleared {cleared_count} demo experiments"
        logger.info("Demo data cleanup completed: %s", message)

        return {
            "success": True,
            "message": message,
            "experiments_cleared": cleared_count,
        }

    except Exception as e:
        error_message = f"Failed to clear demo data: {str(e)}"
        logger.error(error_message)

        return {"success": False, "message": error_message, "experiments_cleared": 0}


@router.get("/info", description="Get information about available demo data")
async def get_demo_info() -> dict:
    """
    Get information about the available demo data configurations.

    Returns metadata about what demo experiments can be created,
    useful for understanding what the populate endpoint will generate.
    """
    return {
        "available_experiments": len(DEMO_EXPERIMENTS),
        "experiment_types": [exp["name"] for exp in DEMO_EXPERIMENTS],
        "agent_models": list(set(exp["agent_id"] for exp in DEMO_EXPERIMENTS)),
        "scenarios": list(set(exp["scenario_id"] for exp in DEMO_EXPERIMENTS)),
        "statuses": list(set(exp["status"] for exp in DEMO_EXPERIMENTS)),
        "description": "Demo data includes realistic business simulation experiments with various AI agents, scenarios, and completion states for development and testing purposes.",
    }
