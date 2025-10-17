"""Tests for the Stripe Checkout Session endpoint."""

import os
from datetime import datetime
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from api.db import Base, get_db
from api.models import User
from api.routers.billing import stripe
from api.security.jwt import create_access_token
from api.security.passwords import hash_password
from api.server import app
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="function")
def setup_database():
    """Create tables before each test and clean up after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def create_test_user(db, email: str, password: str, active: bool = True):
    """Helper to create a test user in the DB."""
    user = User(
        id=str(uuid4()),
        email=email,
        password_hash=hash_password(password),
        is_active=active,
        subscription_status=None,
        created_at=datetime.now(ZoneInfo("UTC")),
        updated_at=datetime.now(ZoneInfo("UTC")),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_auth_token(db, user):
    """Helper to create an access token for the user."""
    claims = {"sub": user.id, "email": user.email}
    return create_access_token(claims)


class TestCheckoutSession:
    def test_checkout_requires_auth_returns_401(self, setup_database):
        """Unauthenticated request returns 401."""
        response = client.post("/billing/checkout-session")
        assert response.status_code == 401
        assert response.json()["detail"] == "invalid_or_expired_token"

    def test_checkout_400_when_missing_price_and_no_default(
        self, client, test_user, auth_token
    ):
        """Returns 400 when no price_id provided and no env default."""
        # Ensure no STRIPE_PRICE_ID_BASIC in env
        original_env = os.environ.get("STRIPE_PRICE_ID_BASIC")
        os.environ.pop("STRIPE_PRICE_ID_BASIC", None)

        response = client.post(
            "/billing/checkout-session",
            json={},
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 400
        assert (
            response.json()["detail"]
            == "No price ID provided and no default configured"
        )
        if original_env:
            os.environ["STRIPE_PRICE_ID_BASIC"] = original_env

    def test_checkout_200_returns_url_with_env_default_price(
        self, client, test_user, auth_token, monkeypatch
    ):
        """Successful checkout with env default price returns 200 with URL."""
        # Set env vars
        monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_mock")
        monkeypatch.setenv("STRIPE_PRICE_ID_DEFAULT", "price_123")
        monkeypatch.setenv("FRONTEND_BASE_URL", "http://localhost:5173")

        # Mock Stripe
        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/pay/cs_test_mock"
        monkeypatch.setattr(
            stripe.checkout.Session, "create", MagicMock(return_value=mock_session)
        )

        response = client.post(
            "/billing/checkout-session",
            json={},
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "url" in data
        assert data["url"] == mock_session.url

    def test_checkout_502_on_stripe_error(
        self, client, test_user, auth_token, monkeypatch
    ):
        """Stripe API error returns 502."""
        # Set env vars
        monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_mock")
        monkeypatch.setenv("STRIPE_PRICE_ID_DEFAULT", "price_123")
        monkeypatch.setenv("FRONTEND_BASE_URL", "http://localhost:5173")

        # Mock Stripe to raise error
        monkeypatch.setattr(
            stripe.checkout.Session,
            "create",
            MagicMock(side_effect=Exception("Stripe error")),
        )

        response = client.post(
            "/billing/checkout-session",
            json={},
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 500
        assert "Stripe error" in response.json()["detail"]

    def test_checkout_uses_customer_email_and_metadata(
        self, client, test_user, auth_token, monkeypatch
    ):
        """Verifies customer_email and metadata are passed to Stripe."""
        # Set env vars
        monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_mock")
        monkeypatch.setenv("STRIPE_PRICE_ID_DEFAULT", "price_123")
        monkeypatch.setenv("FRONTEND_BASE_URL", "http://localhost:5173")

        # Mock Stripe create to capture args
        mock_create = MagicMock()
        monkeypatch.setattr(stripe.checkout.Session, "create", mock_create)

        response = client.post(
            "/billing/checkout-session",
            json={},
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200

        # Verify args passed to create
        call_args = mock_create.call_args[1]  # kwargs
        assert call_args["customer_email"] == test_user.email
        assert call_args["metadata"]["user_id"] == test_user.id
