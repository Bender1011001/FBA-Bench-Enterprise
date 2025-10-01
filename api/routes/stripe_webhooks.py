"""Stripe webhook routes for the FBA-Bench Enterprise API.

Handles incoming Stripe events for subscription status updates.
"""

import stripe
from stripe.error import SignatureVerificationError

from fastapi import APIRouter, Request, HTTPException

from ..config import STRIPE_WEBHOOK_SECRET
from ..db import get_session
from ..models import User


router = APIRouter(prefix="/billing")


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events and update user subscription status."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=500, detail="Webhook secret not configured"
        )

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except SignatureVerificationError:
        raise HTTPException(
            status_code=400, detail="Invalid signature"
        )
    except ValueError:
        # Invalid payload
        raise HTTPException(
            status_code=400, detail="Invalid payload"
        )

    event_type = event.get("type")
    data_object = event.get("data", {}).get("object", {})

    email = None
    new_status = None

    if event_type == "checkout.session.completed":
        email = (
            data_object.get("customer_details", {}).get("email")
            or data_object.get("customer_email")
        )
        if (
            data_object.get("mode") == "subscription"
            and data_object.get("payment_status") == "paid"
        ):
            new_status = "active"
        else:
            new_status = "incomplete"
    elif event_type == "customer.subscription.updated":
        if "customer_email" in data_object:
            email = data_object["customer_email"]
            status = data_object.get("status")
            valid_statuses = {
                "active",
                "trialing",
                "past_due",
                "canceled",
                "unpaid",
                "incomplete",
                "incomplete_expired",
            }
            if status in valid_statuses:
                new_status = status
    elif event_type == "customer.subscription.deleted":
        if "customer_email" in data_object:
            email = data_object["customer_email"]
            new_status = "canceled"

    if email and new_status:
        with get_session() as session:
            user = session.query(User).filter(User.email == email).first()
            if user:
                user.subscription_status = new_status
                session.commit()

    return {"received": True}