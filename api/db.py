"""Database configuration and session management for FBA-Bench Enterprise.

Provides SQLAlchemy 2.0 declarative base, engine creation, session factory,
and FastAPI dependency for database sessions.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool
from fastapi import Depends
from contextlib import contextmanager


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all models."""
    pass

engine = get_engine()
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db_url() -> str:
    """Get DATABASE_URL from environment (loaded via dotenv)."""
    return os.getenv("DATABASE_URL", "sqlite:///./enterprise.db")


def get_engine() -> create_engine:
    """Create and return SQLAlchemy engine from DATABASE_URL.

    For SQLite, use NullPool to avoid lingering file locks (important on Windows for test teardown).
    """
    url = get_db_url()
    if url.startswith("sqlite"):
        return create_engine(url, connect_args={"check_same_thread": False}, poolclass=NullPool)
    return create_engine(url)


def get_db() -> Session:
    """FastAPI dependency to get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_session() -> Session:
    """Context-managed session helper for tests and scripts.

    Usage:
        with get_session() as session:
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

__all__ = ["SessionLocal", "engine", "Base", "get_db"]