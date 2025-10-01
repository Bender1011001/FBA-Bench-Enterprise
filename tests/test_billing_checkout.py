"""Unit tests for the billing checkout session endpoint."""

import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.models import User
from api.security.jwt import get_current_user
from api.server import app  # Import the main app for testing


@pytest.fixture
def client() -> TestClient:
    """Provide a TestClient for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Mock user for authentication."""
    user = User(id=1, email="test@example.com")
    return user


@pytest.fixture
def mock_get_current_user(monkeypatch: pytest.MonkeyPatch, mock_user: User):
    """Mock get_current_user to return a user."""
    def mock_dependency():
        return mock_user
    monkeypatch.setattr("api.routers.billing.get_current_user", mock_dependency)


@pytest.fixture
def mock_stripe_success(monkeypatch: pytest.MonkeyPatch):
    """Mock Stripe Session.create to return a successful session."""
    mock_session = MagicMock()
    mock_session.url = "https://stripe.test/session"
    monkeypatch.setattr("stripe.checkout.Session.create", MagicMock(return_value=mock_session))
    return mock_session


def test_checkout_requires_auth(client: TestClient):
    """POST without token returns 401."""
    response = client.post("/billing/checkout-session", json={})
    assert response.status_code == 401


def test_checkout_success_returns_url(
    client: TestClient,
    mock_get_current_user,
    mock_stripe_success,
    monkeypatch: pytest.MonkeyPatch,
):
    """Test successful checkout with defaults."""
    # Seed env
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_xxx")
    monkeypatch.setenv("STRIPE_PRICE_ID_DEFAULT", "price_default")
    monkeypatch.setenv("FRONTEND_BASE_URL", "http://localhost:5173")

    response = client.post(
        "/billing/checkout-session",
        json={},
        headers={"Authorization": "Bearer fake_token"}  # Mocked by fixture
    )

    assert response.status_code == 200
    data = response.json()
    assert data == {"url": "https://stripe.test/session"}

    # Assert Stripe call params
    stripe_create = mock_stripe_success.call_args[1]
    assert stripe_create["mode"] == "subscription"
    line_item = stripe_create["line_items"][0]
    assert line_item["price"] == "price_default"
    assert line_item["quantity"] == 1
    assert stripe_create["success_url"] == "http://localhost:5173/billing/success"
    assert stripe_create["cancel_url"] == "http://localhost:5173/billing/cancel"
    assert stripe_create["customer_email"] == "test@example.com"


def test_checkout_custom_body_overrides_defaults(
    client: TestClient,
    mock_get_current_user,
    mock_stripe_success,
    monkeypatch: pytest.MonkeyPatch,
):
    """Test custom price_id, quantity, success_url, cancel_url."""
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_xxx")
    monkeypatch.setenv("STRIPE_PRICE_ID_DEFAULT", "price_default")
    monkeypatch.setenv("FRONTEND_BASE_URL", "http://localhost:5173")

    response = client.post(
        "/billing/checkout-session",
        json={
            "price_id": "price_custom",
            "quantity": 3,
            "success_url": "http://custom/success",
            "cancel_url": "http://custom/cancel",
        },
        headers={"Authorization": "Bearer fake_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data == {"url": "https://stripe.test/session"}

    # Assert overrides
    stripe_create = mock_stripe_success.call_args[1]
    line_item = stripe_create["line_items"][0]
    assert line_item["price"] == "price_custom"
    assert line_item["quantity"] == 3
    assert stripe_create["success_url"] == "http://custom/success"
    assert stripe_create["cancel_url"] == "http://custom/cancel"


def test_checkout_400_when_no_price_configured(
    client: TestClient,
    mock_get_current_user,
    monkeypatch: pytest.MonkeyPatch,
):
    """Unset both STRIPE_PRICE_ID_DEFAULT and body.price_id; expect 400."""
    monkeypatch.delenv("STRIPE_PRICE_ID_DEFAULT", raising=False)
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_xxx")

    response = client.post(
        "/billing/checkout-session",
        json={},
        headers={"Authorization": "Bearer fake_token"}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Missing price_id and no default configured"


def test_checkout_503_when_secret_missing(
    client: TestClient,
    mock_get_current_user,
    monkeypatch: pytest.MonkeyPatch,
):
    """Unset STRIPE_SECRET_KEY; expect 503."""
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    monkeypatch.setenv("STRIPE_PRICE_ID_DEFAULT", "price_default")

    response = client.post(
        "/billing/checkout-session",
        json={},
        headers={"Authorization": "Bearer fake_token"}
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Billing unavailable"


def test_checkout_handles_stripe_exception(
    client: TestClient,
    mock_get_current_user,
    monkeypatch: pytest.MonkeyPatch,
):
    """Mock stripe.checkout.Session.create to raise stripe.error.StripeError; expect 500."""
    from stripe.error import StripeError

    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_xxx")
    monkeypatch.setenv("STRIPE_PRICE_ID_DEFAULT", "price_default")
    monkeypatch.setenv("FRONTEND_BASE_URL", "http://localhost:5173")
    with patch("stripe.checkout.Session.create") as mock_create:
        mock_create.side_effect = StripeError("Stripe error")
        response = client.post(
            "/billing/checkout-session",
            json={},
            headers={"Authorization": "Bearer fake_token"}
        )

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to create checkout session"