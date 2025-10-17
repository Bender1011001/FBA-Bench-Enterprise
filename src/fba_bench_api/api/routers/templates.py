"""
Stub router for templates.
"""

import logging

from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/templates")
async def get_templates():
    logger.info("GET /templates")
    return {"templates": []}
