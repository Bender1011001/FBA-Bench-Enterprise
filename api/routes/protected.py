"""Example protected routes demonstrating JWT middleware usage."""
from fastapi import APIRouter, Depends

from ..jwt import get_current_user
from typing import Dict, Any


router = APIRouter(prefix="/protected")


@router.get("/ping")
async def ping(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Example protected endpoint returning status (demonstrates auth guarding)."""
    return {"status": "ok"}