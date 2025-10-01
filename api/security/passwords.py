"""Password hashing utility using Argon2id for FBA-Bench Enterprise.

Provides secure password hashing and verification with configurable parameters
from environment variables.
"""

import os
from typing import Dict

from dotenv import load_dotenv
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError


# Load environment variables early
load_dotenv()


def get_argon2_params() -> Dict[str, int]:
    """Retrieve Argon2id parameters from environment with safe defaults."""
    return {
        "time_cost": int(os.getenv("ARGON2_TIME_COST", "3")),
        "memory_cost": int(os.getenv("ARGON2_MEMORY_COST", "65536")),
        "parallelism": int(os.getenv("ARGON2_PARALLELISM", "2")),
        "hash_len": int(os.getenv("ARGON2_HASH_LEN", "32")),
        "salt_len": int(os.getenv("ARGON2_SALT_LEN", "16")),
    }


# Initialize the PasswordHasher with current parameters
_password_hasher = PasswordHasher(**get_argon2_params())


def hash_password(plain: str) -> str:
    """Hash a plain password using Argon2id."""
    return _password_hasher.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain password against a hashed password using Argon2id."""
    try:
        _password_hasher.verify(hashed, plain)
        return True
    except VerifyMismatchError:
        return False