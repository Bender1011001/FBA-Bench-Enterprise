from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional


class RegistrationRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    email: str
    is_active: bool
    subscription_status: Optional[str] = None
    created_at: datetime
    updated_at: datetime