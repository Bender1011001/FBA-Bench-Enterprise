"""Tests for the Stripe Checkout Session endpoint."""

import os
import pytest
from unittest.mock import MagicMock
from datetime import datetime
from uuid import uuid4

from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.server import app
from api.db import get_db, Base
from api.models import User
from api.security.passwords import hash_password
from api.security.jwt import create_access_token
from api.routers.billing import stripe


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
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_auth_token(db, user):
    """Helper to create an access token for the user."""
    claims = {
        "sub": user.id,
        "email": user.email
    }
    return create_access_token(claims)


class TestCheckoutSession:
    def test_checkout_requires_auth_returns_401(self, setup_database):
        """Unauthenticated request returns 401."""
        response = client.post("/billing/checkout-session")
        assert response.status_code == 401
        assert response.json()["detail"] == "invalid_or_expired_token"

    def test_checkout_400_when_missing_price_and_no_default(self, setup_database):
        """Returns 400 when no price_id provided and no env default."""
        # Ensure no STRIPE_PRICE_ID_BASIC in env
        original_env = os.environ.get("STRIPE_PRICE_ID_BASIC")
        os.environ.pop("STRIPE_PRICE_ID_BASIC", None)

        response = client.post(
            "/billing/checkout-session",
            json={},
            headers={"Authorization": "Bearer invalid_token"}  # Will be 401, but test focuses on price
        )
        # Actually, auth will fail first, but to test price validation, we need auth.
        # For this test, we'll mock auth or use a valid token but focus on price.
        # Since auth is dependency, to isolate, but task says test requires auth, so combine.

        # Create user and token
        db = TestingSessionLocal(bind=engine.connect())
        try:
            user = create_test_user(db, "test@example.com", "Password123!")
            token = get_auth_token(db, user)

            # Set env to no default
            os.environ.pop("STRIPE_PRICE_ID_BASIC", None)

            response = client.post(
                "/billing/checkout-session",
                json={},
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 400
            assert response.json()["detail"] == "invalid_price"
        finally:
            db.close()
            if original_env:
                os.environ["STRIPE_PRICE_ID_BASIC"] = original_env

    def test_checkout_200_returns_url_with_env_default_price(self, setup_database, monkeypatch):
        """Successful checkout with env default price returns 200 with URL."""
        # Set env vars
        monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_mock")
        monkeypatch.setenv("STRIPE_PRICE_ID_BASIC", "price_123")
        monkeypatch.setenv("BILLING_SUCCESS_URL", "http://example.com/success")
        monkeypatch.setenv("BILLING_CANCEL_URL", "http://example.com/cancel")
        monkeypatch.setenv("STRIPE_MODE", "subscription")

        # Mock Stripe
        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/pay/cs_test_mock"
        monkeypatch.setattr(stripe.checkout, "Session", MagicMock(create=mock_session))

        # Create user and token
        db = TestingSessionLocal(bind=engine.connect())
        try:
            user = create_test_user(db, "test@example.com", "Password123!")
            token = get_auth_token(db, user)

            response = client.post(
                "/billing/checkout-session",
                json={},
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200
            data = response.json()
            assert "url" in data
            assert data["url"] == mock_session.url
        finally:
            db.close()

    def test_checkout_502_on_stripe_error(self, setup_database, monkeypatch):
        """Stripe API error returns 502."""
        # Set env vars
        monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_mock")
        monkeypatch.setenv("STRIPE_PRICE_ID_BASIC", "price_123")
        monkeypatch.setenv("BILLING_SUCCESS_URL", "http://example.com/success")
        monkeypatch.setenv("BILLING_CANCEL_URL", "http://example.com/cancel")

        # Mock Stripe to raise error
        monkeypatch.setattr(stripe.checkout, "Session", MagicMock())
        stripe.checkout.Session.create.side_effect = Exception("Stripe error")

        # Create user and token
        db = TestingSessionLocal(bind=engine.connect())
        try:
            user = create_test_user(db, "test@example.com", "Password123!")
            token = get_auth_token(db, user)

            response = client.post(
                "/billing/checkout-session",
                json={},
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 502
            assert response.json()["detail"] == "stripe_api_error"
        finally:
            db.close()

    def test_checkout_uses_customer_email_and_metadata(self, setup_database, monkeypatch):
        """Verifies customer_email and metadata are passed to Stripe."""
        # Set env vars
        monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_mock")
        monkeypatch.setenv("STRIPE_PRICE_ID_BASIC", "price_123")
        monkeypatch.setenv("BILLING_SUCCESS_URL", "http://example.com/success")
        monkeypatch.setenv("BILLING_CANCEL_URL", "http://example.com/cancel")

        # Mock Stripe create to capture args
        mock_create = MagicMock()
        monkeypatch.setattr(stripe.checkout.Session, "create", mock_create)

        # Create user and token
        db = TestingSessionLocal(bind=engine.connect())
        try:
            user = create_test_user(db, "user@example.com", "Password123!")
            token = get_auth_token(db, user)

            response = client.post(
                "/billing/checkout-session",
                json={},
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200

            # Verify args passed to create
            call_args = mock_create.call_args[1]  # kwargs
            assert call_args["customer_email"] == user.email
            assert call_args["metadata"]["user_id"] == user.id
        finally:
            db.close()