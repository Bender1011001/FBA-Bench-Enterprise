"""Security utilities for password hashing using Argon2id.

Provides secure password hashing and verification with configurable parameters.
"""

from argon2 import PasswordHasher, exceptions
from argon2.low_level import Type

from .config import ARGON2_TIME_COST, ARGON2_MEMORY_COST, ARGON2_PARALLELISM


def hash_password(plain: str) -> str:
    """Hash a plaintext password using Argon2id with configurable parameters."""
    ph = PasswordHasher(
        time_cost=ARGON2_TIME_COST,
        memory_cost=ARGON2_MEMORY_COST,
        parallelism=ARGON2_PARALLELISM,
        hash_len=32,
        type=Type.ID,
    )
    return ph.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a hashed password."""
    ph = PasswordHasher(
        time_cost=ARGON2_TIME_COST,
        memory_cost=ARGON2_MEMORY_COST,
        parallelism=ARGON2_PARALLELISM,
        hash_len=32,
        type=Type.ID,
    )
    try:
        ph.verify(hashed, plain)
        return True
    except exceptions.VerifyMismatchError:
        return False