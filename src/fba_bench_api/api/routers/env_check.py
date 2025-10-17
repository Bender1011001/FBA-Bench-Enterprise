"""
Stub router for environment check.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/env-check")
async def env_check():
    """Environment check endpoint (stub)."""
    return {"env": "development", "status": "ready"}
