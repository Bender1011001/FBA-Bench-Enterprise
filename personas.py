"""
DEPRECATED: Competitor Persona Library - High-Fidelity Market Chaos
This file will be removed in a future version.
Please update your imports to use agents.baseline.persona directly.

This module implements the "Embrace Irrationality" architectural mandate by providing
a library of distinct competitor personas with irrational, human-like behaviors that
deviate from simple optimization.

Each persona encapsulates specific market behavior patterns that introduce realistic
chaos and unpredictability into the simulation environment.
"""

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, Optional

# Use project-local money implementation explicitly to avoid third-party shadowing
from money import Money  # Fixed import for Money

from fba_events.competitor import CompetitorState  # Fixed import for CompetitorState


def max_money(a: Money, b: Money) -> Money:
    """
    Return the larger of two Money values by cents.
    """
    try:
        return a if a.cents >= b.cents else b
    except Exception:
        # Fallback: compare via float conversion if cents missing
        try:
            return a if float(str(a)) >= float(str(b)) else b
        except Exception:
            # Last resort: keep 'a' to avoid crashing personas
            return a

def min_money(a: Money, b: Money) -> Money:
    """
    Return the smaller of two Money values by cents.
    """
    try:
        return a if a.cents <= b.cents else b
    except Exception:
        # Fallback: compare via float conversion if cents missing
        try:
            return a if float(str(a)) <= float(str(b)) else b
        except Exception:
            # Last resort: keep 'a' to avoid crashing personas
            return a

# Issue deprecation warning should be externalized, not hardcoded in the file
# warnings.warn( # Removed hardcoded deprecation warning
#     "personas.py shim is deprecated and will be removed in a future version. "
#     "Please update your imports to use agents.baseline.persona directly.",
#     DeprecationWarning,
#     stacklevel=2,
# )


@dataclass
class MarketConditions:
    """
    Market state information provided to personas for decision-making.

    This encapsulates all the market intelligence a competitor would have
    access to when making pricing and strategy decisions.
    """

    current_tick: int
    current_state: CompetitorState
    market_competitors: list[CompetitorState]
    market_average_price: Money
    market_min_price: Money
    market_max_price: Money
    own_sales_velocity: float  # Recent sales trend
    market_trend: str  # "rising", "falling", "stable"


class CompetitorPersona(ABC):
    """
    Base class for all competitor personas.

    Each persona represents a distinct competitive behavior pattern with
    its own decision-making logic, risk tolerance, and market response style.

    Personas maintain their own internal state and can exhibit time-dependent
    behaviors, memory of past actions, and complex strategic patterns.
    """

    def __init__(
        self,
        competitor_id: str,
        cost_basis: Money,
        currency: str = "USD",
        seed: Optional[int] = None,
    ):
        """
        Initialize the persona with basic competitor information.

        Args:
            competitor_id: Unique identifier for this competitor.
            cost_basis: Minimum viable price (cost to produce/acquire product).
            currency: ISO currency code used for Money calculations within this persona (default: "USD").
            seed: Optional seed for random number generation to ensure reproducibility.
        """
        if not isinstance(competitor_id, str) or not competitor_id:
            raise ValueError("competitor_id must be a non-empty string.")
        if not isinstance(cost_basis, Money):
            raise TypeError("cost_basis must be an instance of Money.")
        if not isinstance(currency, str) or not currency:
            raise ValueError("currency must be a non-empty string.")

        self.competitor_id = competitor_id
        self.cost_basis = cost_basis
        self.currency = currency
        self.internal_state: Dict[str, Any] = {}
        self.last_action_tick: int = 0
        self.rng = random.Random(seed)  # Seed control for reproducibility

    @abstractmethod
    async def act(self, market_conditions: MarketConditions) -> Optional[CompetitorState]:
        """
        Evaluate market conditions and decide on competitor actions.

        This is the core decision-making method that each persona must implement.
        The persona receives complete market intelligence and returns an updated
        CompetitorState if it decides to take action, or None if no action.

        Args:
            market_conditions: Current market state and competitor intelligence

        Returns:
            Updated CompetitorState if action taken, None if no changes
        """

    def _calculate_minimum_price(self) -> Money:
        """Calculate the absolute minimum price (cost basis + small margin)."""
        return self.cost_basis * Decimal("1.01")  # 1% minimum margin, returns Money

    def _get_state_value(self, key: str, default: Any = None) -> Any:
        """Safely retrieve internal state value."""
        return self.internal_state.get(key, default)

    def _set_state_value(self, key: str, value: Any) -> None:
        """Update internal state value."""
        self.internal_state[key] = value


class IrrationalSlasher(CompetitorPersona):
    """
    The Irrational Price Slasher Persona

    This persona represents competitors who occasionally engage in destructive
    price wars, ignoring market logic and slashing prices to unsustainable levels.

    Behavior Patterns:
    - 15% chance per tick to enter "slash mode"
    - During slash mode: prices set to just above cost basis
    - Slash episodes last 3-7 ticks
    - Higher chance to slash if losing market share
    - May trigger cascading price wars
    """

    def __init__(
        self,
        competitor_id: str,
        cost_basis: Money,
        currency: str = "USD",
        slash_probability: float = 0.15,
        slash_duration_range: tuple[int, int] = (3, 7),
        low_sales_velocity_threshold: float = 0.5,
        market_avg_price_threshold: Decimal = Decimal("1.2"),
        max_slash_probability: float = 0.4,
        rational_price_discount: Decimal = Decimal("0.95"),
        slash_sales_velocity_boost: Decimal = Decimal("1.5"),
        seed: Optional[int] = None,  # Added seed
    ):
        super().__init__(competitor_id, cost_basis, currency, seed=seed)  # Pass seed to super()

        # Input validation for IrrationalSlasher specific parameters
        if not (0.0 <= slash_probability <= 1.0):
            raise ValueError("slash_probability must be between 0.0 and 1.0.")
        if not (
            isinstance(slash_duration_range, tuple)
            and len(slash_duration_range) == 2
            and all(isinstance(i, int) for i in slash_duration_range)
            and slash_duration_range[0] <= slash_duration_range[1]
            and slash_duration_range[0] > 0
        ):
            raise ValueError(
                "slash_duration_range must be a tuple of two positive integers (min, max) where min <= max."
            )
        if not (0.0 <= low_sales_velocity_threshold <= 1.0):
            raise ValueError("low_sales_velocity_threshold must be between 0.0 and 1.0.")
        if not isinstance(market_avg_price_threshold, Decimal) or market_avg_price_threshold <= 0:
            raise ValueError("market_avg_price_threshold must be a positive Decimal.")
        if not (0.0 <= max_slash_probability <= 1.0):
            raise ValueError("max_slash_probability must be between 0.0 and 1.0.")
        if not isinstance(rational_price_discount, Decimal) or not (
            Decimal("0") < rational_price_discount < Decimal("1")
        ):
            raise ValueError(
                "rational_price_discount must be a Decimal between 0 and 1 (exclusive)."
            )
        if not isinstance(slash_sales_velocity_boost, Decimal) or slash_sales_velocity_boost <= 0:
            raise ValueError("slash_sales_velocity_boost must be a positive Decimal.")

        # Core slashing behavior parameters (configurable)
        self.slash_probability = slash_probability  # base chance per tick
        self.slash_duration_range = slash_duration_range  # ticks
        self.low_sales_velocity_threshold = low_sales_velocity_threshold
        self.market_avg_price_threshold = market_avg_price_threshold
        self.max_slash_probability = max_slash_probability
        self.rational_price_discount = rational_price_discount
        self.slash_sales_velocity_boost = slash_sales_velocity_boost

    async def act(self, market_conditions: MarketConditions) -> Optional[CompetitorState]:
        """
        Implement irrational slashing behavior.

        The slasher evaluates whether to enter slash mode, continue slashing,
        or return to rational pricing based on market conditions and internal state.
        """
        current_tick = market_conditions.current_tick
        is_slashing = self._get_state_value("is_slashing", False)
        slash_end_tick = self._get_state_value("slash_end_tick", 0)

        # Check if currently in slash mode
        if is_slashing:
            if current_tick >= slash_end_tick:
                # End slash mode - return to rational pricing
                self._set_state_value("is_slashing", False)
                self._set_state_value("slash_end_tick", 0)
                return await self._rational_pricing(market_conditions)
            else:
                # Continue slashing - maintain rock-bottom pricing
                return await self._slash_pricing(market_conditions)

        # Not currently slashing - decide whether to start
        should_slash = await self._should_start_slashing(market_conditions)

        if should_slash:
            # Enter slash mode
            duration = self.rng.randint(*self.slash_duration_range)
            self._set_state_value("is_slashing", True)
            self._set_state_value("slash_end_tick", current_tick + duration)
            return await self._slash_pricing(market_conditions)
        else:
            # Continue rational behavior
            return await self._rational_pricing(market_conditions)

    async def _should_start_slashing(self, market_conditions: MarketConditions) -> bool:
        """
        Determine if the competitor should enter destructive slash mode.

        Factors increasing slash probability:
        - Low sales velocity (losing market share)
        - Being significantly above market average price
        - Random irrational impulses
        """
        base_probability = self.slash_probability

        # Increase probability if sales are poor
        if market_conditions.own_sales_velocity < self.low_sales_velocity_threshold:
            base_probability *= 2.0

        # Increase probability if significantly above market average
        current_price = market_conditions.current_state.price
        market_avg = market_conditions.market_average_price
        if current_price > market_avg * Decimal(str(self.market_avg_price_threshold)):
            base_probability *= 1.5

        # Cap maximum probability
        final_probability = min(base_probability, self.max_slash_probability)

        return self.rng.random() < final_probability  # Use persona's rng

    async def _slash_pricing(self, market_conditions: MarketConditions) -> CompetitorState:
        """
        Set destructively low pricing during slash mode.

        Price is set to just above cost basis, ignoring market conditions.
        """
        slash_price = self._calculate_minimum_price()

        # Create updated state with slashed price
        current_state = market_conditions.current_state

        return CompetitorState(
            asin=current_state.asin,
            price=slash_price,
            bsr=current_state.bsr,  # BSR will improve due to low price
            sales_velocity=float(
                Decimal(str(current_state.sales_velocity))
                * Decimal(str(self.slash_sales_velocity_boost))
            ),  # Boost sales
        )

    async def _rational_pricing(self, market_conditions: MarketConditions) -> CompetitorState:
        """
        Implement rational competitive pricing when not in slash mode.

        Follows market-responsive pricing similar to default behavior.
        """
        current_state = market_conditions.current_state
        market_avg = market_conditions.market_average_price

        # Price slightly below market average for competitiveness
        rational_price = market_avg * Decimal(str(self.rational_price_discount))  # returns Money

        # Ensure we don't price below cost basis
        final_price = max_money(rational_price, self._calculate_minimum_price())

        return CompetitorState(
            asin=current_state.asin,
            price=final_price,
            bsr=current_state.bsr,
            sales_velocity=float(current_state.sales_velocity),
        )


class SlowFollower(CompetitorPersona):
    """
    The Slow Market Follower Persona

    This persona represents competitors with delayed market response due to:
    - Organizational bureaucracy and slow decision-making
    - Infrequent market monitoring
    - Conservative risk management
    - Limited market intelligence resources

    Behavior Patterns:
    - Only evaluates market every 4-8 ticks (realistic lag)
    - When active, follows market trends conservatively
    - Gradual price adjustments, never dramatic changes
    - Tends to lag behind market movements
    """

    def __init__(
        self,
        competitor_id: str,
        cost_basis: Money,
        currency: str = "USD",
        evaluation_interval_range: tuple[int, int] = (4, 8),
        max_price_change_percent: Decimal = Decimal("0.10"),
        target_price_bias: Decimal = Decimal("1.02"),
        velocity_down_boost: Decimal = Decimal("1.05"),
        velocity_up_reduction: Decimal = Decimal("0.95"),
        seed: Optional[int] = None,  # Added seed
    ):
        super().__init__(competitor_id, cost_basis, currency, seed=seed)  # Pass seed to super()

        # Input validation for SlowFollower specific parameters
        if not (
            isinstance(evaluation_interval_range, tuple)
            and len(evaluation_interval_range) == 2
            and all(isinstance(i, int) for i in evaluation_interval_range)
            and evaluation_interval_range[0] <= evaluation_interval_range[1]
            and evaluation_interval_range[0] > 0
        ):
            raise ValueError(
                "evaluation_interval_range must be a tuple of two positive integers (min, max) where min <= max."
            )
        if not isinstance(max_price_change_percent, Decimal) or not (
            Decimal("0") <= max_price_change_percent <= Decimal("1")
        ):
            raise ValueError("max_price_change_percent must be a Decimal between 0 and 1.")
        if not isinstance(target_price_bias, Decimal) or target_price_bias <= 0:
            raise ValueError("target_price_bias must be a positive Decimal.")
        if not isinstance(velocity_down_boost, Decimal) or velocity_down_boost <= 0:
            raise ValueError("velocity_down_boost must be a positive Decimal.")
        if not isinstance(velocity_up_reduction, Decimal) or velocity_up_reduction <= 0:
            raise ValueError("velocity_up_reduction must be a positive Decimal.")

        self.evaluation_interval_range = evaluation_interval_range  # Ticks between evaluations
        self.max_price_change_percent = (
            max_price_change_percent  # Maximum fractional price change per evaluation
        )
        self.target_price_bias = target_price_bias  # Conservative bias above market average
        self.velocity_down_boost = (
            velocity_down_boost  # Sales velocity multiplier when price decreases
        )
        self.velocity_up_reduction = (
            velocity_up_reduction  # Sales velocity multiplier when price increases
        )

    async def act(self, market_conditions: MarketConditions) -> Optional[CompetitorState]:
        """
        Implement slow, lagged market following behavior.

        The slow follower only acts periodically and makes conservative
        adjustments when it does evaluate the market.
        """
        current_tick = market_conditions.current_tick
        last_evaluation_tick = self._get_state_value("last_evaluation_tick", 0)
        next_evaluation_tick = self._get_state_value("next_evaluation_tick", 0)

        # Initialize evaluation schedule on first run
        if next_evaluation_tick == 0:
            interval = self.rng.randint(*self.evaluation_interval_range)  # Use persona's rng
            self._set_state_value("next_evaluation_tick", current_tick + interval)
            return None  # No action on first tick

        # Check if it's time for evaluation
        if current_tick < next_evaluation_tick:
            return None  # Not time to evaluate yet

        # Time to evaluate and potentially act
        self._set_state_value("last_evaluation_tick", current_tick)

        # Schedule next evaluation
        interval = self.rng.randint(*self.evaluation_interval_range)  # Use persona's rng
        self._set_state_value("next_evaluation_tick", current_tick + interval)

        # Perform conservative market following
        return await self._conservative_market_following(market_conditions)

    async def _conservative_market_following(
        self, market_conditions: MarketConditions
    ) -> CompetitorState:
        """
        Implement conservative price adjustments following market trends.

        The slow follower makes gradual adjustments toward market conditions
        but never dramatic price changes.
        """
        current_state = market_conditions.current_state
        current_price = current_state.price
        market_avg = market_conditions.market_average_price

        # Calculate target price (market average with slight conservative bias)
        target_price = market_avg * self.target_price_bias  # returns Money

        # Calculate maximum allowed price change
        max_increase = current_price * (Decimal("1") + self.max_price_change_percent)
        max_decrease = current_price * (Decimal("1") - self.max_price_change_percent)

        # Apply conservative adjustment limits
        if target_price > current_price:
            # Trending up - gradual increase
            new_price = min_money(target_price, max_increase)
        else:
            # Trending down - gradual decrease
            new_price = max_money(target_price, max_decrease)

        # Never price below cost basis
        final_price = max_money(new_price, self._calculate_minimum_price())

        # Conservative sales velocity adjustment (slow to respond)
        velocity_adjustment = Decimal("1.0")
        if final_price < current_price:
            velocity_adjustment = self.velocity_down_boost  # Modest boost for price reduction
        elif final_price > current_price:
            velocity_adjustment = self.velocity_up_reduction  # Modest reduction for price increase

        return CompetitorState(
            asin=current_state.asin,
            price=final_price,
            bsr=current_state.bsr,
            sales_velocity=float(Decimal(str(current_state.sales_velocity)) * velocity_adjustment),
        )
