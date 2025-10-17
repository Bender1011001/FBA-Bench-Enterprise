"""Tests for the auth login endpoint and JWT dependency."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from api.db import Base, get_db
from api.models import User
from api.security.jwt import decode_token
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


class TestLoginEndpoint:
    def test_login_success_returns_access_token_and_claims(self, setup_database):
        """Successful login returns access token with correct claims."""
        db = TestingSessionLocal(bind=engine.connect())
        try:
            user = create_test_user(db, "test@example.com", "Password123!")

            response = client.post(
                "/auth/login",
                json={"email": "test@example.com", "password": "Password123!"},
            )

            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"
            assert "expires_in" in data
            assert data["expires_in"] == 900  # 15 minutes

            # Verify access token payload
            payload = decode_token(data["access_token"])
            assert payload["sub"] == user.id
            assert payload["email"] == user.email
            assert payload["token_type"] == "access"
            assert payload["iss"] == "fba-bench-enterprise"

            # Check expiration is within expected range
            exp = payload["exp"]
            now = datetime.now(timezone.utc).timestamp()
            assert 899 <= exp - now <= 901  # Around 15 minutes from now
        finally:
            db.close()

    def test_login_invalid_email_returns_401(self, setup_database):
        """Invalid email returns 401."""
        db = TestingSessionLocal(bind=engine.connect())
        try:
            create_test_user(db, "valid@example.com", "Password123!")

            response = client.post(
                "/auth/login",
                json={"email": "invalid@example.com", "password": "Password123!"},
            )

            assert response.status_code == 401
            assert response.json()["detail"] == "Invalid credentials"
        finally:
            db.close()

    def test_login_wrong_password_returns_401(self, setup_database):
        """Wrong password returns 401."""
        db = TestingSessionLocal(bind=engine.connect())
        try:
            create_test_user(db, "test@example.com", "Password123!")

            response = client.post(
                "/auth/login",
                json={"email": "test@example.com", "password": "wrongpass"},
            )

            assert response.status_code == 401
            assert response.json()["detail"] == "Invalid credentials"
        finally:
            db.close()

    def test_login_inactive_user_returns_403(self, setup_database):
        """Inactive user returns 403."""
        db = TestingSessionLocal(bind=engine.connect())
        try:
            create_test_user(db, "inactive@example.com", "Password123!", active=False)

            response = client.post(
                "/auth/login",
                json={"email": "inactive@example.com", "password": "Password123!"},
            )

            assert response.status_code == 401
            assert response.json()["detail"] == "Inactive account"
        finally:
            db.close()


class TestJWTDependency:
    def test_get_current_user_dependency_rejects_invalid_token(
        self, client, test_user, auth_token
    ):
        """Dependency rejects requests without or with invalid token."""
        # No token
        response = client.get("/protected/test")
        assert response.status_code == 401
        assert response.json()["detail"] == "Could not validate credentials"

        # Invalid token (malformed)
        response = client.get(
            "/protected/test",
            headers={"Authorization": "Bearer invalidtoken"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Could not validate credentials"

        # Valid token
        response = client.get(
            "/protected/test",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        assert response.json()["user_id"] == test_user.id
        assert response.json()["email"] == test_user.email
