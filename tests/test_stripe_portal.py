"""Tests for the Stripe Billing Portal Session endpoint."""

import os
import pytest
from unittest.mock import MagicMock, patch
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


class TestPortalSession:
    def test_portal_requires_auth_returns_401(self, setup_database):
        """Unauthenticated request returns 401."""
        response = client.post("/billing/portal-session")
        assert response.status_code == 401
        assert response.json()["detail"] == "invalid_or_expired_token"

    def test_portal_503_when_stripe_secret_missing(self, setup_database, monkeypatch):
        """Returns 503 when STRIPE_SECRET_KEY missing."""
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
            assert response.json()["detail"] == "stripe_not_configured"
        finally:
            db.close()

    def test_portal_500_when_return_url_missing(self, setup_database, monkeypatch):
        """Returns 500 when no return_url and no env default."""
        # Set STRIPE_SECRET_KEY but no BILLING_PORTAL_RETURN_URL
        monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_mock")
        monkeypatch.delenv("BILLING_PORTAL_RETURN_URL", raising=False)

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
            assert response.json()["detail"] == "billing_url_not_configured"
        finally:
            db.close()

    def test_portal_creates_session_with_existing_customer_email(self, setup_database, monkeypatch):
        """Successful portal with existing customer via search returns 200 with URL."""
        # Set env vars
        monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_mock")
        monkeypatch.setenv("BILLING_PORTAL_RETURN_URL", "http://example.com/return")

        # Mock search to return existing customer
        mock_customer = MagicMock()
        mock_customer.id = "cus_mock_existing"
        mock_customers = MagicMock()
        mock_customers.data = [mock_customer]
        monkeypatch.setattr(stripe.Customer, "search", MagicMock(return_value=mock_customers))

        # Mock session create
        mock_session = MagicMock()
        mock_session.url = "https://billing.stripe.com/session/mock"
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
            assert "url" in data
            assert data["url"] == mock_session.url

            # Ensure search called with user email
            stripe.Customer.search.assert_called_once_with(query='email:"test@example.com"')
        finally:
            db.close()

    def test_portal_creates_customer_if_not_exists_then_session(self, setup_database, monkeypatch):
        """Creates customer if none exists, then session; verifies metadata."""
        # Set env vars
        monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_mock")
        monkeypatch.setenv("BILLING_PORTAL_RETURN_URL", "http://example.com/return")

        # Mock search to return empty
        mock_empty_customers = MagicMock()
        mock_empty_customers.data = []
        monkeypatch.setattr(stripe.Customer, "search", MagicMock(return_value=mock_empty_customers))

        # Mock create customer
        mock_customer = MagicMock()
        mock_customer.id = "cus_new_mock"
        monkeypatch.setattr(stripe.Customer, "create", MagicMock(return_value=mock_customer))

        # Mock session create
        mock_session = MagicMock()
        mock_session.url = "https://billing.stripe.com/session/mock"
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
            assert "url" in data
            assert data["url"] == mock_session.url

            # Ensure search called (empty result)
            stripe.Customer.search.assert_called_once_with(query='email:"test@example.com"')

            # Ensure create called with email and metadata
            create_call_args = stripe.Customer.create.call_args[1]
            assert create_call_args["email"] == user.email
            assert create_call_args["metadata"]["user_id"] == str(user.id)

            # Ensure session created with customer.id
            stripe.billing_portal.Session.create.assert_called_once_with(
                customer=mock_customer.id,
                return_url="http://example.com/return"
            )
        finally:
            db.close()

    def test_portal_502_on_stripe_error(self, setup_database, monkeypatch):
        """Stripe API error returns 502."""
        # Set env vars
        monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_mock")
        monkeypatch.setenv("BILLING_PORTAL_RETURN_URL", "http://example.com/return")

        # Mock to raise on customer search (simulate API error)
        monkeypatch.setattr(stripe.Customer, "search", MagicMock(side_effect=Exception("Stripe search error")))

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

            assert response.status_code == 502
            assert response.json()["detail"] == "stripe_api_error"
        finally:
            db.close()