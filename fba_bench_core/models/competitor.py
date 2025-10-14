from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from money import Money


@dataclass
class Competitor:
    """
    Canonical competitor entity used by services like CompetitorManager.

    Fields:
    - id: internal identifier (often an ASIN or competitor key)
    - price: Money price for the competitor's product
    - bsr: Best Seller Rank (lower is better)
    - sales_velocity: estimated units/time
    - strategy: optional strategy enum/object (kept as Any to avoid import cycles)
    - persona: optional behavioral persona object
    - competitor_id: optional external-facing identifier used in some tests/events
    - metadata: arbitrary extra attributes
    """
    id: str
    price: Money
    bsr: int = 100_000
    sales_velocity: float = 0.0
    strategy: Optional[Any] = None
    persona: Optional[Any] = None
    competitor_id: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Normalize price inputs into Money
        if not isinstance(self.price, Money):
            try:
                # Treat ints as cents, float/str as dollars
                if isinstance(self.price, int):
                    self.price = Money(self.price)
                else:
                    self.price = Money.from_dollars(self.price)
            except Exception:
                self.price = Money.zero()


__all__ = ["Competitor"]