from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, List, Optional

from money import Money


@dataclass
class Product:
    """
    Canonical product model used by services (fees, customer events, etc.).

    Fields align with fee/trust calculators:
    - product_id: primary identifier (also used as asin alias if asin not provided)
    - category: category name used for referral fee lookups
    - weight_oz: numeric weight in ounces (int/float/Decimal)
    - dimensions_inches: [L, W, H] inches (numbers); used for dimensional weight
    - cost_basis: average cost per unit as Money
    - metadata: arbitrary extra attributes
    - asin: optional explicit ASIN; defaults to product_id
    """
    product_id: str
    category: str = "default"
    weight_oz: Decimal | int | float = 16
    dimensions_inches: List[Decimal | int | float] = field(default_factory=lambda: [12, 8, 1])
    cost_basis: Money = field(default_factory=Money.zero)
    metadata: dict[str, Any] = field(default_factory=dict)
    asin: Optional[str] = None

    def __post_init__(self) -> None:
        # Normalize asin
        if not self.asin:
            self.asin = self.product_id
        # Normalize cost_basis to Money
        if not isinstance(self.cost_basis, Money):
            try:
                if isinstance(self.cost_basis, (int, float, str, Decimal)):
                    self.cost_basis = Money.from_dollars(self.cost_basis)
                else:
                    self.cost_basis = Money.zero()
            except Exception:
                self.cost_basis = Money.zero()
        # Ensure dimensions has length 3
        try:
            if not isinstance(self.dimensions_inches, list) or len(self.dimensions_inches) != 3:
                self.dimensions_inches = [12, 8, 1]
        except Exception:
            self.dimensions_inches = [12, 8, 1]

__all__ = ["Product"]