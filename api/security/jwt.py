"""JWT utilities and authentication dependency for FBA-Bench Enterprise.

Provides token creation, verification, and a FastAPI dependency to get the current user.
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

from fastapi import Depends, HTTPException, status, Header
from fastapi.security.utils import get_authorization_scheme_param
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from ..config import settings

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

from api.db import get_db
from api.models import User






def create_access_token(claims: Dict[str, Any]) -> str:
    """Create a short-lived access token."""
    to_encode = claims.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({
        "token_type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "iss": "fba-bench-enterprise",
    })
    encoded = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and verify a JWT token, raising HTTPException on failure."""
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_aud": False},
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_or_expired_token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    db: Session = Depends(get_db),
    authorization: str = Header(None),
) -> User:
    """FastAPI dependency to get the current active user from JWT."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="invalid_or_expired_token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Extract token
    scheme, token = get_authorization_scheme_param(authorization)
    if not (scheme and scheme.lower() == "bearer"):
        raise credentials_exception
    
    # Decode token
    payload = decode_token(token)
    if payload.get("token_type") != "access":
        raise credentials_exception
    
    user_id: str = payload.get("sub")
    if not user_id:
        raise credentials_exception
    
    # Fetch user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="inactive_user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user