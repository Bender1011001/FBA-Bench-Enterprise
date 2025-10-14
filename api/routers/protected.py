"""Protected routes requiring JWT authentication."""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from api.dependencies import get_db
from api.security.jwt import get_current_user
from api.models import User

router = APIRouter(prefix="/protected", tags=["protected"])


async def require_user_protected(request: Request, db: Session = Depends(get_db)) -> User:
    auth = request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        # Normalize missing/invalid scheme to test-expected detail
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    token = auth[7:].lstrip()
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    try:
        return await get_current_user(credentials=credentials, db=db)
    except HTTPException as exc:
        # Normalize any upstream 401 into the protected-route contract
        if exc.status_code == 401:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
        raise


@router.get("/test")
def protected_test(user: User = Depends(require_user_protected)):
    """Return the current user's identifiers (for tests)."""
    return {"user_id": user.id, "email": user.email}


@router.get("/ping")
def protected_ping(user: User = Depends(get_current_user)):
    """Ping endpoint for protected route testing."""
    return {"status": "ok"}