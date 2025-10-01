"""Billing routes for the FBA-Bench Enterprise API.

Implements the /billing/checkout-session endpoint for creating Stripe Checkout sessions.
"""

from typing import Optional
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, validator

import stripe
from stripe.error import StripeError

from ..config import (
    STRIPE_SECRET_KEY,
    STRIPE_DEFAULT_PRICE_ID,
    PUBLIC_APP_BASE_URL,
    STRIPE_PORTAL_RETURN_PATH,
)

from ..jwt import get_current_user
from ..models import User


class CheckoutSessionRequest(BaseModel):
    price_id: Optional[str] = None
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None
    quantity: Optional[int] = 1
    mode: Optional[str] = "subscription"

    @validator("quantity")
    def validate_quantity(cls, v):
        if v < 1:
            raise ValueError("quantity must be at least 1")
        return v

    @validator("mode")
    def validate_mode(cls, v):
        if v not in ["subscription", "payment"]:
            raise ValueError("mode must be 'subscription' or 'payment'")
        return v

    @validator("success_url", "cancel_url", pre=True, always=True)
    def validate_urls(cls, v, values, field):
        base_url = values.get("success_url") if field.name == "cancel_url" else values.get("cancel_url")
        if v is None:
            return f"{PUBLIC_APP_BASE_URL}/billing/{'success' if field.name == 'success_url' else 'cancel'}"
        parsed = urlparse(v)
        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"{field.name} must be a valid HTTP/HTTPS URL")
        return v


class CheckoutSessionResponse(BaseModel):
    url: str


class PortalSessionResponse(BaseModel):
    url: str


router = APIRouter(prefix="/billing")


@router.post("/checkout-session", response_model=CheckoutSessionResponse)
async def create_checkout_session(request: CheckoutSessionRequest):
    """Create a Stripe Checkout session for subscriptions or payments."""
    if not STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=500,
            detail="Stripe configuration is not available. Please check your environment settings.",
        )

    price_id = request.price_id or STRIPE_DEFAULT_PRICE_ID
    if not price_id:
        raise HTTPException(
            status_code=400,
            detail="price_id required",
        )

    try:
        stripe.api_key = STRIPE_SECRET_KEY

        session = stripe.checkout.Session.create(
            mode=request.mode,
            line_items=[{"price": price_id, "quantity": request.quantity}],
            success_url=request.success_url,
            cancel_url=request.cancel_url,
        )

        return CheckoutSessionResponse(url=session.url)
    except StripeError:
        raise HTTPException(
            status_code=502,
            detail="Stripe error",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.post("/portal-session", response_model=PortalSessionResponse)
async def create_portal_session(current_user: dict = Depends(get_current_user)):
    """Create a Stripe Billing Portal session for the authenticated user."""
    user_email = current_user.get("email")
    if not user_email:
        raise HTTPException(
            status_code=400,
            detail="User email missing",
        )

    if not STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=500,
            detail="Stripe secret missing",
        )

    try:
        stripe.api_key = STRIPE_SECRET_KEY

        # Resolve or create Stripe customer
        customers = stripe.Customer.list(email=user_email, limit=1)
        if customers.data:
            customer_id = customers.data[0].id
        else:
            customer = stripe.Customer.create(email=user_email)
            customer_id = customer.id

        # Create portal session
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=f"{PUBLIC_APP_BASE_URL}{STRIPE_PORTAL_RETURN_PATH}",
        )

        return PortalSessionResponse(url=session.url)
    except StripeError:
        raise HTTPException(
            status_code=502,
            detail="Stripe error",
        )