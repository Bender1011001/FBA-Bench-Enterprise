"""
Stub router for system stats.
"""

from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/stats")
async def get_stats():
    logger.info("GET /stats")
    return {"cpu": 0, "memory": 0, "status": "healthy"}