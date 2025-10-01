"""Tests for the Stripe Billing Portal endpoint."""

import os
from unittest.mock import MagicMock, patch
from datetime import datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from stripe.error import StripeError

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


class TestPortalSession:
    def test_portal_requires_auth(self, setup_database):
        """POST without token → 401."""
        response = client.post("/billing/portal-session")
        assert response.status_code == 401
        assert response.json()["detail"] == "Could not validate credentials"

    def test_portal_503_when_secret_missing(self, setup_database, monkeypatch):
        """Unset STRIPE_SECRET_KEY → 503."""
        # Ensure no STRIPE_SECRET_KEY
        monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)

        # Create user and token
        db = TestingSessionLocal(bind=engine.connect())
        try:
            user = create_test_user(db, "test@example.com", "Password123!")
            token = get_auth_token(db, user)

            response = client.post(
                "/billing/portal-session",
                json={},
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 503
            assert response.json()["detail"] == "Billing unavailable"
        finally:
            db.close()

    def test_portal_404_when_customer_not_found(self, setup_database, monkeypatch):
        """Mock stripe.Customer.list to return empty → 404."""
        # Set required env vars
        monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_mock")
        monkeypatch.setenv("FRONTEND_BASE_URL", "http://localhost:5173")

        # Mock stripe.Customer.list to return empty
        mock_customers = MagicMock()
        mock_customers.data = []
        monkeypatch.setattr(stripe.Customer, "list", MagicMock(return_value=mock_customers))

        # Create user and token
        db = TestingSessionLocal(bind=engine.connect())
        try:
            user = create_test_user(db, "test@example.com", "Password123!")
            token = get_auth_token(db, user)

            response = client.post(
                "/billing/portal-session",
                json={},
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 404
            assert response.json()["detail"] == "No Stripe customer found"
        finally:
            db.close()

    def test_portal_success_returns_url(self, setup_database, monkeypatch):
        """Mock list to return [{"id":"cus_test"}], Mock Session.create, Authenticated POST → 200 {"url":...}."""
        # Set required env vars
        monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_mock")
        monkeypatch.setenv("FRONTEND_BASE_URL", "http://localhost:5173")

        # Mock stripe.Customer.list to return customer
        mock_customer = MagicMock()
        mock_customer.id = "cus_test"
        mock_customers = MagicMock()
        mock_customers.data = [mock_customer]
        monkeypatch.setattr(stripe.Customer, "list", MagicMock(return_value=mock_customers))

        # Mock stripe.billing_portal.Session.create
        mock_session = MagicMock()
        mock_session.url = "https://stripe.test/portal"
        monkeypatch.setattr(stripe.billing_portal.Session, "create", MagicMock(return_value=mock_session))

        # Create user and token
        db = TestingSessionLocal(bind=engine.connect())
        try:
            user = create_test_user(db, "test@example.com", "Password123!")
            token = get_auth_token(db, user)

            response = client.post(
                "/billing/portal-session",
                json={},
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data == {"url": "https://stripe.test/portal"}

            # Assert Session.create called with customer="cus_test" and return_url "http://localhost:5173/account"
            stripe.billing_portal.Session.create.assert_called_once_with(
                customer="cus_test",
                return_url="http://localhost:5173/account"
            )
        finally:
            db.close()

    def test_portal_respects_custom_return_url(self, setup_database, monkeypatch):
        """With STRIPE_PORTAL_RETURN_URL set, assert used for return_url."""
        # Set env vars
        monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_mock")
        monkeypatch.setenv("FRONTEND_BASE_URL", "http://localhost:5173")
        monkeypatch.setenv("STRIPE_PORTAL_RETURN_URL", "https://custom.return/url")

        # Mock stripe.Customer.list to return customer
        mock_customer = MagicMock()
        mock_customer.id = "cus_test"
        mock_customers = MagicMock()
        mock_customers.data = [mock_customer]
        monkeypatch.setattr(stripe.Customer, "list", MagicMock(return_value=mock_customers))

        # Mock stripe.billing_portal.Session.create
        mock_session = MagicMock()
        mock_session.url = "https://stripe.test/portal"
        monkeypatch.setattr(stripe.billing_portal.Session, "create", MagicMock(return_value=mock_session))

        # Create user and token
        db = TestingSessionLocal(bind=engine.connect())
        try:
            user = create_test_user(db, "test@example.com", "Password123!")
            token = get_auth_token(db, user)

            response = client.post(
                "/billing/portal-session",
                json={},
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200

            # Assert used custom return_url
            stripe.billing_portal.Session.create.assert_called_once_with(
                customer="cus_test",
                return_url="https://custom.return/url"
            )
        finally:
            db.close()

    def test_portal_handles_stripe_exception(self, setup_database, monkeypatch):
        """Mock Session.create raise StripeError → 500 "Failed to create portal session"."""
        # Set required env vars
        monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_mock")
        monkeypatch.setenv("FRONTEND_BASE_URL", "http://localhost:5173")

        # Mock stripe.Customer.list to return customer
        mock_customer = MagicMock()
        mock_customer.id = "cus_test"
        mock_customers = MagicMock()
        mock_customers.data = [mock_customer]
        monkeypatch.setattr(stripe.Customer, "list", MagicMock(return_value=mock_customers))

        # Mock Session.create to raise StripeError
        monkeypatch.setattr(stripe.billing_portal.Session, "create", MagicMock(side_effect=StripeError("test stripe error")))

        # Create user and token
        db = TestingSessionLocal(bind=engine.connect())
        try:
            user = create_test_user(db, "test@example.com", "Password123!")
            token = get_auth_token(db, user)

            response = client.post(
                "/billing/portal-session",
                json={},
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 500
            assert response.json()["detail"] == "Failed to create portal session"
        finally:
            db.close()