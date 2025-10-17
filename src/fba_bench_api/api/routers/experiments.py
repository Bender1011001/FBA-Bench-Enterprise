"""
Stub router for experiments.
"""

import logging

from fastapi import APIRouter, Query

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/experiments")
async def get_experiments(project: str = Query("FBA-Bench")):
    logger.info(f"GET /experiments?project={project}")
    return {"experiments": []}  # Direct array for frontend filter
