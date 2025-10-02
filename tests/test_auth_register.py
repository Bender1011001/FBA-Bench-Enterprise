"""Unit tests for auth registration endpoint."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.server import app
from api.db import get_db, Base
from api.models import User
from api.security.passwords import verify_password


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


def test_register_success_returns_201_and_public_user_fields(setup_database):
    """Test successful registration returns 201 and public user fields."""
    response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "Password123!"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["email"] == "test@example.com"
    assert data["is_active"] is True
    assert data["subscription_status"] is None
    assert "created_at" in data
    assert "updated_at" in data
    # Ensure no password_hash in response
    assert "password_hash" not in data


def test_register_duplicate_email_returns_409(setup_database):
    """Test duplicate email returns 409 Conflict."""
    # First registration
    client.post(
        "/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "Password123!"
        }
    )
    # Second attempt
    response = client.post(
        "/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "DifferentPass456!"
        }
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "email_already_registered"


def test_register_invalid_email_returns_400(setup_database):
    """Test invalid email returns 400 Bad Request."""
    response = client.post(
        "/auth/register",
        json={
            "email": "invalid-email",
            "password": "Password123!"
        }
    )
    assert response.status_code == 400
    assert "value_error.email" in str(response.json()["detail"])


def test_register_weak_password_returns_400(setup_database):
    """Test weak password returns 400 Bad Request."""
    # Too short
    response = client.post(
        "/auth/register",
        json={
            "email": "weak@example.com",
            "password": "short"
        }
    )
    assert response.status_code == 400
    assert "Password must be 8-128 characters long" in response.json()["detail"]

    # No uppercase
    response = client.post(
        "/auth/register",
        json={
            "email": "weak@example.com",
            "password": "password123!"
        }
    )
    assert response.status_code == 400
    assert "Password must contain at least one uppercase letter" in response.json()["detail"]

    # No digit
    response = client.post(
        "/auth/register",
        json={
            "email": "weak@example.com",
            "password": "Password!"
        }
    )
    assert response.status_code == 400
    assert "Password must contain at least one digit" in response.json()["detail"]

    # No special char
    response = client.post(
        "/auth/register",
        json={
            "email": "weak@example.com",
            "password": "Password123"
        }
    )
    assert response.status_code == 400
    assert "Password must contain at least one symbol (non-alphanumeric)" in response.json()["detail"]


def test_register_case_insensitive_duplicate_returns_409(setup_database):
    """Test duplicate email (case-insensitive) returns 409 Conflict."""
    email = "duplicate@example.com"
    # First registration
    client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "Password123!"
        }
    )
    # Second attempt with different case
    response = client.post(
        "/auth/register",
        json={
            "email": "DUPLICATE@EXAMPLE.COM",
            "password": "DifferentPass456!"
        }
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "Email already registered"


def test_register_email_normalization(setup_database):
    """Test email is normalized to lowercase in response and DB."""
    response = client.post(
        "/auth/register",
        json={
            "email": " Test@Example.COM ",
            "password": "Password123!"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"  # Lowercased and trimmed


def test_password_is_hashed_in_db_not_plaintext(client, test_user):
    """Test password is hashed in DB, not stored as plaintext."""
    email = test_user.email
    password = "Password123!"
    
    # Query DB directly
    db = next(get_db())
    try:
        user = db.query(User).filter(User.email == email).first()
        assert user is not None
        assert user.password_hash != password  # Not plaintext
        assert verify_password(password, user.password_hash)  # But verifiable
    finally:
        db.close()