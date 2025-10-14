import warnings

from fba_bench_core.services import *  # noqa: F403

warnings.warn(
    "The 'services' package is deprecated; use 'fba_bench_core.services'. This shim will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)
