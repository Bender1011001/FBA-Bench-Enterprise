from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# Import canonical Money (re-exported shim ensures single implementation)
from money import Money


class Product(BaseModel):
    """
    Canonical Product model used in simulation and tests.

    This model is intentionally permissive to maintain compatibility with existing tests.
    It accepts common legacy fields (asin, base_demand, inventory_units, etc.) while
    preserving strong typing for monetary fields.

    Key compatibility behaviors:
    - If sku is missing but asin is provided, sku defaults to asin.
    - If name is missing, name defaults to asin or sku.
    - If weight_kg is missing but `weight` is provided, weight_kg is derived from `weight`.
    - Extra/unknown fields are allowed and set as attributes for ease-of-use in tests.
    """

    # Canonical identifiers
    id: UUID = Field(default_factory=uuid4)
    sku: Optional[str] = Field(default=None, description="Stock Keeping Unit")
    asin: Optional[str] = Field(default=None, description="Amazon ASIN identifier")
    name: Optional[str] = Field(default=None, description="Product display name")

    # Domain attributes
    category: Optional[str] = Field(default="general")
    price: Money
    cost: Money

    # Optional analytics/metadata expected by tests
    base_demand: Optional[float] = Field(default=0.0, ge=0)
    inventory_units: Optional[int] = Field(default=0, ge=0)
    bsr: Optional[int] = Field(default=100000, ge=1)
    trust_score: Optional[float] = Field(default=0.8, ge=0.0, le=1.0)
    size: Optional[str] = Field(default="small")
    weight_kg: Optional[float] = Field(default=None, gt=0)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # -------------------------
    # Normalizers and validators
    # -------------------------
    @field_validator("price", "cost", mode="before")
    def ensure_money_type(cls, v):
        """
        Normalize various inputs to canonical Money:
        - Money instance: passthrough
        - dict with 'cents' or 'amount' (dollars) + optional 'currency'
        - numeric/string: interpreted as dollars
        """
        if isinstance(v, Money):
            return v
        if isinstance(v, dict):
            currency = v.get("currency", "USD")
            cents = v.get("cents", None)
            if isinstance(cents, int):
                return Money(int(cents), currency)
            amount = v.get("amount", None)
            if amount is not None:
                return Money.from_dollars(amount, currency)
            # Fallback if unrecognized dict keys: treat as zero dollars
            return Money.zero(currency)
        # Numeric or string: treat as dollars
        if isinstance(v, (int, float, str)):
            return Money.from_dollars(v)
        # Unknown type: let pydantic raise a validation error downstream
        return v

    @model_validator(mode="before")
    def _coerce_legacy_fields(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pre-process legacy/alternate field names and derive sensible defaults.
        - sku <- asin when sku missing
        - name <- asin or sku when name missing
        - weight_kg <- weight if provided
        """
        asin = values.get("asin")
        sku = values.get("sku")
        if not sku and asin:
            values["sku"] = asin

        if not values.get("name"):
            values["name"] = asin or sku or "unnamed"

        # Map legacy 'weight' to 'weight_kg' (assumed already in kg in tests)
        if values.get("weight_kg") is None and "weight" in values:
            try:
                w = float(values.get("weight"))
                if w > 0:
                    values["weight_kg"] = w
            except Exception:
                pass

        return values

    # -------------------------
    # Convenience methods
    # -------------------------
    def get_profit_margin(self) -> Money:
        """
        Return the unit profit margin as Money (price - cost).
        """
        try:
            return self.price - self.cost
        except Exception:
            # Fallback: compute via cents if direct subtraction not supported
            return Money(int(self.price.cents) - int(self.cost.cents))

    # Pydantic v2 model configuration
    model_config = ConfigDict(
        frozen=False,
        arbitrary_types_allowed=True,  # Allow canonical Money type
        title="Canonical Product Model",
        extra="allow",  # Accept extra fields used by some tests
    )
