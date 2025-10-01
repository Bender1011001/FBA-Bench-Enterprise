"""FBA-Bench Enterprise FastAPI Application.

Wiring for startup, database initialization, and auth endpoints.
"""

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from sqlalchemy import text

from api.db import get_engine
from api.models import User  # Import to register model with Base.metadata
from api.routers import auth, billing


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager for app startup and shutdown."""
    # Startup
    load_dotenv()  # Load environment variables from .env
    engine = get_engine()
    
    # Verify database connectivity
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    
    yield
    
    # Shutdown (optional: close engine if needed, but SQLAlchemy handles it)


app = FastAPI(
    title="FBA-Bench Enterprise API",
    description="API for FBA-Bench Enterprise features including authentication.",
    version="0.1.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(auth.router)
app.include_router(billing.router)