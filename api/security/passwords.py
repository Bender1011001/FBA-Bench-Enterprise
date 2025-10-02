"""Password hashing utility using Argon2id for FBA-Bench Enterprise."""

from argon2 import PasswordHasher, exceptions
from argon2.low_level import Type

from api.config import (
    ARGON2_TIME_COST,
    ARGON2_MEMORY_COST,
    ARGON2_PARALLELISM,
)

# Single hasher instance configured for Argon2id with import-safe defaults
_password_hasher = PasswordHasher(
    time_cost=ARGON2_TIME_COST,
    memory_cost=ARGON2_MEMORY_COST,
    parallelism=ARGON2_PARALLELISM,
    hash_len=32,
    type=Type.ID,
)


def hash_password(plain: str) -> str:
    """Hash a plaintext password using Argon2id."""
    return _password_hasher.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a hashed password using Argon2id."""
    try:
        _password_hasher.verify(hashed, plain)
        return True
    except exceptions.VerifyMismatchError:
        return False