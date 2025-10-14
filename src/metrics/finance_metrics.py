# metrics/finance_metrics.py
import logging
import statistics  # Added for mean/stdev calculations
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol

import numpy as np

from fba_events import BaseEvent, PurchaseOccurred, SaleOccurred  # Explicitly import event types
from money import Money  # Assuming Money class is correctly implemented

logger = logging.getLogger(__name__)


# --- Abstract Service Interfaces (from metric_suite.py or a shared contracts module) ---
# Defining them here for self-containment, but ideally imported.
class AbstractFinancialAuditService(Protocol):
    """Protocol for a financial audit service."""

    def get_current_net_worth(self) -> Money:
        ...

    def get_current_cash_flow(self) -> Money:
        ...  # Assuming this method exists

    def get_violations(self) -> List[Any]:
        ...

    def get_status_summary(self) -> Dict[str, Any]:
        ...


@dataclass
class FinanceMetricsConfig:
    """Configurable parameters for FinanceMetrics."""

    risk_free_rate: float = 0.01  # Annualized risk-free rate for Sharpe Ratio
    sharpe_ratio_min_returns: int = 2  # Minimum returns needed for Sharpe Ratio calculation
    cash_flow_stability_epsilon: float = 1e-9  # Small value to prevent division by zero
    resilience_recovery_threshold: float = 0.5  # Percentage recovery target


@dataclass
class ShockNetWorthSnapshot:
    """Stores net worth snapshots around a shock event."""

    before_shock: Optional[Money] = None
    during_shock: Optional[Money] = None
    after_shock: Optional[Money] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if self.before_shock:
            data["before_shock"] = (
                self.before_shock.to_dict()
                if hasattr(self.before_shock, "to_dict")
                else str(self.before_shock)
            )
        if self.during_shock:
            data["during_shock"] = (
                self.during_shock.to_dict()
                if hasattr(self.during_shock, "to_dict")
                else str(self.during_shock)
            )
        if self.after_shock:
            data["after_shock"] = (
                self.after_shock.to_dict()
                if hasattr(self.after_shock, "to_dict")
                else str(self.after_shock)
            )
        return data


class FinanceMetrics:
    """
    Tracks and calculates financial performance metrics for an agent.
    Integrates with a FinancialAuditService for core financial data.
    """

    def __init__(
        self,
        financial_audit_service: Optional[AbstractFinancialAuditService] = None,
        config: Optional[FinanceMetricsConfig] = None,
    ):
        if financial_audit_service is not None and not isinstance(
            financial_audit_service, AbstractFinancialAuditService
        ):
            raise TypeError(
                "financial_audit_service must implement AbstractFinancialAuditService protocol."
            )
        self.financial_audit_service: Optional[
            AbstractFinancialAuditService
        ] = financial_audit_service
        self.config = config if config else FinanceMetricsConfig()

        self.net_worth_history: List[Money] = []  # Stores Money objects
        self.cash_flow_history: List[Money] = []  # Stores Money objects
        self.shock_net_worth_snapshots: Dict[
            str, ShockNetWorthSnapshot
        ] = {}  # shock_id: ShockNetWorthSnapshot

        # Unit-test compatibility: lightweight metric registry
        self._metrics: Dict[str, Any] = {}

        self._last_update_tick: int = -1
        self._last_update_time: Optional[datetime] = None

        logger.info("FinanceMetrics initialized.")

    def update(self, current_tick: int, events: List[BaseEvent]) -> None:
        """
        Updates financial metrics based on new events from the simulation.
        Processes events to derive cash flow and pulls net worth from the audit service.
        """
        if current_tick <= self._last_update_tick:
            logger.debug(f"FinanceMetrics already updated for tick {current_tick}.")
            return

        # Always get current net worth from audit service
        current_net_worth = self.financial_audit_service.get_current_net_worth()
        self.net_worth_history.append(current_net_worth)

        # Compute cash flow primarily from audit service, fallback to event-based calculation
        current_cash_flow = self.financial_audit_service.get_current_cash_flow()
        if (
            current_cash_flow is None
        ):  # Fallback if audit service doesn't provide real-time cash flow
            current_cash_flow = self._compute_cash_flow_from_events(events)

        self.cash_flow_history.append(current_cash_flow)

        self._last_update_tick = current_tick
        self._last_update_time = datetime.now()
        logger.debug(
            f"FinanceMetrics updated for tick {current_tick}. Net worth: {current_net_worth}, Cash flow: {current_cash_flow}"
        )

    def record_shock_snapshot(self, shock_id: str, phase: str) -> None:
        """
        Records snapshots of net worth before, during, and after a shock event.
        Args:
            shock_id: Unique identifier for the shock event.
            phase: The phase of the shock ("before", "during", "after").
        """
        current_net_worth = self.financial_audit_service.get_current_net_worth()

        # Ensure Money objects are consistent
        if not isinstance(current_net_worth, Money):
            logger.warning(
                f"Financial audit service returned non-Money type for net worth: {type(current_net_worth)}"
            )
            current_net_worth = Money.from_dollars(current_net_worth, "USD")  # Attempt conversion

        if shock_id not in self.shock_net_worth_snapshots:
            self.shock_net_worth_snapshots[shock_id] = ShockNetWorthSnapshot()

        snapshot = self.shock_net_worth_snapshots[shock_id]

        if phase == "before":
            snapshot.before_shock = current_net_worth
        elif phase == "during":
            snapshot.during_shock = current_net_worth
        elif phase == "after":
            snapshot.after_shock = current_net_worth
        else:
            logger.warning(
                f"Unknown shock phase '{phase}' for shock_id '{shock_id}'. Snapshot not recorded."
            )

        logger.debug(f"Recorded shock snapshot for {shock_id} ({phase}): {current_net_worth}")

    def calculate_resilient_net_worth(self) -> float:
        """
        Calculates a resilience score based on net worth recovery after a shock.
        Returns a percentage (0-100), where 100 means full or over-recovery.
        """
        resilience_scores: List[float] = []
        for shock_id, snapshot in self.shock_net_worth_snapshots.items():
            if snapshot.before_shock and snapshot.during_shock and snapshot.after_shock:
                before = snapshot.before_shock.to_decimal()
                during = snapshot.during_shock.to_decimal()
                after = snapshot.after_shock.to_decimal()

                if before > 0:
                    # Calculate drop during shock and subsequent recovery from that drop
                    drop = before - during
                    recovery = after - during

                    if drop > 0:  # Only if there was an actual drop
                        resilience_score = recovery / drop
                        resilience_scores.append(float(resilience_score))
                    else:  # No drop, or net worth increased during shock - consider fully resilient
                        resilience_scores.append(1.0)
                else:  # Cannot calculate if before_shock is zero or negative
                    resilience_scores.append(0.0)  # Assume no resilience if no baseline

            elif (
                snapshot.before_shock
                and snapshot.before_shock.to_decimal() > 0
                and snapshot.during_shock
            ):
                # Partial data: if shock ongoing, can't measure full recovery yet.
                # Just indicate current state relative to before.
                before = snapshot.before_shock.to_decimal()
                during = snapshot.during_shock.to_decimal()
                if before > 0:
                    resilience_scores.append(float(during / before))
                else:
                    resilience_scores.append(0.0)
            else:
                logger.debug(
                    f"Insufficient data for shock_id '{shock_id}' to calculate resilience."
                )

        if not resilience_scores:
            return (
                100.0 if self.net_worth_history else 0.0
            )  # If no shocks, assume perfect recovery, or 0 if no net worth data

        # Average all resilience scores, cap at 1.0 (100% recovery) and convert to percentage
        return float(np.mean([min(1.0, s) for s in resilience_scores]) * 100)

    def calculate_sharpe_ratio(self) -> float:
        """
        Calculates the Sharpe Ratio for the agent's financial performance.
        Includes robust handling for insufficient data and zero standard deviation.
        """
        returns: List[float] = []
        for i in range(1, len(self.net_worth_history)):
            current_nw = self.net_worth_history[i].to_decimal()
            previous_nw = self.net_worth_history[i - 1].to_decimal()
            if previous_nw != 0:
                returns.append(float((current_nw - previous_nw) / previous_nw))
            else:
                returns.append(0.0)  # Cannot calculate return from zero, treat as 0% for now

        if len(returns) < self.config.sharpe_ratio_min_returns:
            logger.debug(
                f"Insufficient returns data ({len(returns)}) for Sharpe Ratio, need at least {self.config.sharpe_ratio_min_returns}."
            )
            return 0.0  # Not enough data for meaningful ratio

        returns_np = np.array(returns)
        excess_returns = returns_np - self.config.risk_free_rate  # Use configurable risk_free_rate

        std_dev_excess_returns = np.std(excess_returns)

        if std_dev_excess_returns != 0:
            return float(np.mean(excess_returns) / std_dev_excess_returns)
        else:
            return 0.0  # Avoid ZeroDivisionError if returns are constant

    def calculate_drawdown_recovery(self) -> float:
        """
        Calculates the agent's ability to recover from financial drawdowns.
        Returns a recovery percentage (0-100).
        """
        if not self.net_worth_history:
            return 0.0  # No net worth history, no recovery to calculate

        net_worth_decimals = [nw.to_decimal() for nw in self.net_worth_history]

        peak = net_worth_decimals[0]
        max_drawdown = Money(0, "USD").to_decimal()
        current_drawdown = Money(0, "USD").to_decimal()

        for nw in net_worth_decimals:
            if nw > peak:
                peak = nw
            current_drawdown = max(current_drawdown, peak - nw)
            max_drawdown = max(max_drawdown, current_drawdown)

        if max_drawdown == 0:
            return 100.0  # No drawdown occurred, perfect recovery

        # Simple recovery measure: (End_Net_worth - (Peak - Max_Drawdown)) / Max_Drawdown
        # More robust: time to recover to previous peak.

        # To calculate the "recovery from max drawdown", we need to know the value at the lowest point
        # and the subsequent highest point. For simplicity, if a drawdown occurred, a placeholder.
        # This metric is often time to new peak, so a simpler version is harder without more data.

        # A simple placeholder for "recovery rate" can be inverse of max drawdown
        return float((1 - max_drawdown / peak) * 100) if peak > 0 else 0.0

    def _compute_cash_flow_from_events(self, events: List[BaseEvent]) -> Money:
        """
        Computes cash flow from a list of BaseEvent objects.
        This is a fallback if the audit service does not provide real-time cash flow.
        """
        cash_in = Money(0, "USD")
        cash_out = Money(0, "USD")

        for e in events:
            if isinstance(e, SaleOccurred):
                # Assuming SaleOccurred has `unit_price` (Money) and `units_sold` (int)
                if isinstance(e.unit_price, Money) and isinstance(e.units_sold, int):
                    cash_in += e.unit_price * e.units_sold
                else:
                    logger.warning(
                        f"SaleOccurred event {e.event_id} has unexpected unit_price or units_sold type."
                    )
            elif isinstance(e, PurchaseOccurred):
                # Assuming PurchaseOccurred has `unit_cost` (Money) and `quantity` (int)
                if isinstance(e.unit_cost, Money) and isinstance(e.quantity, int):
                    cash_out += e.unit_cost * e.quantity
                else:
                    logger.warning(
                        f"PurchaseOccurred event {e.event_id} has unexpected unit_cost or quantity type."
                    )
            # Add other cash flow related events as necessary

        return cash_in - cash_out

    def calculate_cash_flow_stability(self) -> float:
        """
        Calculates cash flow stability based on the standard deviation of historical cash flows.
        A higher value indicates greater stability (lower standard deviation).
        """
        if len(self.cash_flow_history) < 2:
            return 0.0  # Not enough data for std dev

        # Convert Money history to Decimal values for calculation
        cash_flow_decimals = [cf.to_decimal() for cf in self.cash_flow_history]

        std_dev_cash_flow = statistics.pstdev(
            cash_flow_decimals
        )  # Population std dev for whole history

        # Ensure float conversion for return type
        if std_dev_cash_flow <= self.config.cash_flow_stability_epsilon:  # Use configurable epsilon
            return float(
                1.0 / self.config.cash_flow_stability_epsilon
            )  # Very high stability if near zero std dev
        else:
            return float(1.0 / std_dev_cash_flow)  # Inverse of std dev for stability score

    def get_metrics_breakdown(self) -> Dict[str, Any]:
        """
        Calculates and returns a detailed breakdown of all financial metrics.
        Returns a dictionary with metric names and their calculated float values.
        """
        resilient_net_worth = self.calculate_resilient_net_worth()
        sharpe_ratio = self.calculate_sharpe_ratio()
        drawdown_recovery = self.calculate_drawdown_recovery()
        cash_flow_stability = self.calculate_cash_flow_stability()

        # Pull audit violations directly
        audit_violations = self.financial_audit_service.get_violations()

        return {
            "overall_score": (
                resilient_net_worth * 0.3
                + sharpe_ratio * 0.2
                + drawdown_recovery * 0.3
                + cash_flow_stability * 0.2
            ),  # Example composite score
            "resilient_net_worth": resilient_net_worth,
            "sharpe_ratio": sharpe_ratio,
            "drawdown_recovery": drawdown_recovery,
            "cash_flow_stability": cash_flow_stability,
            "audit_violations_count": len(audit_violations),
        }

    def get_violations(self) -> List[Any]:
        """Pass-through method to get financial audit violations from the audit service."""
        return self.financial_audit_service.get_violations()

    def get_status_summary(self) -> Dict[str, Any]:
        """Provides a summary of the current state of the FinanceMetrics module."""
        return {
            "last_update_tick": self._last_update_tick,
            "net_worth_history_length": len(self.net_worth_history),
            "cash_flow_history_length": len(self.cash_flow_history),
            "num_shock_snapshots": len(self.shock_net_worth_snapshots),
            "config": asdict(self.config),
        }

    def reset_metrics(self) -> None:
        """Resets all metrics history for a new simulation run."""
        self.net_worth_history.clear()
        self.cash_flow_history.clear()
        self.shock_net_worth_snapshots.clear()
        self._last_update_tick = -1
        self._last_update_time = None

        logger.info("FinanceMetrics reset successfully.")

    # ---- Unit-test compatible calculation helpers (dict-based) ----
    def calculate_profit_margin(self, data: Dict[str, float]) -> float:
        revenue = float(data.get("revenue", 0.0))
        cost = float(data.get("cost", 0.0))
        return ((revenue - cost) / revenue) if revenue > 0 else 0.0

    def calculate_return_on_investment(self, data: Dict[str, float]) -> float:
        gain = float(data.get("gain", 0.0))
        cost = float(data.get("cost", 0.0))
        return gain / cost if cost > 0 else 0.0

    def calculate_break_even_point(self, data: Dict[str, float]) -> float:
        fixed_costs = float(data.get("fixed_costs", 0.0))
        price_per_unit = float(data.get("price_per_unit", 0.0))
        variable_cost_per_unit = float(data.get("variable_cost_per_unit", 0.0))
        contribution_margin = price_per_unit - variable_cost_per_unit
        return fixed_costs / contribution_margin if contribution_margin > 0 else 0.0

    def calculate_cash_flow(self, data: Dict[str, float]) -> float:
        cash_inflows = float(data.get("cash_inflows", 0.0))
        cash_outflows = float(data.get("cash_outflows", 0.0))
        return cash_inflows - cash_outflows

    def calculate_working_capital(self, data: Dict[str, float]) -> float:
        assets = float(data.get("current_assets", 0.0))
        liabilities = float(data.get("current_liabilities", 0.0))
        return assets - liabilities

    def generate_finance_report(self, data: Dict[str, float]) -> Dict[str, float]:
        profit_margin = self.calculate_profit_margin(data)
        roi = self.calculate_return_on_investment(data)
        break_even = self.calculate_break_even_point(data)
        cash_flow = self.calculate_cash_flow(data)
        working_capital = self.calculate_working_capital(data)
        return {
            "profit_margin": profit_margin,
            "return_on_investment": roi,
            "break_even_point": break_even,
            "cash_flow": cash_flow,
            "working_capital": working_capital,
        }
