"""
Validators framework package.

Exports:
- Function-style registry helpers: register_validator, get_validator, list_validators
- Auto-imports built-in validators to trigger registration on package import
"""

# Auto-import built-in function-style validators (each module calls register_validator on import)
from src.benchmarking.validators import (  # noqa: F401
    determinism_check,
    reproducibility_metadata,
    structural_consistency,
)

from .audit_trail import AuditTrailManager

# Import legacy utilities for backward-compat public API
from .deterministic import DeterministicEnvironment
from .registry import (
    get_validator,
    list_validators,
    register_validator,
)  # function-style helpers
from .reproducibility_validator import ReproducibilityValidator
from .statistical_validator import StatisticalValidator
from .version_control import VersionControlManager

# The following will be added and auto-registered:
# - schema_adherence
# - outlier_detection
# - fairness_balance
try:
    from . import (
        fairness_balance,  # noqa: F401
        outlier_detection,  # noqa: F401
        schema_adherence,  # noqa: F401
    )
except Exception:
    # Optional during partial installs; tests that need them will import directly
    pass

__all__ = [
    "register_validator",
    "get_validator",
    "list_validators",
    "DeterministicEnvironment",
    "VersionControlManager",
    "StatisticalValidator",
    "AuditTrailManager",
    "ReproducibilityValidator",
]
