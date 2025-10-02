from pydantic import BaseModel
from typing import Optional


class CheckoutSessionRequest(BaseModel):
    price_id: Optional[str] = None
    quantity: Optional[int] = None
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class CheckoutSessionResponse(BaseModel):
    url: str


class PortalSessionResponse(BaseModel):
    url: str