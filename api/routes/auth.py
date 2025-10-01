"""Authentication routes for the FBA-Bench Enterprise API.

Implements the /auth/register endpoint for user registration.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from uuid import uuid4

from email_validator import validate_email, EmailNotValidError

from ..models import User
from ..security import hash_password
from ..db import get_session
from ..config import PASSWORD_MIN_LENGTH

from datetime import timedelta
from ..jwt import create_access_token
from ..security import verify_password


class RegisterRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    is_active: bool
    subscription_status: str | None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str


router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(request: RegisterRequest):
    """Register a new user with email and password.

    Validates input, hashes password, checks for duplicates, and stores in DB.
    """
    try:
        validated_email = validate_email(request.email, check_deliverability=False).email
    except EmailNotValidError:
        raise HTTPException(
            status_code=400, detail="Invalid email or password does not meet policy"
        )

    if len(request.password) < PASSWORD_MIN_LENGTH:
        raise HTTPException(
            status_code=400, detail="Invalid email or password does not meet policy"
        )

    hashed_password = hash_password(request.password)

    user = User(
        id=str(uuid4()),
        email=validated_email,
        password_hash=hashed_password,
        is_active=True,
        subscription_status=None,
    )

    try:
        with get_session() as session:
            session.add(user)
            session.commit()
            session.refresh(user)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Email already registered")

    # Response model excludes password_hash automatically
    return user


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Login user with email and password, return access token on success."""
    with get_session() as session:
        user = session.query(User).filter(User.email == request.email).first()
        if not user or not verify_password(request.password, user.password_hash):
            raise HTTPException(
                status_code=401, detail="Invalid credentials"
            )
        access_token = create_access_token({"sub": user.id})
        return LoginResponse(access_token=access_token, token_type="bearer")