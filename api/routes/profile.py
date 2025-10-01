"""Profile routes for authenticated user profile retrieval."""
from fastapi import APIRouter, Depends

from ..jwt import get_current_user
from typing import Dict, Any


router = APIRouter()


@router.get("/me", response_model=dict)
async def get_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Retrieve the authenticated user's profile (safe fields only)."""
    return current_user