"""JWT utilities for access token creation, decoding, and FastAPI dependency.

Provides secure JWT handling with expiration and user loading.
"""
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt.exceptions import PyJWTError, ExpiredSignatureError, InvalidTokenError

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .config import JWT_SECRET, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRES_MINUTES
from .models import User
from .db import get_session


security = HTTPBearer(auto_error=False)


def create_access_token(payload: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token from payload, adding exp claim if needed.

    Payload must include 'sub' with user ID. Uses UTC and numeric exp (Unix timestamp).
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRES_MINUTES)
    
    payload_copy = payload.copy()
    expire_unix = int(expire.timestamp())
    if "exp" not in payload_copy:
        payload_copy["exp"] = expire_unix
    
    encoded_jwt = jwt.encode(
        payload_copy, JWT_SECRET, algorithm=JWT_ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> Dict:
    """Decode and validate JWT token, returning payload.

    Validates signature and expiration. Raises PyJWTError on failure.
    """
    try:
        payload = jwt.decode(
            token, JWT_SECRET, algorithms=[JWT_ALGORITHM], options={"verify_exp": True}
        )
        return payload
    except (ExpiredSignatureError, InvalidTokenError, PyJWTError):
        raise PyJWTError("Token validation failed")


async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Dict[str, Any]:
    """FastAPI dependency to get current user from bearer token.

    Extracts token, decodes it, loads user from DB, raises 401 on failure.
    Returns safe user fields as dict to avoid session detachment issues.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    try:
        payload = decode_token(token)
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    with get_session() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {
            "id": user.id,
            "email": user.email,
            "is_active": user.is_active,
            "subscription_status": user.subscription_status,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        }