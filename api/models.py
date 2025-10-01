"""SQLAlchemy models for FBA-Bench Enterprise.

Defines the User model for persistent user storage.
"""

from sqlalchemy import String, DateTime, Boolean, func, Index
from sqlalchemy.orm import Mapped, mapped_column

from api.db import Base


class User(Base):
    """User model representing authenticated users in the system."""
    
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    subscription_status: Mapped[str | None] = mapped_column(String(32), nullable=True)