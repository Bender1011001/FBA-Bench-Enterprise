from __future__ import annotations

import os
from typing import Optional


def _parse_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "t", "yes", "y", "on")


# Database
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./enterprise.db")
APPLY_DB_MIGRATIONS_ON_STARTUP: bool = _parse_bool(
    os.getenv("APPLY_DB_MIGRATIONS_ON_STARTUP", "false"), default=False
)

# JWT
JWT_SECRET: str = os.getenv("JWT_SECRET", "test-secret-key")
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRES_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRES_MINUTES", "15"))

# Argon2id password hashing
ARGON2_TIME_COST: int = int(os.getenv("ARGON2_TIME_COST", "2"))
ARGON2_MEMORY_COST: int = int(os.getenv("ARGON2_MEMORY_COST", "102400"))
ARGON2_PARALLELISM: int = int(os.getenv("ARGON2_PARALLELISM", "8"))

# Stripe/Billing
STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PORTAL_RETURN_URL: str = os.getenv("STRIPE_PORTAL_RETURN_URL", "")
FRONTEND_BASE_URL: str = os.getenv("FRONTEND_BASE_URL", "http://localhost:5173")
STRIPE_PRICE_ID_DEFAULT: str = os.getenv("STRIPE_PRICE_ID_DEFAULT", "")
STRIPE_PRICE_ID_BASIC: str = os.getenv("STRIPE_PRICE_ID_BASIC", "")