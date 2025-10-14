"""Profile routes for user information."""
from fastapi import APIRouter, Depends
from api.security.jwt import get_current_user
from api.models import User

router = APIRouter()

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    """Return the current user's profile."""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "is_active": bool(getattr(current_user, "is_active", True)),
        "subscription_status": getattr(current_user, "subscription_status", None),
    }