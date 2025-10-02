"""Auth router for FBA-Bench Enterprise.

Handles user registration endpoint.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from uuid import uuid4
import re

from api.db import get_db
from api.models import User
from api.schemas.auth import LoginRequest, RegistrationRequest, TokenResponse, UserPublic
from api.security.passwords import hash_password, verify_password
from api.security.jwt import create_access_token, get_current_user
from api.config import ACCESS_TOKEN_EXPIRES_MINUTES


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserPublic, status_code=201)
def register_user(
    request: RegistrationRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new user with email and password.

    Validates input, checks for duplicates, hashes password,
    and persists the user. Returns safe user fields.
    """
    # Normalize email
    email = request.email.lower().strip()

    # Check for existing user by email (case-insensitive)
    existing_user = db.query(User).filter(func.lower(User.email) == email).first()
    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )

    # Validate password policy
    if not 8 <= len(request.password) <= 128:
        raise HTTPException(
            status_code=400,
            detail="Password must be 8-128 characters long"
        )
    if not re.search(r'[a-z]', request.password):
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least one lowercase letter"
        )
    if not re.search(r'[A-Z]', request.password):
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least one uppercase letter"
        )
    if not re.search(r'\d', request.password):
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least one digit"
        )
    if not re.search(r'[^a-zA-Z0-9]', request.password):
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least one symbol (non-alphanumeric)"
        )

    # Hash password
    password_hash = hash_password(request.password)

    # Create new user
    user = User(
        id=str(uuid4()),
        email=email,
        password_hash=password_hash,
        is_active=True,
        subscription_status=None
    )

    # Persist user
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )

    # Return safe fields
    return UserPublic.model_validate(user)


@router.post("/login", response_model=TokenResponse)
def login_user(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return short-lived JWT access token.
    """
    # Normalize email
    email = request.email.lower().strip()

    # Fetch user by normalized email
    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="Inactive account"
        )

    # Create access token
    claims = {
        "sub": user.id,
        "email": user.email,
        "token_type": "access"
    }
    access_token = create_access_token(claims)

    expires_in = ACCESS_TOKEN_EXPIRES_MINUTES * 60

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": expires_in
    }


@router.get("/me", response_model=UserPublic)
def get_profile(current_user: User = Depends(get_current_user)):
    """
    Retrieve the authenticated user's public profile.
    """
    return current_user