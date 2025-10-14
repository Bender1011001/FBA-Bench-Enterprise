"""
Ethics and compliance-related events for FBA-Bench.
Defines ComplianceViolationEvent which is published by services (e.g., FinancialAuditService)
when a compliance rule or safety policy is violated.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

from .base import BaseEvent


@dataclass
class ComplianceViolationEvent(BaseEvent):
    """
    Published when a compliance/audit violation occurs.
    Consumers include EthicalSafetyMetrics and reputation/safety systems.

    Attributes:
        violation_type: A machine-readable violation code (e.g., 'accounting_identity', 'negative_cash').
        severity: Severity level (e.g., 'CRITICAL', 'ERROR', 'WARNING', 'INFO').
        details: Arbitrary structured context for the violation.
    """

    violation_type: str
    severity: str
    details: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        super().__post_init__()

        # Validate violation_type: Must be a non-empty string.
        if not self.violation_type or not isinstance(self.violation_type, str):
            raise ValueError(
                "Violation type must be a non-empty string for ComplianceViolationEvent."
            )

        # Validate severity: Must be one of the predefined categories.
        valid_severities = ["CRITICAL", "ERROR", "WARNING", "INFO"]
        if self.severity not in valid_severities:
            raise ValueError(
                f"Severity must be one of {valid_severities}, but got '{self.severity}' for ComplianceViolationEvent."
            )

        # Validate details: Must be a dictionary.
        if not isinstance(self.details, dict):
            raise TypeError("Details must be a dictionary for ComplianceViolationEvent.")

    def to_summary_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "violation_type": self.violation_type,
            "severity": self.severity,
            "details": self.details,
        }
