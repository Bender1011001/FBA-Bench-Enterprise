"""
Project-wide site customizations for test/runtime convenience.

This module is auto-imported by Python's site module if present on sys.path.
We expose ZoneInfo in builtins so tests that reference ZoneInfo without importing it do not fail.
"""

import builtins

try:
    from zoneinfo import ZoneInfo  # Python 3.9+
    builtins.ZoneInfo = ZoneInfo  # type: ignore[attr-defined]
except Exception:
    # If zoneinfo is unavailable on a given platform, we do nothing.
    # Tests expecting ZoneInfo should be skipped or handled separately.
    pass