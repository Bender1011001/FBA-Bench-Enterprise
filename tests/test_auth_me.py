"""Tests for the /auth/me protected profile endpoint."""

import atexit
import os
import tempfile
from datetime import datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set required env vars for tests before importing modules that load them
os.environ["JWT_SECRET"] = "test-jwt-secret-key"

# Create temporary SQLite file DB for shared state across connections
test_db_fd, test_db_filename = tempfile.mkstemp(suffix=".db")
atexit.register(os.unlink, test_db_filename)
os.environ["DATABASE_URL"] = f"sqlite:///{test_db_filename}"

from api.db import Base, get_db
from api.models import User
from api.security.passwords import hash_password
from api.server import app

SQLALCHEMY_DATABASE_URL = os.environ["DATABASE_URL"]

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


class TestProfileEndpoint:
    def test_me_unauthorized_without_token_returns_401(self, setup_database):
        """Call GET /auth/me without Authorization header; expect 401."""
        response = client.get("/auth/me")
        assert response.status_code == 401
        assert response.json()["detail"] == "invalid_or_expired_token"
        assert "WWW-Authenticate" in response.headers
        assert response.headers["WWW-Authenticate"] == "Bearer"

    def test_me_unauthorized_with_invalid_token_returns_401(self, setup_database):
        """Call GET /auth/me with an invalid/malformed Authorization token; expect 401."""
        response = client.get(
            "/auth/me", headers={"Authorization": "Bearer invalidtoken"}
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "invalid_or_expired_token"
        assert "WWW-Authenticate" in response.headers
        assert response.headers["WWW-Authenticate"] == "Bearer"

    def test_me_with_valid_token_returns_profile_200(
        self, client, test_user, auth_token
    ):
        """Register a user, login to get token, call GET /auth/me; expect 200 with public fields."""
        # Call /auth/me with token
        response = client.get(
            "/auth/me", headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()

        # Check public fields present
        assert "id" in data
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email
        assert "created_at" in data
        assert "updated_at" in data
        assert data["is_active"] is True
        assert data["subscription_status"] is None

        # Confirm password_hash is not present
        assert "password_hash" not in data

    def test_me_with_inactive_user_returns_401(self, client, test_user, auth_token):
        """Create active user, login to get token, deactivate user, call GET /auth/me; expect 401."""
        # Deactivate the user
        db = next(get_db())
        try:
            inactive_user = db.query(User).filter(User.id == test_user.id).first()
            inactive_user.is_active = False
            inactive_user.updated_at = datetime.now(ZoneInfo("UTC"))
            db.commit()

            # Call /auth/me with token; should fail due to inactive
            response = client.get(
                "/auth/me", headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert response.status_code == 401
            assert response.json()["detail"] == "Could not validate credentials"
            assert "WWW-Authenticate" in response.headers
            assert response.headers["WWW-Authenticate"] == "Bearer"
        finally:
            db.close()
