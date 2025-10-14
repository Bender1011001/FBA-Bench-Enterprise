"""LLM-related events for FBA-Bench."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict

from .base import BaseEvent


@dataclass
class LLMResponseErrorEvent(BaseEvent):
    """
    Emitted when an LLM response fails parsing or schema validation.
    """

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    agent_id: str = ""
    error_type: str = ""
    message: str = ""
    severity: str = "warning"
    details: Dict[str, Any] = field(default_factory=dict)

    def to_summary_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "agent_id": self.agent_id,
            "error_type": self.error_type,
            "message": self.message,
            "severity": self.severity,
            "details": self.details,
        }


__all__ = ["LLMResponseErrorEvent"]
