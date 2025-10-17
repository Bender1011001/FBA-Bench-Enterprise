"""
Stub router for ClearML status.
"""

import logging

from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/stack/clearml/status")
async def clearml_status():
    logger.info("GET /stack/clearml/status")
    return {"status": "disabled", "connected": False, "version": "0.0.0"}
