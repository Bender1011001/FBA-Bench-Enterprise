from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from fba_bench_core.money import Money


class SalesResult(BaseModel):
    """
    Represents the outcome of a processed sale.

    This is the canonical, Pydantic-based model that aligns with the
    typed event schemas and contract tests. It replaces the previous
    dictionary-based implementation.
    """

    product_id: UUID = Field(..., description="The unique ID of the product sold.")
    quantity_sold: int = Field(..., gt=0, description="The number of units sold.")
    total_revenue: Money = Field(..., description="The total revenue generated from the sale.")

    model_config = ConfigDict(
        frozen=True,
        arbitrary_types_allowed=True,  # Allow canonical Money type
        title="Canonical Sales Result",
    )
