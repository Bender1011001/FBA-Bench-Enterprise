"""Database configuration and session management for FBA-Bench Enterprise.

Provides SQLAlchemy 2.0 declarative base, engine creation, session factory,
and FastAPI dependency for database sessions.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.orm import Session
from fastapi import Depends


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all models."""
    pass


def get_db_url() -> str:
    """Get DATABASE_URL from environment (loaded via dotenv)."""
    return os.getenv("DATABASE_URL", "sqlite:///./enterprise.db")


def get_engine() -> create_engine:
    """Create and return SQLAlchemy engine from DATABASE_URL."""
    url = get_db_url()
    if url.startswith("sqlite"):
        return create_engine(url, connect_args={"check_same_thread": False})
    return create_engine(url)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())


def get_db() -> Session:
    """FastAPI dependency to get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()