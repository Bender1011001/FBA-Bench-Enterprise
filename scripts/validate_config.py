#!/usr/bin/env python3
"""
Deployment configuration validator for FBA-Bench.

Usage:
  python scripts/validate_config.py --env-file .env
  python scripts/validate_config.py --env-file config/env/prod.env
  python scripts/validate_config.py             # reads os.environ only

Exit codes:
  0 = OK
  2 = Warnings (non-fatal)
  3 = Errors (fatal)
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from typing import Dict, Tuple

WARNING = "WARNING"
ERROR = "ERROR"
INFO = "INFO"


def load_env_file(path: str) -> Dict[str, str]:
    env: Dict[str, str] = {}
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                s = line.strip()
                if not s or s.startswith("#"):
                    continue
                if "=" not in s:
                    continue
                k, v = s.split("=", 1)
                env[k.strip()] = v.strip()
    except FileNotFoundError:
        raise
    return env


def truthy(v: str | None, default: bool = False) -> bool:
    if v is None:
        return default
    s = v.strip().lower()
    if s in ("1", "true", "yes", "on"):
        return True
    if s in ("0", "false", "no", "off"):
        return False
    return default


def is_protected_env(env: Dict[str, str]) -> bool:
    v = (
        (env.get("ENVIRONMENT") or env.get("APP_ENV") or env.get("ENV") or "development")
        .strip()
        .lower()
    )
    return v in ("production", "prod", "staging")


def result(line: str, level: str = INFO) -> None:
    print(f"[{level}] {line}")


def validate(env: Dict[str, str]) -> Tuple[int, int]:
    warnings = 0
    errors = 0

    protected = is_protected_env(env)
    if protected:
        result(
            f"Protected environment detected (ENVIRONMENT={env.get('ENVIRONMENT', 'N/A')})", INFO
        )
    else:
        result(
            f"Non-protected environment detected (ENVIRONMENT={env.get('ENVIRONMENT', 'N/A')})",
            INFO,
        )

    # Auth checks
    auth_enabled = truthy(env.get("AUTH_ENABLED"), default=protected)
    auth_test_bypass = truthy(env.get("AUTH_TEST_BYPASS"), default=not protected)
    auth_protect_docs = truthy(env.get("AUTH_PROTECT_DOCS"), default=protected)

    if auth_enabled and auth_test_bypass:
        errors += 1
        result("AUTH_TEST_BYPASS must be false when AUTH_ENABLED is true.", ERROR)

    if protected and not auth_protect_docs:
        warnings += 1
        result(
            "API docs should be protected in staging/production. Set AUTH_PROTECT_DOCS=true.",
            WARNING,
        )

    if auth_enabled:
        key_present = (
            any(
                (env.get("AUTH_JWT_PUBLIC_KEY") or "").strip(),
            )
            or any(
                (env.get("AUTH_JWT_PUBLIC_KEYS") or "").strip(),
            )
            or any(
                (env.get("AUTH_JWT_PUBLIC_KEY_FILE") or "").strip(),
            )
        )
        if not key_present:
            errors += 1
            result(
                "AUTH_ENABLED=true but no JWT verification key configured. Set AUTH_JWT_PUBLIC_KEY or AUTH_JWT_PUBLIC_KEYS or AUTH_JWT_PUBLIC_KEY_FILE.",
                ERROR,
            )

    # CORS checks
    cors = (env.get("FBA_CORS_ALLOW_ORIGINS") or "").strip()
    if protected:
        if not cors:
            errors += 1
            result(
                "FBA_CORS_ALLOW_ORIGINS must be set to a comma-separated allow-list in staging/production.",
                ERROR,
            )
        elif cors == "*":
            errors += 1
            result("FBA_CORS_ALLOW_ORIGINS cannot be '*' in staging/production.", ERROR)

    # Rate limit
    rate = (env.get("API_RATE_LIMIT") or "").strip()
    if not rate:
        warnings += 1
        result(
            "API_RATE_LIMIT not set. Default may apply (100/minute). Consider setting explicitly.",
            WARNING,
        )
    else:
        if not re.match(r"^\d+/(second|minute|hour|day)s?$", rate.strip(), flags=re.IGNORECASE):
            warnings += 1
            result(
                f"API_RATE_LIMIT format seems unusual: {rate} (expected like '100/minute').",
                WARNING,
            )

    # Redis
    redis_url = (env.get("FBA_BENCH_REDIS_URL") or env.get("REDIS_URL") or "").strip()
    if not redis_url:
        warnings += 1
        result(
            "Redis URL not set (FBA_BENCH_REDIS_URL or REDIS_URL). Realtime/websocket features may be impaired.",
            WARNING,
        )
    else:
        if not (redis_url.startswith("redis://") or redis_url.startswith("rediss://")):
            errors += 1
            result(f"Redis URL must start with redis:// or rediss:// (got: {redis_url})", ERROR)
        if protected and "@" not in redis_url:
            warnings += 1
            result(
                "Redis URL in production should include authentication (username/password).",
                WARNING,
            )

    # Database
    db_url = (env.get("FBA_BENCH_DB_URL") or env.get("DATABASE_URL") or "").strip()
    if not db_url:
        warnings += 1
        result(
            "DATABASE_URL not set. SQLite may be used by default; not recommended for production.",
            WARNING,
        )
    else:
        if protected and db_url.startswith("sqlite:"):
            errors += 1
            result(
                "SQLite is not recommended for staging/production. Use Postgres (postgresql+asyncpg://...).",
                ERROR,
            )

    # Logging
    log_level = (env.get("LOG_LEVEL") or "").strip().upper()
    if log_level and log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        warnings += 1
        result(
            f"LOG_LEVEL value '{log_level}' is unusual. Expected one of DEBUG, INFO, WARNING, ERROR, CRITICAL.",
            WARNING,
        )

    # Final summary
    if errors == 0 and warnings == 0:
        result("All checks passed.", INFO)
    else:
        result(f"Summary: {errors} error(s), {warnings} warning(s).", INFO)

    return errors, warnings


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--env-file", help="Path to .env-like file to validate", default=None)
    args = ap.parse_args()

    merged: Dict[str, str] = {}

    if args.env_file:
        if not os.path.isfile(args.env_file):
            print(f"[ERROR] env file not found: {args.env_file}", file=sys.stderr)
            return 3
        file_env = load_env_file(args.env_file)
        merged.update(file_env)

    # Overlay with current process environment (highest precedence)
    for k, v in os.environ.items():
        merged[k] = v

    errors, warnings = validate(merged)
    if errors > 0:
        return 3
    if warnings > 0:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
