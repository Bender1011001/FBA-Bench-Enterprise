"""
Stub router for leaderboard.
"""

from fastapi import APIRouter, Query
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/leaderboard")
async def get_leaderboard(limit: int = Query(50)):
    logger.info(f"GET /leaderboard?limit={limit}")
    # Return a raw array so the frontend can map/filter without extra unwrapping
    return []