"""
Basic health check router.
"""

from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health endpoint."""
    logger.info("GET /health")
    return {"status": "healthy", "managers": "initialized"}