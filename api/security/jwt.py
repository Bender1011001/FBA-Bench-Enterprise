"""JWT utilities and authentication dependency for FBA-Bench Enterprise."""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from api.config import (
    JWT_SECRET,
    JWT_ALGORITHM,
    ACCESS_TOKEN_EXPIRES_MINUTES,
)
from api.db import get_db
from api.models import User

ISSUER = "fba-bench-enterprise"

security = HTTPBearer(auto_error=False)


def create_access_token(payload: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token from payload, adding exp and iss if not present.

    - Ensures `iss` is set to the canonical issuer for tests and production defaults.
    - Sets `exp` as a numeric (Unix timestamp) for portability across JWT libs.
    """
    to_encode = payload.copy()

    # Ensure issuer claim
    if "iss" not in to_encode:
        to_encode["iss"] = ISSUER

    # Compute default expiration
    expire_at = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRES_MINUTES)
    )

    # Normalize/set exp to numeric timestamp
    if "exp" in to_encode:
        exp_val = to_encode["exp"]
        if isinstance(exp_val, datetime):
            to_encode["exp"] = int(exp_val.timestamp())
        elif isinstance(exp_val, (int, float)):
            to_encode["exp"] = int(exp_val)
        else:
            # Fallback: reset to computed default if unknown type
            to_encode["exp"] = int(expire_at.timestamp())
    else:
        to_encode["exp"] = int(expire_at.timestamp())

    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token, returning the payload."""
    return jwt.decode(
        token,
        JWT_SECRET,
        algorithms=[JWT_ALGORITHM],
        options={"verify_aud": False},
    )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Return the current ORM User or raise 401 on failure."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not credentials or credentials.scheme.lower() != "bearer":
        raise credentials_exception

    token = credentials.credentials
    try:
        payload: Dict[str, Any] = decode_token(token)
    except JWTError:
        raise credentials_exception

    user_id = payload.get("sub")
    if not user_id:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise credentials_exception

    return user