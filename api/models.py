"""SQLAlchemy models for FBA-Bench Enterprise.

Defines the User model for persistent user storage.
"""

from sqlalchemy import String, DateTime, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from api.db import Base


class User(Base):
    """User model representing authenticated users in the system."""
    
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    # Use Python-side defaults to avoid SQLite 'now()' server-function issues during tests
    created_at: Mapped[DateTime] = mapped_column(
        DateTime, default=lambda: datetime.now(ZoneInfo("UTC")), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(ZoneInfo("UTC")),
        onupdate=lambda: datetime.now(ZoneInfo("UTC")),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    subscription_status: Mapped[str | None] = mapped_column(String(32), nullable=True)