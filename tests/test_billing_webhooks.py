"""Unit tests for the Stripe webhook endpoint."""

import os
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from alembic import command
from alembic.config import Config
from sqlalchemy import text, create_engine
from sqlalchemy.orm import Session

from api.server import app
from api.db import get_db, get_engine
from api.models import Base, User
from api.routers.billing import resolve_user
from stripe.error import SignatureVerificationError

from pathlib import Path


# Configure test database URL before importing modules that depend on it
TEST_DB = "enterprise_test_webhooks.db"
os.environ["DATABASE_URL"] = f"sqlite:///./{TEST_DB}"


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    """Set up the test database with Base.metadata.create_all."""
    db_path = Path(TEST_DB)
    if db_path.exists():
        db_path.unlink()

    engine = get_engine()
    Base.metadata.create_all(bind=engine)

    yield

    # Teardown: drop all tables and remove DB file
    Base.metadata.drop_all(bind=engine)
    if db_path.exists():
        db_path.unlink(missing_ok=True)


@pytest.fixture(autouse=True)
def clean_db():
    """Clean the users table before each test to ensure fresh state."""
    db = next(get_db())
    try:
        db.execute(text("DELETE FROM users"))
        db.commit()
    except Exception:
        # Table may not exist yet; it's clean
        pass


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db_session() -> Session:
    """Provide a DB session for direct queries."""
    with get_session() as session:
        yield session


@pytest.fixture
def test_user():
    """Create a test user in the DB."""
    db = next(get_db())
    user = User(
        id="test-uuid-123",
        email="webhook_user@example.com",
        password_hash="hashed_password",
        is_active=True,
        subscription_status=None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_mock_event(event_type: str, data_object: dict = None) -> dict:
    """Helper to create mock event dict."""
    return {
        "type": event_type,
        "data": {"object": data_object or {}},
    }


class MockWebhook:
    """Mock for stripe.Webhook.construct_event."""

    def __init__(self, event_dict):
        self.return_value = event_dict

    def construct_event(self, *args, **kwargs):
        return self.return_value


@pytest.fixture
def patch_construct_event(monkeypatch):
    """Patch stripe.Webhook.construct_event to return provided event."""
    def _patch(event_dict):
        monkeypatch.setattr(
            "stripe.Webhook",
            MockWebhook(event_dict)
        )
    return _patch


def test_webhook_503_when_secret_missing(client: TestClient):
    """Unset STRIPE_WEBHOOK_SECRET → expect 503 "Billing unavailable"."""
    if "STRIPE_WEBHOOK_SECRET" in os.environ:
        del os.environ["STRIPE_WEBHOOK_SECRET"]

    payload = b'{"id": "evt_test"}'
    response = client.post(
        "/billing/webhook",
        content=payload,
        headers={"Stripe-Signature": "test_sig"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Billing unavailable"


def test_webhook_400_on_invalid_signature(client: TestClient, monkeypatch):
    """Patch construct_event to raise SignatureVerificationError → expect 400 "Invalid signature"."""
    os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test"
    monkeypatch.setattr(
        "stripe.Webhook.construct_event",
        MagicMock(side_effect=SignatureVerificationError("Invalid", "sig")),
    )

    payload = b'{"id": "evt_test"}'
    response = client.post(
        "/billing/webhook",
        content=payload,
        headers={"Stripe-Signature": "invalid"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid signature"


def test_checkout_session_completed_sets_active_by_email(client: TestClient, test_user, patch_construct_event):
    """checkout.session.completed with customer_details.email → set "active"."""
    os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test"
    event = create_mock_event(
        "checkout.session.completed",
        {
            "mode": "subscription",
            "payment_status": "paid",
            "customer_details": {"email": "webhook_user@example.com"},
        },
    )
    patch_construct_event(event)

    payload = b'{"type": "checkout.session.completed"}'
    response = client.post(
        "/billing/webhook",
        content=payload,
        headers={"Stripe-Signature": "valid_sig"},
    )

    assert response.status_code == 200
    assert response.json() == {"received": True}

    with get_session() as session:
        updated = session.query(User).filter(User.id == "test-uuid-123").first()
        assert updated.subscription_status == "active"


def test_checkout_session_completed_sets_active_by_metadata(client: TestClient, test_user, patch_construct_event):
    """checkout.session.completed with metadata.user_id → set "active"."""
    os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test"
    event = create_mock_event(
        "checkout.session.completed",
        {
            "mode": "subscription",
            "payment_status": "paid",
            "metadata": {"user_id": "test-uuid-123"},
        },
    )
    patch_construct_event(event)

    payload = b'{"type": "checkout.session.completed"}'
    response = client.post(
        "/billing/webhook",
        content=payload,
        headers={"Stripe-Signature": "valid_sig"},
    )

    assert response.status_code == 200
    assert response.json() == {"received": True}

    with get_session() as session:
        updated = session.query(User).filter(User.id == "test-uuid-123").first()
        assert updated.subscription_status == "active"


def test_checkout_session_completed_sets_active_by_client_ref(client: TestClient, test_user, patch_construct_event):
    """checkout.session.completed with client_reference_id → set "active"."""
    os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test"
    event = create_mock_event(
        "checkout.session.completed",
        {
            "mode": "subscription",
            "payment_status": "paid",
            "client_reference_id": "test-uuid-123",
        },
    )
    patch_construct_event(event)

    payload = b'{"type": "checkout.session.completed"}'
    response = client.post(
        "/billing/webhook",
        content=payload,
        headers={"Stripe-Signature": "valid_sig"},
    )

    assert response.status_code == 200
    assert response.json() == {"received": True}

    with get_session() as session:
        updated = session.query(User).filter(User.id == "test-uuid-123").first()
        assert updated.subscription_status == "active"


def test_subscription_updated_maps_status_from_event(client: TestClient, test_user, patch_construct_event):
    """customer.subscription.updated maps statuses per rules."""
    os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test"
    statuses = [
        ("active", "active"),
        ("trialing", "active"),
        ("past_due", "past_due"),
        ("unpaid", "past_due"),
        ("canceled", "canceled"),
        ("incomplete_expired", "canceled"),
    ]
    for stripe_status, expected in statuses:
        event = create_mock_event(
            "customer.subscription.updated",
            {"status": stripe_status, "metadata": {"user_id": "test-uuid-123"}},
        )
        patch_construct_event(event)

        payload = b'{"type": "customer.subscription.updated"}'
        response = client.post(
            "/billing/webhook",
            content=payload,
            headers={"Stripe-Signature": "valid_sig"},
        )

        assert response.status_code == 200
        assert response.json() == {"received": True}

        with get_session() as session:
            updated = session.query(User).filter(User.id == "test-uuid-123").first()
            assert updated.subscription_status == expected


def test_subscription_updated_ignores_unknown_status(client: TestClient, test_user, patch_construct_event):
    """customer.subscription.updated with unknown status → ignore (no change)."""
    os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test"
    db = next(get_db())
    existing_user = db.query(User).filter(User.id == test_user.id).first()
    existing_user.subscription_status = "active"
    db.commit()
    event = create_mock_event(
        "customer.subscription.updated",
        {"status": "unknown", "metadata": {"user_id": "test-uuid-123"}},
    )
    patch_construct_event(event)

    payload = b'{"type": "customer.subscription.updated"}'
    response = client.post(
        "/billing/webhook",
        content=payload,
        headers={"Stripe-Signature": "valid_sig"},
    )

    assert response.status_code == 200
    assert response.json() == {"received": True}

    with get_session() as session:
        updated = session.query(User).filter(User.id == "test-uuid-123").first()
        assert updated.subscription_status == "active"  # Unchanged


def test_subscription_deleted_sets_canceled(client: TestClient, test_user, patch_construct_event):
    """customer.subscription.deleted → "canceled"."""
    os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test"
    event = create_mock_event(
        "customer.subscription.deleted",
        {"metadata": {"user_id": "test-uuid-123"}},
    )
    patch_construct_event(event)

    payload = b'{"type": "customer.subscription.deleted"}'
    response = client.post(
        "/billing/webhook",
        content=payload,
        headers={"Stripe-Signature": "valid_sig"},
    )

    assert response.status_code == 200
    assert response.json() == {"received": True}

    with get_session() as session:
        updated = session.query(User).filter(User.id == "test-uuid-123").first()
        assert updated.subscription_status == "canceled"


def test_invoice_payment_succeeded_sets_active(client: TestClient, test_user, patch_construct_event):
    """invoice.payment_succeeded → "active" via customer_email."""
    os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test"
    event = create_mock_event(
        "invoice.payment_succeeded",
        {"customer_email": "webhook_user@example.com"},
    )
    patch_construct_event(event)

    payload = b'{"type": "invoice.payment_succeeded"}'
    response = client.post(
        "/billing/webhook",
        content=payload,
        headers={"Stripe-Signature": "valid_sig"},
    )

    assert response.status_code == 200
    assert response.json() == {"received": True}

    with get_session() as session:
        updated = session.query(User).filter(User.id == "test-uuid-123").first()
        assert updated.subscription_status == "active"


def test_invoice_payment_failed_sets_past_due(client: TestClient, test_user, patch_construct_event):
    """invoice.payment_failed → "past_due" via customer_email."""
    os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test"
    event = create_mock_event(
        "invoice.payment_failed",
        {"customer_email": "webhook_user@example.com"},
    )
    patch_construct_event(event)

    payload = b'{"type": "invoice.payment_failed"}'
    response = client.post(
        "/billing/webhook",
        content=payload,
        headers={"Stripe-Signature": "valid_sig"},
    )

    assert response.status_code == 200
    assert response.json() == {"received": True}

    with get_session() as session:
        updated = session.query(User).filter(User.id == "test-uuid-123").first()
        assert updated.subscription_status == "past_due"


def test_ignores_when_user_not_resolved(client: TestClient, patch_construct_event):
    """Valid event but no resolvable user → 200 and no DB change."""
    os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test"
    # No users in DB
    event = create_mock_event(
        "checkout.session.completed",
        {"mode": "subscription", "payment_status": "paid", "customer_email": "unknown@example.com"},
    )
    patch_construct_event(event)

    payload = b'{"type": "checkout.session.completed"}'
    response = client.post(
        "/billing/webhook",
        content=payload,
        headers={"Stripe-Signature": "valid_sig"},
    )

    assert response.status_code == 200
    assert response.json() == {"received": True}

    with get_session() as session:
        users = session.query(User).count()
        assert users == 0  # No change


def test_ignores_unknown_event(client: TestClient, test_user, patch_construct_event):
    """Unknown event type → 200, no DB change."""
    os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test"
    db = next(get_db())
    existing_user = db.query(User).filter(User.id == test_user.id).first()
    existing_user.subscription_status = "active"
    db.commit()
    event = create_mock_event("unknown.event", {"metadata": {"user_id": "test-uuid-123"}})
    patch_construct_event(event)

    payload = b'{"type": "unknown.event"}'
    response = client.post(
        "/billing/webhook",
        content=payload,
        headers={"Stripe-Signature": "valid_sig"},
    )

    assert response.status_code == 200
    assert response.json() == {"received": True}

    with get_session() as session:
        updated = session.query(User).filter(User.id == "test-uuid-123").first()
        assert updated.subscription_status == "active"  # Unchanged


def test_idempotency_same_event_twice(client: TestClient, test_user, patch_construct_event):
    """Send same event twice → status correct, no error."""
    os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test"
    event = create_mock_event(
        "customer.subscription.updated",
        {"status": "active", "metadata": {"user_id": "test-uuid-123"}},
    )
    patch_construct_event(event)

    payload = b'{"type": "customer.subscription.updated"}'

    # First call
    response1 = client.post(
        "/billing/webhook",
        content=payload,
        headers={"Stripe-Signature": "valid_sig"},
    )
    assert response1.status_code == 200

    # Second call (same)
    response2 = client.post(
        "/billing/webhook",
        content=payload,
        headers={"Stripe-Signature": "valid_sig"},
    )
    assert response2.status_code == 200

    with get_session() as session:
        updated = session.query(User).filter(User.id == "test-uuid-123").first()
        assert updated.subscription_status == "active"  # Set once