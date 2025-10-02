from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, List, Optional

from fba_bench.money import Money


@dataclass
class ExploitDefinition:
    exploit_id: str
    name: str
    description: str
    impact: str
    recommended_action: str
    categories: List[str]
    difficulty_level: int
    financial_impact_limit_usd: float
    context_requirements: Dict[str, Any]


@dataclass
class AdversarialEvent:
    exploit_id: str
    exploit_category: str
    exploit_name: str
    description: str
    impact: str
    recommended_action: str
    exploit_difficulty: int
    financial_impact_limit: float
    context_requirements: Dict[str, Any]


@dataclass
class PhishingEvent:
    event_id: str
    timestamp: datetime
    exploit_type: str = "phishing"
    difficulty_level: int
    target_action: str
    deception_vector: str
    sender_email: str
    message_content: str
    requested_action: str
    time_window: int


@dataclass
class MarketManipulationEvent:
    event_id: str
    timestamp: datetime
    exploit_type: str = "market_manipulation"
    difficulty_level: int
    target_action: str
    deception_vector: str
    false_data_type: str
    manipulated_values: Dict[str, Any]
    source_credibility: int
    market_impact_claim: str


@dataclass
class ComplianceTrapEvent:
    event_id: str
    timestamp: datetime
    exploit_type: str = "compliance_trap"
    difficulty_level: int
    target_action: str
    deception_vector: str
    fake_policy_name: str
    policy_description: str
    compliance_deadline: datetime
    penalty_claim: str
    official_appearance: int


@dataclass
class AdversarialResponse:
    event_id: str
    timestamp: datetime
    adversarial_event_id: str
    agent_id: str
    fell_for_exploit: bool
    detected_attack: bool
    reported_attack: bool
    protective_action_taken: Optional[str] = None
    response_time_seconds: float
    financial_damage: Optional[Money] = None
    exploit_difficulty: int


__all__ = [
    "AdversarialEvent",
    "AdversarialResponse",
    "ComplianceTrapEvent",
    "ExploitDefinition",
    "MarketManipulationEvent",
    "PhishingEvent",
]