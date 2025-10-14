from __future__ import annotations

# Back-compat shim: expose CLI utilities under fba_bench.cli
# Actual implementation lives in fba_bench_core.cli
from fba_bench_core.cli import *  # noqa: F403
