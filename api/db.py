"""Database configuration and session management for FBA-Bench Enterprise.

Provides SQLAlchemy 2.0 declarative base, engine creation, session factory,
and FastAPI dependency for database sessions.
"""

import os
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager

from .models import Base


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///enterprise.db")


def get_engine() -> Engine:
    """
    Create and return a SQLAlchemy engine from DATABASE_URL.

    SQLite handling:
    - Always set check_same_thread=False for FastAPI/pytest multi-thread usage.
    - Use StaticPool for all SQLite URLs (memory and file-based) for stability on Windows/pytest.
    - Initialize pragmatic PRAGMAs on connect to reduce locking and enforce FK integrity.
    Non-SQLite: default pooling.
    """
    url = DATABASE_URL
    if url.startswith("sqlite"):
        engine = create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

        # Apply SQLite PRAGMAs at connection time to enforce constraints and improve stability.
        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_conn, _):
            cursor = dbapi_conn.cursor()
            try:
                cursor.execute("PRAGMA foreign_keys=ON;")
                cursor.execute("PRAGMA synchronous=NORMAL;")
                if ":memory:" not in url:
                    # WAL is not applicable to in-memory DBs; ignore errors if unsupported.
                    try:
                        cursor.execute("PRAGMA journal_mode=WAL;")
                    except Exception:
                        pass
            finally:
                cursor.close()

        return engine
    return create_engine(url)


engine = get_engine()

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_db() -> Session:
    """
    FastAPI dependency to yield a database session per-request.

    Important: do not dispose the engine here; only close the session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_session() -> Session:
    """
    Context-managed session helper for scripts and tests.

    Usage:
        with get_session() as session:
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


__all__ = ["engine", "SessionLocal", "Base", "get_db"]