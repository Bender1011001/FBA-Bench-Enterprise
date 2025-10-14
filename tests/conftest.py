import os
import pytest
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from sqlalchemy import text

# Shared test DB file
TEST_DB = "test_shared.db"
db_path = Path(TEST_DB)
if db_path.exists():
    db_path.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///./{TEST_DB}"

from api.dependencies import Base, engine, get_db as app_get_db
from api.models import User
from api.security.passwords import hash_password
from fastapi.testclient import TestClient
from api.server import app

def override_get_db():
    yield from app_get_db()

app.dependency_overrides[app_get_db] = override_get_db

@pytest.fixture(scope="session", autouse=True)
def setup_shared_db():
    """Create tables once for all tests."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if db_path.exists():
        try:
            db_path.unlink()
        except PermissionError:
            pass  # Windows lock

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create all tables once for the test session"""
    Base.metadata.create_all(bind=engine)
    yield
    # Optional teardown (keep minimal risk): drop tables after session
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
@pytest.fixture(scope="function")
def db_session():
    gen = app_get_db()
    db = next(gen)
    try:
        yield db
    finally:
        try:
            next(gen)
        except StopIteration:
            pass


@pytest.fixture(autouse=True)
def clean_db(db_session):
    """Clean users table before each test."""
    try:
        db_session.execute(text("DELETE FROM users"))
        db_session.commit()
    except Exception:
        pass  # Table may not exist

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        id="test-uuid-123",
        email="test@example.com",
        password_hash=hash_password("Password123!"),
        is_active=True,
        subscription_status=None,
        created_at=datetime.now(ZoneInfo("UTC")),
        updated_at=datetime.now(ZoneInfo("UTC")),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def auth_token(test_user):
    from api.security.jwt import create_access_token
    claims = {"sub": test_user.id, "email": test_user.email}
    return create_access_token(claims)