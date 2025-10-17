import os

import pytest
from api.db import Base, get_db
from api.models import User
from api.server import app
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from stripe.error import SignatureVerificationError

# Set test-specific env
os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test_secret"
os.environ["DATABASE_URL"] = "sqlite:///./test_webhooks.db"

# Test database setup
engine = create_engine(os.environ["DATABASE_URL"])
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Override get_db for tests
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# Create tables before tests
Base.metadata.create_all(bind=engine)


def create_test_user(db, user_id: str, email: str, subscription_status: str = None):
    user = User(
        id=user_id,
        email=email,
        password_hash="test_hash",
        subscription_status=subscription_status,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


class TestStripeWebhooks:
    @pytest.fixture(autouse=True)
    def setup_db(self, monkeypatch):
        # Clean DB before each test
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def test_webhook_400_on_invalid_signature(self, monkeypatch):
        # Monkeypatch to raise SignatureVerificationError (simulating invalid signature)
        def mock_construct_event(payload, sig_header, secret):
            raise SignatureVerificationError("Invalid signature", "sig")

        monkeypatch.setattr("stripe.Webhook.construct_event", mock_construct_event)

        payload = b'{"id": "evt_test", "type": "test.event"}'
        headers = {"Stripe-Signature": "test_sig"}

        response = client.post(
            "/billing/webhook",
            content=payload,
            headers=headers,
        )

        assert response.status_code == 400
        assert response.json() == {"detail": "invalid_signature"}

    def test_checkout_session_completed_sets_active_by_metadata_user_id(
        self, monkeypatch
    ):
        # Setup
        db = TestingSessionLocal()
        user_id = "user-123"
        email = "user@example.com"
        create_test_user(db, user_id, email, subscription_status=None)

        # Mock construct_event to return event
        event_data = {
            "id": "evt_123",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "mode": "subscription",
                    "payment_status": "paid",
                    "metadata": {"user_id": user_id},
                }
            },
        }

        def mock_construct_event(payload, sig_header, secret):
            return event_data

        monkeypatch.setattr("stripe.Webhook.construct_event", mock_construct_event)

        payload = b'{"type": "checkout.session.completed"}'  # Actual payload doesn't matter due to mock
        headers = {"Stripe-Signature": "test_sig"}

        response = client.post(
            "/billing/webhook",
            content=payload,
            headers=headers,
        )

        assert response.status_code == 200
        assert response.json() == {"received": True}

        # Verify DB update
        updated_user = db.query(User).filter(User.id == user_id).first()
        assert updated_user.subscription_status == "active"
        db.close()

    def test_checkout_session_completed_sets_active_by_customer_email(
        self, monkeypatch
    ):
        # Setup
        db = TestingSessionLocal()
        user_id = "user-456"
        email = "user2@example.com"
        create_test_user(db, user_id, email, subscription_status=None)

        # Mock event without metadata.user_id but with customer_email
        event_data = {
            "id": "evt_456",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "mode": "subscription",
                    "payment_status": "paid",
                    "customer_email": email,
                    # No metadata.user_id
                }
            },
        }

        def mock_construct_event(payload, sig_header, secret):
            return event_data

        monkeypatch.setattr("stripe.Webhook.construct_event", mock_construct_event)

        payload = b'{"type": "checkout.session.completed"}'
        headers = {"Stripe-Signature": "test_sig"}

        response = client.post(
            "/billing/webhook",
            content=payload,
            headers=headers,
        )

        assert response.status_code == 200
        assert response.json() == {"received": True}

        # Verify DB update
        updated_user = db.query(User).filter(User.email == email).first()
        assert updated_user.subscription_status == "active"
        db.close()

    def test_subscription_updated_sets_past_due(self, monkeypatch):
        # Setup
        db = TestingSessionLocal()
        user_id = "user-789"
        email = "user3@example.com"
        create_test_user(db, user_id, email, subscription_status="active")

        # Mock event
        event_data = {
            "id": "evt_789",
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "status": "past_due",
                    "metadata": {"user_id": user_id},
                }
            },
        }

        def mock_construct_event(payload, sig_header, secret):
            return event_data

        monkeypatch.setattr("stripe.Webhook.construct_event", mock_construct_event)

        payload = b'{"type": "customer.subscription.updated"}'
        headers = {"Stripe-Signature": "test_sig"}

        response = client.post(
            "/billing/webhook",
            content=payload,
            headers=headers,
        )

        assert response.status_code == 200
        assert response.json() == {"received": True}

        # Verify DB update
        updated_user = db.query(User).filter(User.id == user_id).first()
        assert updated_user.subscription_status == "past_due"
        db.close()

    def test_subscription_deleted_sets_canceled(self, monkeypatch):
        # Setup
        db = TestingSessionLocal()
        user_id = "user-101"
        email = "user4@example.com"
        create_test_user(db, user_id, email, subscription_status="active")

        # Mock event
        event_data = {
            "id": "evt_101",
            "type": "customer.subscription.deleted",
            "data": {
                "object": {
                    "metadata": {"user_id": user_id},
                }
            },
        }

        def mock_construct_event(payload, sig_header, secret):
            return event_data

        monkeypatch.setattr("stripe.Webhook.construct_event", mock_construct_event)

        payload = b'{"type": "customer.subscription.deleted"}'
        headers = {"Stripe-Signature": "test_sig"}

        response = client.post(
            "/billing/webhook",
            content=payload,
            headers=headers,
        )

        assert response.status_code == 200
        assert response.json() == {"received": True}

        # Verify DB update
        updated_user = db.query(User).filter(User.id == user_id).first()
        assert updated_user.subscription_status == "canceled"
        db.close()

    def test_unknown_event_type_is_ignored_with_200(self, monkeypatch):
        # Setup
        db = TestingSessionLocal()
        user_id = "user-unknown"
        email = "user5@example.com"
        create_test_user(db, user_id, email, subscription_status="active")

        # Mock event with unknown type
        event_data = {
            "id": "evt_unknown",
            "type": "unknown.event.type",
            "data": {
                "object": {
                    "metadata": {"user_id": user_id},
                }
            },
        }

        def mock_construct_event(payload, sig_header, secret):
            return event_data

        monkeypatch.setattr("stripe.Webhook.construct_event", mock_construct_event)

        payload = b'{"type": "unknown.event.type"}'
        headers = {"Stripe-Signature": "test_sig"}

        response = client.post(
            "/billing/webhook",
            content=payload,
            headers=headers,
        )

        assert response.status_code == 200
        assert response.json() == {"received": True, "ignored": True}

        # Verify no DB change
        updated_user = db.query(User).filter(User.id == user_id).first()
        assert updated_user.subscription_status == "active"
        db.close()

    def test_webhook_user_not_found_returns_200(self, monkeypatch):
        # Mock event with non-existent user_id
        event_data = {
            "id": "evt_notfound",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "mode": "subscription",
                    "payment_status": "paid",
                    "metadata": {"user_id": "nonexistent"},
                }
            },
        }

        def mock_construct_event(payload, sig_header, secret):
            return event_data

        monkeypatch.setattr("stripe.Webhook.construct_event", mock_construct_event)

        payload = b'{"type": "checkout.session.completed"}'
        headers = {"Stripe-Signature": "test_sig"}

        response = client.post(
            "/billing/webhook",
            content=payload,
            headers=headers,
        )

        assert response.status_code == 200
        assert response.json() == {"received": True, "note": "user_not_found"}

    def test_webhook_no_webhook_secret_returns_503(self):
        # Unset secret
        del os.environ["STRIPE_WEBHOOK_SECRET"]

        payload = b'{"type": "test"}'
        headers = {"Stripe-Signature": "test_sig"}

        response = client.post(
            "/billing/webhook",
            content=payload,
            headers=headers,
        )

        assert response.status_code == 503
        assert response.json() == {"detail": "webhook_not_configured"}
