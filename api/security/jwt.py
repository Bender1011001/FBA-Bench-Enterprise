"""JWT utilities and authentication dependency for FBA-Bench Enterprise."""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy import func, cast, String
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError

from api.config import (
    JWT_SECRET,
    JWT_ALGORITHM,
    ACCESS_TOKEN_EXPIRES_MINUTES,
)
from api.dependencies import get_db
from api.db import ensure_schema
from api.models import User

ISSUER = "fba-bench-enterprise"
LEEWAY_SECONDS = 10

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
    options = {"require": ["exp", "iss"], "verify_aud": False, "leeway": LEEWAY_SECONDS}
    return jwt.decode(
        token,
        JWT_SECRET,
        algorithms=[JWT_ALGORITHM],
        issuer=ISSUER,
        options=options,
    )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Return the current ORM User or raise 401 on failure."""
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Ensure schema exists for this session's bind (idempotent)
    ensure_schema(db)

    token = credentials.credentials
    try:
        payload: Dict[str, Any] = decode_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_or_expired_token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email = (payload.get("email") or "").strip().lower()
    sub = payload.get("sub")
    if not sub and not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_or_expired_token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = None
    try:
        if email:
            user = db.query(User).filter(func.lower(User.email) == email).first()
        if not user and sub:
            # Try PK direct first
            user = db.get(User, sub)
            if not user:
                # Cast PK to String to handle UUID/typed PK mismatches
                user = (
                    db.query(User)
                    .filter(
                        (User.id == sub) | (cast(User.id, String) == str(sub))
                    )
                    .first()
                )
        # Visibility-safe retry for email lookup to handle transaction visibility edge cases in tests
        if not user and email:
            db.expire_all()
            user = db.query(User).filter(func.lower(User.email) == email).first()
    except OperationalError:
        # If the users table doesn't exist on this bind (common in tests with custom engines),
        # ensure schema and retry once
        ensure_schema(db)
        if email:
            user = db.query(User).filter(func.lower(User.email) == email).first()
        if not user and sub:
            user = db.get(User, sub)
            if not user:
                user = (
                    db.query(User)
                    .filter(
                        (User.id == sub) | (cast(User.id, String) == str(sub))
                    )
                    .first()
                )
        if not user and email:
            db.expire_all()
            user = db.query(User).filter(func.lower(User.email) == email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if hasattr(user, "is_active") and user.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user