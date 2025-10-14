"""Database configuration and session management for FBA-Bench Enterprise.

Provides SQLAlchemy 2.0 declarative base, engine creation, session factory,
and FastAPI dependency for database sessions.
"""

import os
import threading # Added for thread-safe engine caching
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.pool import StaticPool, NullPool
from typing import Dict, Optional, Iterator, Generator # Added Dict, Optional for type hinting
from contextlib import contextmanager

from .models import Base

# URL-keyed engine cache and lock for thread-safe lazy initialization
_ENGINE_CACHE: Dict[str, Engine] = {}
_ENGINE_LOCK = threading.Lock()

def get_current_db_url() -> str:
    """
    Get the current DATABASE_URL from environment or fall back to config default.
    The config default is "sqlite:///./enterprise.db".
    """
    # Use config default "sqlite:///./enterprise.db" as per instructions.
    return os.getenv("DATABASE_URL") or "sqlite:///./enterprise.db"

def _create_single_engine_instance(url: str) -> Engine:
    """
    Internal helper to create a SQLAlchemy engine instance for a given URL.
    Includes specific configurations for SQLite.
    """
    if url.startswith("sqlite"):
        # Choose pool based on SQLite target: StaticPool for in-memory, NullPool for file-based
        is_memory = (":memory:" in url) or url.endswith("?mode=memory")
        pool_cls = StaticPool if is_memory else NullPool
        engine = create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=pool_cls,
            pool_pre_ping=True,
        )

        # Apply SQLite PRAGMAs at connection time to enforce constraints and improve stability.
        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_conn, _):
            cursor = dbapi_conn.cursor()
            try:
                cursor.execute("PRAGMA foreign_keys=ON;")
                cursor.execute("PRAGMA synchronous=NORMAL;")
                if not is_memory:
                    # WAL is not applicable to in-memory DBs; ignore errors if unsupported.
                    try:
                        cursor.execute("PRAGMA journal_mode=WAL;")
                    except Exception:
                        pass
            finally:
                cursor.close()

        try:
            # Eagerly ensure schema on a live connection to stabilize early sessions
            with engine.connect() as conn:
                ensure_schema(conn)
        except Exception:
            # Avoid breaking startup/tests on transient DDL races or import timing
            pass

        return engine
    engine = create_engine(url, pool_pre_ping=True)
    try:
        # Eagerly ensure schema; tolerate unexpected failures to avoid startup breakage
        with engine.connect() as conn:
            ensure_schema(conn)
    except Exception:
        pass
    return engine

def get_engine(url: Optional[str] = None) -> Engine:
    """
    Get a SQLAlchemy engine, creating and caching it per unique URL.
    If no URL is provided, it uses the current DATABASE_URL.
    """
    resolved_url = url or get_current_db_url()
    with _ENGINE_LOCK:
        if resolved_url in _ENGINE_CACHE:
            return _ENGINE_CACHE[resolved_url]
        
        # Create a new engine instance if not found in cache
        engine_instance = _create_single_engine_instance(resolved_url)
        _ENGINE_CACHE[resolved_url] = engine_instance
        return engine_instance

# Global engine for backward compatibility. Initialized with the default URL at import time.
# Note: Canonical access for URL-aware sessions is via get_db() or get_session().
engine = get_engine() # This now uses the cached get_engine and thus the default URL

# Global SessionLocal using scoped_session for backward compatibility.
# It is bound to the initial engine created at import time.
# Note: Canonical access for URL-aware sessions is via get_db() or get_session().
SessionLocal = scoped_session(sessionmaker(
    bind=engine, # Binds to the *initial* engine as defined above
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
))


def get_session_maker(url: Optional[str] = None) -> sessionmaker[Session]:
    """
    Create a SQLAlchemy sessionmaker bound to an engine for the specified URL.
    If no URL is provided, uses the current DATABASE_URL.
    """
    engine = get_engine(url)
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency to yield a database session per-request, bound to the current URL.
    
    Important: do not dispose the engine here; only close the session.
    The global SessionLocal is for backward compatibility; canonical access uses this function.
    """
    current_url = get_current_db_url()
    # Use a temporary sessionmaker bound to the current URL.
    session_factory = get_session_maker(current_url)
    db = session_factory()
    try:
        ensure_schema(db)
        yield db
    finally:
        db.close() # Close the specific session instance used in this request


@contextmanager
def get_session() -> Iterator[Session]:
    """
    Context manager for tests: allows `with get_session() as session:`.
    Creates an independent session bound to the current URL and ensures close on exit.
    The global SessionLocal is for backward compatibility; canonical access uses this function.
    """
    current_url = get_current_db_url()
    # Use a temporary sessionmaker bound to the current URL.
    session_factory = get_session_maker(current_url)
    session = session_factory()
    try:
        ensure_schema(session)
        yield session
    finally:
        session.close()


def ensure_schema(db_or_bind=None) -> None:
    """
    Ensure all SQLAlchemy tables are created for the provided session bind/engine.

    Idempotent and safe to call frequently. For tests that override get_db and/or
    create separate Engines/Connections, this ensures the 'users' table (and others)
    exists on the exact connection/engine being used by the current Session.
    """
    # Ensure models are imported to register all Table objects on Base.metadata
    from api import models  # ensures Base metadata is populated

    # Import locally to avoid cycles
    from sqlalchemy.orm import Session as SASession  # type: ignore

    # Resolve declared tables after model import; if none, nothing to create
    tables = list(models.Base.metadata.sorted_tables)
    if not tables:
        return

    # Resolve binds
    if isinstance(db_or_bind, SASession):
        try:
            bind = db_or_bind.get_bind() or db_or_bind.bind  # type: ignore[attr-defined]
        except Exception:
            bind = getattr(db_or_bind, "bind", None)
    else:
        bind = db_or_bind or engine

    # Determine the owning Engine and live Connection (if any)
    live_conn = None
    engine_owner = None
    if bind is None:
        engine_owner = engine
    else:
        if hasattr(bind, "engine"):
            # A live Connection provides an owning Engine
            engine_owner = bind.engine
            live_conn = bind
        else:
            # An Engine (or Engine-like) bind
            engine_owner = bind

    # Safety fallback
    engine_owner = engine_owner or engine

    # Inspect current engine to determine if any tables are missing
    insp = inspect(engine_owner)
    try:
        existing = set(insp.get_table_names())
    except Exception:
        existing = set()

    missing = any(t.name not in existing for t in tables)
    if missing:
        # Apply DDL to the engine owner first
        models.Base.metadata.create_all(bind=engine_owner)

        # For SQLite, also ensure visibility on the active live connection if distinct
        try:
            backend_name = engine_owner.url.get_backend_name()  # type: ignore[attr-defined]
        except Exception:
            backend_name = getattr(getattr(engine_owner, "dialect", None), "name", None)
        if backend_name == "sqlite" and live_conn is not None and live_conn is not engine_owner:
            try:
                models.Base.metadata.create_all(bind=live_conn)
            except Exception:
                # Non-fatal; engine-level DDL already applied
                pass

    # Enable foreign keys on live SQLite connections to align with tests
    try:
        backend_fk = engine_owner.url.get_backend_name()  # type: ignore[attr-defined]
    except Exception:
        backend_fk = getattr(getattr(engine_owner, "dialect", None), "name", None)
    if backend_fk == "sqlite" and live_conn is not None:
        try:
            live_conn.execute(text("PRAGMA foreign_keys=ON"))
        except Exception:
            # Best-effort; ignore pragma errors
            pass


__all__ = ["engine", "SessionLocal", "Base", "get_session_maker", "get_db", "get_session", "ensure_schema"]