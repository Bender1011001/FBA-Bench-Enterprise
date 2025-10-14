from __future__ import annotations

import os
import sys
import warnings

# Ensure fba_bench_core is importable in editable/unchecked-out environments
# When running tests directly (without installing the package), add ./src to sys.path.
try:
    from fba_bench_core.money import (  # type: ignore
        EUR_ZERO,
        GBP_ZERO,
        MAX_MONEY_CENTS,
        USD_ZERO,
        Money,
        max_money,
        min_money,
        sum_money,
    )
except ModuleNotFoundError:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    src_dir = os.path.join(repo_root, "src")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    # Retry import after adding src to path
    from fba_bench_core.money import (  # type: ignore
        EUR_ZERO,
        GBP_ZERO,
        MAX_MONEY_CENTS,
        USD_ZERO,
        Money,
        max_money,
        min_money,
        sum_money,
    )

warnings.warn(
    "The 'money' package is deprecated; use 'fba_bench_core.money'. This shim will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "Money",
    "sum_money",
    "max_money",
    "min_money",
    "USD_ZERO",
    "EUR_ZERO",
    "GBP_ZERO",
    "MAX_MONEY_CENTS",
]
