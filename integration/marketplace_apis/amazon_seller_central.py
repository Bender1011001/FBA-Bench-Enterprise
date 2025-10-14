import random
from typing import Any, Dict


class AmazonSellerCentral:
    """
    A "Level 2" mock of the Amazon Seller Central API.

    This is a stateful, deterministic mock that simulates a dynamic marketplace
    without making any real external API calls. It's designed for cost-effective
    and reproducible testing of agent logic.

    Features:
    - Simulates two competitors with distinct pricing strategies.
    - Models price-sensitive demand: lower prices lead to higher sales volume.
    - Maintains its own internal state for competitor prices.
    """

    def __init__(self, api_key: str, api_secret: str, marketplace_id: str):
        # The credentials are not used but are part of the expected interface.
        self._api_key = api_key
        self._api_secret = api_secret
        self._marketplace_id = marketplace_id

        # Internal state for the mock
        self._competitor_prices: Dict[str, float] = {}

    def _get_or_init_competitor_prices(self, product_id: str) -> Dict[str, float]:
        """Initializes competitor prices if they don't exist for the product."""
        if product_id not in self._competitor_prices:
            # Initialize with some baseline prices
            self._competitor_prices[product_id] = {
                "competitor_A_price": 24.99,
                "competitor_B_price": 25.50,
            }
        return self._competitor_prices[product_id]

    def get_competitor_prices(self, product_id: str) -> Dict[str, float]:
        """
        Simulates fetching prices from two competitors.
        - Competitor A is aggressive and tries to undercut.
        - Competitor B is stable and adjusts prices slowly.
        """
        prices = self._get_or_init_competitor_prices(product_id)

        # Simulate Competitor A's move (undercuts slightly)
        prices["competitor_A_price"] *= 1 - random.uniform(0.01, 0.03)  # drop by 1-3%

        # Simulate Competitor B's move (small random fluctuation)
        prices["competitor_B_price"] += random.uniform(-0.25, 0.25)

        return {
            "competitor_a": round(prices["competitor_A_price"], 2),
            "competitor_b": round(prices["competitor_B_price"], 2),
        }

    def get_estimated_sales_volume(self, product_id: str, your_price: float) -> int:
        """
        Estimates sales volume based on your price relative to competitors.
        A simple model where lower prices significantly boost sales.
        """
        prices = self._get_or_init_competitor_prices(product_id)
        avg_competitor_price = (prices["competitor_A_price"] + prices["competitor_B_price"]) / 2

        base_demand = 100  # Base sales volume per time step

        # If you are cheaper than the average, you get a big bonus
        if your_price < avg_competitor_price:
            price_advantage = (avg_competitor_price - your_price) / avg_competitor_price
            # Exponential bonus for being cheaper
            sales_multiplier = 1 + (price_advantage * 5)
        else:
            # Penalty for being more expensive
            price_disadvantage = (your_price - avg_competitor_price) / avg_competitor_price
            sales_multiplier = max(0.1, 1 - (price_disadvantage * 2))

        # Add some random noise
        noise = random.randint(-10, 10)

        estimated_sales = int(base_demand * sales_multiplier) + noise
        return max(0, estimated_sales)

    def get_product_pricing(self, product_id: str) -> Dict[str, Any]:
        """Mocked function to get your own product's pricing - in a real scenario
        this would be your own data."""
        # This function is less important in the mock as the agent sets its own price.
        # We'll just return a static example.
        return {"price": 25.00, "currency": "USD"}

    def submit_inventory_update(self, product_id: str, quantity: int) -> Dict[str, str]:
        """Simulates updating inventory levels."""
        # In this mock, we just acknowledge the request.
        return {
            "status": "success",
            "message": f"Inventory for {product_id} updated to {quantity}.",
        }
