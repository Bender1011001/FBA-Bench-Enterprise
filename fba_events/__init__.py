"""
FBA Events compatibility shim.
Re-exports events from src/fba_events for backward compatibility.
"""

import os
import sys

# Add src directory to path so we can import from src/fba_events
src_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Ensure this package's __path__ includes the real src/fba_events directory so
# submodule imports like `from fba_events.base import BaseEvent` resolve correctly.
_pkg_dir = os.path.abspath(os.path.join(src_path, "fba_events"))
try:
    __path__  # type: ignore[name-defined]
except Exception:  # pragma: no cover
    __path__ = []  # type: ignore[assignment, name-defined]
if _pkg_dir not in __path__:  # type: ignore[operator]
    __path__.append(_pkg_dir)  # type: ignore[union-attr]

# IMPORTANT:
# Do NOT import from 'src.fba_events' directly here, as that creates a second
# module hierarchy (src.fba_events.*) distinct from 'fba_events.*' and causes
# class identity mismatches in isinstance checks.
# We adjust __path__ above so that imports like 'from fba_events.adversarial import PhishingEvent'
# resolve to the single canonical module under this package.
#
# Explicit top-level re-exports (within this package) for test/back-compat:
# These imports come from the single canonical module tree under 'fba_events.*'
# and therefore do not create duplicate class identities.
# from .adversarial import (
#     AdversarialEvent as AdversarialEvent,
# )
# from .adversarial import (
#     AdversarialResponse as AdversarialResponse,
# )
# from .adversarial import (
#     ComplianceTrapEvent as ComplianceTrapEvent,
# )
# from .adversarial import (
#     MarketManipulationEvent as MarketManipulationEvent,
# )
# from .adversarial import (
#     PhishingEvent as PhishingEvent,
# )
# from .adversarial import (
#     ShockEndEvent as ShockEndEvent,
# )
# from .adversarial import (
#     ShockInjectionEvent as ShockInjectionEvent,
# )
# from .base import BaseEvent as BaseEvent
# from .budget import (
#     BudgetExceeded as BudgetExceeded,
# )
# from .budget import (
#     BudgetWarning as BudgetWarning,
# )
# from .budget import (
#     ConstraintViolation as ConstraintViolation,
# )
# from .bus import (
#     EventBus as EventBus,
# )
# from .bus import (
#     InMemoryEventBus as InMemoryEventBus,
# )
# from .bus import (
#     get_event_bus as get_event_bus,
# )
# from .bus import (
#     set_event_bus as set_event_bus,
# )
# from .competitor import (
#     CompetitorPricesUpdated as CompetitorPricesUpdated,
# )
# from .competitor import (
#     CompetitorState as CompetitorState,
# )
# from .customer import (
#     ComplaintEvent as ComplaintEvent,
# )
# from .customer import (
#     CustomerDisputeEvent as CustomerDisputeEvent,
# )
# from .customer import (
#     CustomerMessageReceived as CustomerMessageReceived,
# )
# from .customer import (
#     CustomerReviewEvent as CustomerReviewEvent,
# )
# from .customer import (
#     DisputeResolvedEvent as DisputeResolvedEvent,
# )
# from .customer import (
#     NegativeReviewEvent as NegativeReviewEvent,
# )
# from .customer import (
#     RespondToCustomerMessageCommand as RespondToCustomerMessageCommand,
# )
# from .customer import (
#     RespondToReviewCommand as RespondToReviewCommand,
# )
# from .inventory import (
#     InventoryUpdate as InventoryUpdate,
# )
# from .inventory import (
#     LowInventoryEvent as LowInventoryEvent,
# )
# from .inventory import (
#     WorldStateSnapshotEvent as WorldStateSnapshotEvent,
# )
# from .marketing import (
#     AdClickEvent as AdClickEvent,
# )
# from .marketing import (
#     AdSpendEvent as AdSpendEvent,
# )
# from .marketing import (
#     CustomerAcquisitionEvent as CustomerAcquisitionEvent,
# )
# from .marketing import (
#     MarketTrendEvent as MarketTrendEvent,
# )
# from .marketing import (
#     RunMarketingCampaignCommand as RunMarketingCampaignCommand,
# )
# from .marketing import (
#     VisitEvent as VisitEvent,
# )
# from .pricing import (
#     ProductPriceUpdated as ProductPriceUpdated,
# )
# from .pricing import (
#     SetPriceCommand as SetPriceCommand,
# )
# from .reporting import LossEvent as LossEvent
# from .reporting import ProfitReport as ProfitReport
# from .sales import SaleOccurred as SaleOccurred

# Legacy alias expected by some tests
# PurchaseOccurred = SaleOccurred
# from .cost import (
#     ApiCostEvent as ApiCostEvent,
# )
# from .cost import (
#     LLMUsageReportedEvent as LLMUsageReportedEvent,
# )
# from .cost import (
#     PenaltyEvent as PenaltyEvent,
# )
# from .cost import (
#     TokenUsageEvent as TokenUsageEvent,
# )

__all__ = [
    # Base/bus
    # "BaseEvent",
    # "EventBus",
    # "InMemoryEventBus",
    # "get_event_bus",
    # "set_event_bus",
    # Adversarial
    # "AdversarialEvent",
    # "AdversarialResponse",
    # "ComplianceTrapEvent",
    # "MarketManipulationEvent",
    # "PhishingEvent",
    # "ShockInjectionEvent",
    # "ShockEndEvent",
    # Pricing
    # "SetPriceCommand",
    # "ProductPriceUpdated",
    # Competitor
    # "CompetitorPricesUpdated",
    # "CompetitorState",
    # Inventory
    "InventoryUpdate",
    "LowInventoryEvent",
    "WorldStateSnapshotEvent",
    # Budget
    "BudgetWarning",
    "BudgetExceeded",
    "ConstraintViolation",
    # Marketing
    "MarketTrendEvent",
    "RunMarketingCampaignCommand",
    "AdClickEvent",
    "CustomerAcquisitionEvent",
    "VisitEvent",
    "AdSpendEvent",
    # Customer
    "CustomerMessageReceived",
    "NegativeReviewEvent",
    "ComplaintEvent",
    "RespondToCustomerMessageCommand",
    "CustomerDisputeEvent",
    "DisputeResolvedEvent",
    "CustomerReviewEvent",
    "RespondToReviewCommand",
    # Reporting
    "ProfitReport",
    "LossEvent",
    # Sales
    "SaleOccurred",
    "PurchaseOccurred",
    # Cost
    "ApiCostEvent",
    "TokenUsageEvent",
    "PenaltyEvent",
    "LLMUsageReportedEvent",
]
