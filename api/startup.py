"""Startup utilities for the FBA-Bench Enterprise API.

Provides helpers for database migrations and other initialization tasks.
"""

import os
from pathlib import Path

from alembic import command
from alembic.config import Config

from .config import APPLY_DB_MIGRATIONS_ON_STARTUP, DATABASE_URL
from api.dependencies import Base, engine
import api.models  # noqa: F401

__all__ = ["init_db"]

def init_db() -> None:
    """Initialize database tables in an idempotent way.

    Ensures SQLAlchemy models are imported so their metadata is registered,
    then creates all tables if they do not already exist.
    Safe to call multiple times.
    """
    # Models import is at module level to register metadata; no action needed here.

    Base.metadata.create_all(bind=engine)

def run_db_migrations_if_configured() -> None:
    """Run database migrations if configured to do so.

    This is intended to be called during application startup (e.g., in a server entrypoint).
    """
    if not APPLY_DB_MIGRATIONS_ON_STARTUP:
        print("DB migrations skipped (APPLY_DB_MIGRATIONS_ON_STARTUP=false)")
        return

    # Locate alembic.ini relative to this file
    alembic_ini_path = Path(__file__).parent.parent / "alembic.ini"
    if not alembic_ini_path.exists():
        raise FileNotFoundError(f"Alembic config not found at {alembic_ini_path}")

    alembic_cfg = Config(str(alembic_ini_path))
    alembic_cfg.set_main_option("sqlalchemy.url", DATABASE_URL)

    print("Applying DB migrations...")
    command.upgrade(alembic_cfg, "head")
    print("DB migrations applied successfully.")
    