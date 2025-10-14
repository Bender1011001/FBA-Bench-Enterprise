from __future__ import annotations

# Top-level shim for backward compatibility with tests importing `alert_system`
# Re-export the alert system from the observability package.
from observability.alert_system import (
    DEFAULT_ALERT_RULES,
    AlertEvent,
    AlertRule,
    AlertSeverity,
    ObservabilityAlertSystem,
)

__all__ = [
    "ObservabilityAlertSystem",
    "AlertRule",
    "AlertSeverity",
    "AlertEvent",
    "DEFAULT_ALERT_RULES",
]
