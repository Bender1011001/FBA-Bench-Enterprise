from typing import Optional, Literal
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RegistrationRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"]
    expires_in: int


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    is_active: bool
    subscription_status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None