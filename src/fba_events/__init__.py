"""fba_events: split modules for FBA-Bench v3 event schema."""

from __future__ import annotations

from .adversarial import ShockEndEvent as ShockEndEvent
from .adversarial import ShockInjectionEvent as ShockInjectionEvent

# Core base event (explicit top-level export for convenience/back-compat)
from .base import BaseEvent as BaseEvent

# Ergonomic re-export for canonical in-memory event bus
from .bus import EventBus as EventBus
from .bus import InMemoryEventBus as InMemoryEventBus

# Cost metrics related events (re-exports for convenience/back-compat)
from .cost import ApiCostEvent as ApiCostEvent
from .cost import LLMUsageReportedEvent as LLMUsageReportedEvent
from .cost import PenaltyEvent as PenaltyEvent
from .cost import TokenUsageEvent as TokenUsageEvent
from .marketing import AdClickEvent as AdClickEvent
from .marketing import CustomerAcquisitionEvent as CustomerAcquisitionEvent
from .marketing import VisitEvent as VisitEvent
from .registry import *  # noqa: F403

# Commonly used domain events
from .supplier import PurchaseOccurred as PurchaseOccurred
