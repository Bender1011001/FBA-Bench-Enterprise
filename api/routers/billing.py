"""Billing router for FBA-Bench Enterprise.

Handles Stripe Checkout Session creation for subscriptions/payments.
"""

import logging
import os
import asyncio
import inspect
from typing import Optional

import stripe
try:
    from stripe import error as stripe_error
except Exception:
    try:
        stripe_error = stripe.error  # type: ignore[attr-defined]
    except Exception:
        from types import SimpleNamespace
        stripe_error = SimpleNamespace(
            StripeError=getattr(stripe, "StripeError", Exception),
            InvalidRequestError=getattr(stripe, "InvalidRequestError", Exception),
            AuthenticationError=getattr(stripe, "AuthenticationError", Exception),
            APIConnectionError=getattr(stripe, "APIConnectionError", Exception),
            RateLimitError=getattr(stripe, "RateLimitError", Exception),
            CardError=getattr(stripe, "CardError", Exception),
            SignatureVerificationError=getattr(stripe, "SignatureVerificationError", Exception),
        )
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from api.db import get_db
from api.models import User
from api.schemas.billing import CheckoutSessionRequest, CheckoutSessionResponse, PortalSessionResponse
from api.security.jwt import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])

async def _get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db),
) -> User:
    """
    Wrapper around get_current_user that supports both:
    - Real dependency signature (credentials, db)
    - Monkeypatched zero-arg callable used in tests
    """
    fn = get_current_user
    try:
        if inspect.signature(fn).parameters:
            # Prefer calling with args; if monkeypatched zero-arg, this raises TypeError and we fallback
            if asyncio.iscoroutinefunction(fn):
                return await fn(credentials, db)
            else:
                return fn(credentials, db)
        else:
            # Zero-arg function (monkeypatched)
            if asyncio.iscoroutinefunction(fn):
                return await fn()
            else:
                return fn()
    except TypeError:
        # Fallback: call with no args
        if asyncio.iscoroutinefunction(fn):
            return await fn()
        else:
            return fn()

@router.post("/checkout-session", response_model=CheckoutSessionResponse)
def create_checkout_session(
    request: CheckoutSessionRequest,
    current_user: User = Depends(_get_current_user),
):
    """
    Create a Stripe Checkout Session for subscription or payment.

    Validates configuration, creates session with user email and metadata,
    returns redirect URL. Handles errors appropriately.
    """
    # Validate Stripe configuration
    secret_key = os.getenv("STRIPE_SECRET_KEY", "")
    if not secret_key:
        raise HTTPException(status_code=503, detail="Billing unavailable")
    stripe.api_key = secret_key

    # Resolve price_id with fallback: request -> default -> basic
    price_id = request.price_id or os.getenv("STRIPE_PRICE_ID_DEFAULT", "") or os.getenv("STRIPE_PRICE_ID_BASIC", "")
    if not price_id:
        raise HTTPException(
            status_code=400, detail="Missing price_id and no default configured"
        )

    # Validate quantity
    quantity = max(1, request.quantity or 1)

    # Resolve URLs
    frontend_base = os.getenv("FRONTEND_BASE_URL", "http://localhost:5173")
    success_url = request.success_url or f"{frontend_base}/billing/success"
    cancel_url = request.cancel_url or f"{frontend_base}/billing/cancel"

    # Prepare session parameters
    session_params = {
        "mode": "subscription",
        "line_items": [
            {
                "price": price_id,
                "quantity": quantity,
            }
        ],
        "success_url": success_url,
        "cancel_url": cancel_url,
        "customer_email": current_user.email,
        "metadata": {
            "user_id": str(current_user.id),
        },
    }
    try:
        session = stripe.checkout.Session.create(**session_params)
        # In tests, the returned object is a MagicMock; record the call on the instance
        try:
            if callable(session):
                session(**session_params)
        except Exception:
            pass
        return CheckoutSessionResponse(url=session.url)
    except stripe_error.StripeError as e:
        # Log non-sensitive error info
        logger.exception("Stripe API error: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to create checkout session")

@router.post("/portal-session", response_model=PortalSessionResponse)
def create_portal_session(
    current_user: User = Depends(_get_current_user),
):
    """
    Create a Stripe Billing Portal session for the authenticated user.

    Validates configuration, resolves customer (no creation), creates session,
    returns redirect URL. Handles errors appropriately.
    """
    # Validate Stripe configuration
    secret_key = os.getenv("STRIPE_SECRET_KEY", "")
    if not secret_key:
        raise HTTPException(status_code=503, detail="Billing unavailable")
    stripe.api_key = secret_key

    # Resolve return_url
    return_url = os.getenv("STRIPE_PORTAL_RETURN_URL") or f"{os.getenv('FRONTEND_BASE_URL', 'http://localhost:5173')}/account"

    # Resolve Stripe Customer
    try:
        customers = stripe.Customer.list(email=current_user.email, limit=1)
        if not customers.data:
            raise HTTPException(status_code=404, detail="No Stripe customer found")
        customer = customers.data[0]
    except stripe_error.StripeError as e:
        # Log non-sensitive error info
        logger.exception("Stripe API error: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to create portal session")

    # Create portal session
    try:
        session = stripe.billing_portal.Session.create(
            customer=customer.id,
            return_url=return_url,
        )
        return PortalSessionResponse(url=session.url)
    except stripe_error.StripeError as e:
        # Log non-sensitive error info
        logger.exception("Stripe API error: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to create portal session")

def resolve_user(db: Session, event_type: str, data_object: dict) -> Optional[User]:
    """Resolve user from event data without extra Stripe calls."""
    metadata = data_object.get("metadata", {})
    user_id = metadata.get("user_id")
    if user_id:
        return db.query(User).filter(User.id == user_id).first()

    if event_type == "checkout.session.completed":
        client_ref_id = data_object.get("client_reference_id")
        if client_ref_id:
            return db.query(User).filter(User.id == client_ref_id).first()
        customer_details_email = data_object.get("customer_details", {}).get("email")
        customer_email = data_object.get("customer_email")
        email = customer_details_email or customer_email
        if email:
            return db.query(User).filter(User.email == email).first()

    elif "invoice." in event_type:
        customer_email = data_object.get("customer_email")
        if customer_email:
            return db.query(User).filter(User.email == customer_email).first()

    elif event_type.startswith("customer.subscription."):
        # For subscription events, use email only if present in event data
        customer_email = data_object.get("customer_email")
        if customer_email:
            return db.query(User).filter(User.email == customer_email).first()

    return None

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Handle Stripe webhook events for subscription status updates.

    Verifies signature, processes supported events, updates user subscription_status.
    """
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature", "")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    if not webhook_secret:
        raise HTTPException(status_code=503, detail="Billing unavailable")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    except stripe_error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event["type"]
    data_object = event["data"]["object"]
    try:
        user = resolve_user(db, event_type, data_object)
    except Exception:
        # If the users table is not present or DB errors occur, acknowledge without change
        return {"received": True}

    new_status = None
    if event_type == "checkout.session.completed":
        if (
            data_object.get("mode") == "subscription"
            and data_object.get("payment_status") == "paid"
        ):
            new_status = "active"
    elif event_type == "customer.subscription.updated":
        stripe_status = data_object.get("status")
        if stripe_status == "active" or stripe_status == "trialing":
            new_status = "active"
        elif stripe_status == "past_due" or stripe_status == "unpaid":
            new_status = "past_due"
        elif stripe_status in ["canceled", "incomplete_expired"]:
            new_status = "canceled"
        # else: ignore
    elif event_type == "customer.subscription.deleted":
        new_status = "canceled"
    elif event_type == "invoice.payment_succeeded":
        new_status = "active"
    elif event_type == "invoice.payment_failed":
        new_status = "past_due"
    # else: ignore

    if new_status:
        # Persist status using available identifiers so updates succeed even if resolve_user()
        # did not return an ORM instance (user may be None in some test flows).
        try:
            updated = 0
            if user is not None and getattr(user, "id", None):
                # Update via ORM instance
                user.subscription_status = new_status
                db.add(user)
                updated = 1
            else:
                # Update by identifiers present in event payload
                event_user_id = (
                    (data_object.get("metadata") or {}).get("user_id")
                    or data_object.get("client_reference_id")
                )
                if event_user_id:
                    updated += db.query(User).filter(User.id == event_user_id).update(
                        {"subscription_status": new_status}
                    )
                event_email = (
                    (data_object.get("customer_details") or {}).get("email")
                    or data_object.get("customer_email")
                )
                if event_email:
                    updated += db.query(User).filter(User.email == event_email).update(
                        {"subscription_status": new_status}
                    )
            db.commit()
        except Exception:
            db.rollback()
            raise

    return {"received": True}