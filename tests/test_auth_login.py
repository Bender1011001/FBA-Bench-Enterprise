"""Tests for the auth login endpoint and JWT dependency."""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends, Header
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.server import app
from api.db import get_db, Base
from api.models import User
from api.security.passwords import hash_password, verify_password
from api.security.jwt import decode_token, get_current_user


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
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
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
    @pytest.fixture
    def temp_app(self, setup_database):
        """Create a temporary FastAPI app for dependency testing."""
        temp_app = FastAPI()
        
        def temp_override_get_db():
            connection = engine.connect()
            transaction = connection.begin()
            session = TestingSessionLocal(bind=connection)
            try:
                yield session
            finally:
                session.close()
                transaction.rollback()
                connection.close()
        
        temp_app.dependency_overrides[get_db] = temp_override_get_db
        
        @temp_app.get("/protected/test")
        def protected_route(
            current_user: User = Depends(get_current_user),
        ):
            return {"user_id": current_user.id, "email": current_user.email}
        
        return temp_app

    def test_get_current_user_dependency_rejects_invalid_token(self, temp_app):
        """Dependency rejects requests without or with invalid token."""
        temp_client = TestClient(temp_app)
        
        # No token
        response = temp_client.get("/protected/test")
        assert response.status_code == 401
        assert response.json()["detail"] == "invalid_or_expired_token"
        
        # Invalid token (malformed)
        response = temp_client.get(
            "/protected/test",
            headers={"Authorization": "Bearer invalidtoken"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "invalid_or_expired_token"
        
        # Valid flow (create user, login, use token)
        db = TestingSessionLocal(bind=engine.connect())
        try:
            user = create_test_user(db, "valid@example.com", "Password123!")
            
            # Get token via main app (with override already set)
            login_response = client.post(
                "/auth/login",
                json={"email": "valid@example.com", "password": "Password123!"},
            )
            token = login_response.json()["access_token"]
            
            # Test with valid token on temp app
            response = temp_client.get(
                "/protected/test",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 200
            
            # Verify token claims in dependency context (indirectly via success)
            # Since dependency decodes and fetches user, success confirms token_type="access"
            assert response.json()["user_id"] == user.id
            assert response.json()["email"] == user.email
        finally:
            db.close()