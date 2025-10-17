"""Tests for authenticated profile retrieval and protected routes."""

import os
from datetime import datetime
from zoneinfo import ZoneInfo

# Configure test database URL before importing modules that depend on it
TEST_DB = "enterprise_test_profile.db"
os.environ["DATABASE_URL"] = f"sqlite:///./{TEST_DB}"

from pathlib import Path

import pytest
from api.db import get_db
from api.models import Base, User
from api.security.passwords import hash_password
from api.server import app
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    """Set up the test database by creating tables."""
    db_path = Path(TEST_DB)
    if db_path.exists():
        db_path.unlink()

    engine = create_engine(os.environ["DATABASE_URL"])
    Base.metadata.create_all(bind=engine)

    yield

    # Teardown: drop tables and remove DB file
    Base.metadata.drop_all(bind=engine)
    try:
        if db_path.exists():
            db_path.unlink()
    except PermissionError:
        pass  # Ignore Windows file lock


@pytest.fixture(autouse=True)
def clean_db():
    """Clean the users table before each test to ensure fresh state."""
    with get_session() as session:
        session.execute(text("DELETE FROM users"))
        session.commit()


@pytest.fixture
def client():
    return TestClient(app)


def create_test_user(email: str, password: str):
    """Helper to create a test user with hashed password."""
    hashed = hash_password(password)
    user = User(
        id="test-user-id",
        email=email,
        password_hash=hashed,
        is_active=True,
        subscription_status=None,
        created_at=datetime.now(ZoneInfo("UTC")),
        updated_at=datetime.now(ZoneInfo("UTC")),
    )
    db = next(get_db())
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    finally:
        db.close()
    return user


def test_me_requires_auth_returns_401_without_token(client):
    """Test /me requires authentication and returns 401 without token."""
    response = client.get("/me")
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Not authenticated"


def test_me_returns_200_and_user_profile_with_token(client):
    """Test /me returns 200 and user profile with valid token."""
    # Create and login test user
    create_test_user("test@example.com", "SuperSecure123!")
    login_response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "SuperSecure123!"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # Get profile with token
    response = client.get(
        "/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "test-user-id"
    assert data["email"] == "test@example.com"
    assert data["is_active"] is True
    assert data["subscription_status"] is None
    assert "created_at" in data
    assert "updated_at" in data
    assert "password_hash" not in data


def test_protected_ping_requires_auth_returns_401(client):
    """Test /protected/ping requires authentication and returns 401 without token."""
    response = client.get("/protected/ping")
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Not authenticated"


def test_protected_ping_returns_200_with_token(client):
    """Test /protected/ping returns 200 with valid token."""
    # Create and login test user
    create_test_user("test@example.com", "SuperSecure123!")
    login_response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "SuperSecure123!"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # Ping with token
    response = client.get(
        "/protected/ping",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "ok"}
