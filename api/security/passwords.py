"""Password hashing and verification utilities.

- New hashes use Argon2id.
- Verification supports multi-scheme:
  * "$argon2" → Argon2id (primary)
  * "$2a", "$2b", "$2y" → bcrypt (fallback if installed)
  * otherwise → False
"""

import logging

from argon2 import PasswordHasher, exceptions
from argon2.low_level import Type

# Optional bcrypt import; verification will gracefully degrade if unavailable
try:
    import bcrypt  # type: ignore
except ImportError:  # pragma: no cover - environment dependent
    bcrypt = None  # type: ignore[assignment]

from api.config import (
    ARGON2_TIME_COST,
    ARGON2_MEMORY_COST,
    ARGON2_PARALLELISM,
)

logger = logging.getLogger(__name__)

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


def _is_bcrypt_hash(h: str) -> bool:
    # Common bcrypt prefixes
    return h.startswith("$2a") or h.startswith("$2b") or h.startswith("$2y")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a hashed password with multi-scheme support.

    Order:
      1) Argon2 if hash starts with "$argon2"
      2) bcrypt if hash starts with "$2a", "$2b", "$2y" (fallback, optional)
      3) Unknown scheme → False
    """
    if not isinstance(plain, str) or not isinstance(hashed, str) or not hashed:
        return False

    # Argon2 primary path
    if hashed.startswith("$argon2"):
        try:
            _password_hasher.verify(hashed, plain)
            return True
        except exceptions.VerifyMismatchError:
            return False
        except exceptions.InvalidHash:
            # Invalid Argon2 hash format
            logger.debug("Invalid Argon2 hash format encountered during verification.")
            return False
        except Exception:
            # Do not leak details; keep behavior safe-by-default
            logger.debug("Unexpected error during Argon2 verification.", exc_info=True)
            return False

    # bcrypt fallback path
    if _is_bcrypt_hash(hashed):
        if bcrypt is None:
            # bcrypt not installed; do not raise to avoid breaking runtime envs
            logger.debug("bcrypt not installed; cannot verify bcrypt hash.")
            return False
        try:
            # Libraries ensure constant-time behavior; avoid custom comparisons
            return bool(bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8")))
        except ValueError:
            # Invalid bcrypt hash format
            logger.debug("Invalid bcrypt hash format encountered during verification.")
            return False
        except Exception:
            logger.debug("Unexpected error during bcrypt verification.", exc_info=True)
            return False

    # Unknown or unsupported scheme
    logger.debug(
        "Unknown password hash scheme.",
        extra={"prefix": hashed[:7] if isinstance(hashed, str) else None},
    )
    return False