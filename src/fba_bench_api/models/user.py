"""User model for authentication and authorization."""

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.sql import func

from fba_bench_api.models.base import Base


class User(Base):
    """User model for authentication and user management."""

    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    subscription_status = Column(String, nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Profile fields
    full_name = Column(String, nullable=True)
    profile_data = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<User(id='{self.id}', email='{self.email}')>"
