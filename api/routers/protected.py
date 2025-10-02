"""Protected routes requiring JWT authentication."""

from fastapi import APIRouter, Depends
from api.security.jwt import get_current_user
from api.models import User

router = APIRouter(prefix="/protected", tags=["protected"])


@router.get("/test")
def protected_test(current_user: User = Depends(get_current_user)):
    """Return the current user's identifiers (for tests)."""
    return {"user_id": current_user.id, "email": current_user.email}