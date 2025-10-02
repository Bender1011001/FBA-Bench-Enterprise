from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional, List

from fba_bench.money import Money


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class AdversarialEvent:
    # Non-default fields must come first
    event_type: str
    difficulty_level: int
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "difficulty_level": self.difficulty_level,
            "payload": self.payload,
            "metadata": self.metadata or {},
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass(frozen=True)
class AdversarialResponse:
    handled: bool
    notes: Optional[str] = None
    mitigation_cost: Optional[Money] = None
    extra: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "handled": self.handled,
            "notes": self.notes,
            "mitigation_cost": self.mitigation_cost.to_dict() if self.mitigation_cost else None,
            "extra": self.extra,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass(frozen=True)
class ComplianceTrapEvent:
    event_type: str
    difficulty_level: int
    policy_id: str
    severity: str
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=_utcnow)

    @staticmethod
    def make(policy_id: str, severity: str, difficulty_level: int, payload: Optional[Dict[str, Any]] = None,
             metadata: Optional[Dict[str, Any]] = None) -> "ComplianceTrapEvent":
        return ComplianceTrapEvent(
            event_type="compliance_trap",
            difficulty_level=difficulty_level,
            policy_id=policy_id,
            severity=severity,
            payload=payload or {},
            metadata=metadata,
        )


@dataclass(frozen=True)
class MarketManipulationEvent:
    event_type: str
    difficulty_level: int
    competitor_id: str
    action: str
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=_utcnow)

    @staticmethod
    def make(competitor_id: str, action: str, difficulty_level: int,
             payload: Optional[Dict[str, Any]] = None,
             metadata: Optional[Dict[str, Any]] = None) -> "MarketManipulationEvent":
        return MarketManipulationEvent(
            event_type="market_manipulation",
            difficulty_level=difficulty_level,
            competitor_id=competitor_id,
            action=action,
            payload=payload or {},
            metadata=metadata,
        )


@dataclass(frozen=True)
class PhishingEvent:
    event_type: str
    difficulty_level: int
    target_email: str
    attack_vector: str
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=_utcnow)

    @staticmethod
    def make(target_email: str, attack_vector: str, difficulty_level: int,
             payload: Optional[Dict[str, Any]] = None,
             metadata: Optional[Dict[str, Any]] = None) -> "PhishingEvent":
        return PhishingEvent(
            event_type="phishing",
            difficulty_level=difficulty_level,
            target_email=target_email,
            attack_vector=attack_vector,
            payload=payload or {},
            metadata=metadata,
        )


@dataclass(frozen=True)
class ExploitDefinition:
    name: str
    description: str
    risk_score: int
    financial_damage: Money = field(default_factory=lambda: Money.from_dollars("0", "USD"))
    tags: List[str] = field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "risk_score": self.risk_score,
            "financial_damage": self.financial_damage.to_dict(),
            "tags": list(self.tags),
            "metadata": self.metadata or {},
        }


__all__ = [
    "AdversarialEvent",
    "AdversarialResponse",
    "ComplianceTrapEvent",
    "MarketManipulationEvent",
    "PhishingEvent",
    "ExploitDefinition",
]