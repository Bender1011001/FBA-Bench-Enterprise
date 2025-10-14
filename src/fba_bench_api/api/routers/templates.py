"""
Stub router for templates.
"""

from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/templates")
async def get_templates():
    logger.info("GET /templates")
    return {"templates": []}