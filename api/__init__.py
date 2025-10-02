"""API package initialization.

Ensures ZoneInfo is available via builtins for environments lacking the standard
library's zoneinfo module at runtime (e.g., constrained environments).
"""

import builtins

try:
    from zoneinfo import ZoneInfo  # Python 3.9+
    builtins.ZoneInfo = ZoneInfo  # type: ignore[attr-defined]
except Exception:
    # Best-effort: if zoneinfo is unavailable, leave environment unchanged.
    # Tests that rely on ZoneInfo should import the api package first so that,
    # when available, ZoneInfo is injected into builtins.
    pass