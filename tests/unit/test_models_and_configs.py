from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from money import Money

import config.model_config as mc
from agent_runners.diy_runner import DynamicPricingStrategy
from agents.advanced_agent import AdvancedAgent
from agents.hierarchical_planner import PlanType, StrategicPlanner
from agents.skill_modules.financial_analyst import (
    FinancialAnalystSkill,
    FinancialForecast,
)
from config.model_config import get_model_params


def _reset_params_cache():
    # Ensure fresh load of model params across tests
    mc._cached_params = None  # type: ignore[attr-defined]


def test_yaml_overlay_merge(tmp_path, monkeypatch):
    _reset_params_cache()
    # Create minimal override YAML
    p = tmp_path / "params.yaml"
    p.write_text(
        "\n".join(
            [
                "version: '1.0'",
                "advanced_agent:",
                "  inv_low_ratio: 0.6",
                "planner:",
                "  growth_profit_margin_gt: 0.2",
                "  strategy_refresh_days: 100",  # New parameter
                "  tactical_action_cleanup_days: 10",  # New parameter
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("MODEL_PARAMS_YAML", str(p))
    params = get_model_params(force_reload=True)
    assert pytest.approx(params.advanced_agent.inv_low_ratio, rel=0, abs=1e-9) == 0.6
    assert pytest.approx(params.planner.growth_profit_margin_gt, rel=0, abs=1e-9) == 0.2
    assert params.planner.strategy_refresh_days == 100
    assert params.planner.tactical_action_cleanup_days == 10


def test_advanced_agent_uses_central_params(tmp_path, monkeypatch):
    _reset_params_cache()
    # Override a couple of AdvancedAgent parameters via YAML
    p = tmp_path / "agent_params.yaml"
    p.write_text(
        "\n".join(
            [
                "version: '1.0'",
                "advanced_agent:",
                "  undercut: 0.02",
                "  inv_low_ratio: 0.55",
                "  inv_low_nudge: 0.25",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("MODEL_PARAMS_YAML", str(p))
    get_model_params(force_reload=True)  # set cache from YAML

    agent = AdvancedAgent(config={"parameters": {}})
    # undercut picked from YAML defaults (no per-agent override supplied)
    assert pytest.approx(agent.undercut, rel=0, abs=1e-12) == 0.02

    # Inventory factor should follow configured thresholds/nudges
    # inventory_ratio below inv_low_ratio => inv_low_nudge
    factor = agent._compute_inventory_factor(0.54)  # just below 0.55
    assert pytest.approx(factor, rel=0, abs=1e-9) == agent._mp.inv_low_nudge

    # Test confidence calculation with various inputs
    # Mock parameters for DIYRunner methods
    mp_adv = get_model_params().advanced_agent

    # Create a mock DIYRunner instance for testing its methods separately
    mock_diy_runner = agent_runners.diy_runner.DIYRunner(
        agent_id="test_agent", config={}
    )
    mock_diy_runner._do_initialize()  # Initialize its internal config and strategy

    # Test cases for _calculate_confidence
    product_data = {
        "cost": 100,
        "current_price": 120,
        "sales_rank": 500,
        "inventory": 50,
    }
    market_data = {"market_demand": 1.5, "competitor_prices": [110, 125, 130]}

    # Expect high confidence with good data
    confidence = mock_diy_runner._calculate_confidence(product_data, market_data)
    expected_confidence_with_data = (
        0.5
        + 4 * mp_adv.confidence_product_data_boost
        + 2 * mp_adv.confidence_market_data_boost_per_item
    )
    assert pytest.approx(confidence, rel=0, abs=1e-9) == min(
        expected_confidence_with_data, mp_adv.confidence_max_cap
    )

    # Expect lower confidence with sparse data
    sparse_product_data = {"cost": 0, "current_price": 0}
    sparse_market_data = {"market_demand": 0, "competitor_prices": []}
    confidence_sparse = mock_diy_runner._calculate_confidence(
        sparse_product_data, sparse_market_data
    )
    expected_confidence_sparse_data = 0.5  # Base confidence only
    assert pytest.approx(confidence_sparse, rel=0, abs=1e-9) == min(
        expected_confidence_sparse_data, mp_adv.confidence_max_cap
    )  # Should still respect cap

    # Test _generate_reasoning logic
    product_for_reasoning = {
        "asin": "TEST-REASONING",
        "cost": 50.0,
        "current_price": 60.0,
        "sales_rank": 5000,  # High demand
        "inventory": 5,  # Low inventory
    }
    market_for_reasoning = {
        "market_demand": 1.3,  # High market demand
        "competitor_prices": [58.0, 62.0, 65.0],
    }
    new_price_for_reasoning = 61.0

    reasoning = mock_diy_runner._generate_reasoning(
        product_for_reasoning, market_for_reasoning, new_price_for_reasoning
    )

    # Assertions for relevant parts of the reasoning string
    assert "High demand product (rank 5000)." in reasoning
    assert "Low inventory (5 units)." in reasoning
    assert "High market demand." in reasoning
    # Corrected assertion: new_price 61.0 is below avg_competitor_price 61.67, but the deviation
    # (0.01) is less than the threshold (0.1), so it should not trigger "Priced below competitors"
    assert "Priced below competitors (avg $61.67)." not in reasoning
    assert "Priced above competitors (avg $61.67)." not in reasoning
    assert f"Calculated price ${new_price_for_reasoning:.2f}" in reasoning

    # Test edge cases or specific scenarios for reasoning
    product_sparse = {"asin": "SPARSE", "cost": 0, "current_price": 0}
    market_sparse = {"market_demand": 0.5, "competitor_prices": []}
    new_price_sparse = 10.0
    reasoning_sparse = mock_diy_runner._generate_reasoning(
        product_sparse, market_sparse, new_price_sparse
    )
    assert (
        "Cost: $0.00, Margin: 0.0%" in reasoning_sparse
    )  # Test default margin when cost is 0
    assert "Low market demand." in reasoning_sparse  # Default market demand logic
    assert "Priced above competitors" not in reasoning_sparse  # No competitors


@pytest.mark.asyncio
async def test_financial_forecast_ma_fallback(monkeypatch):
    # Force MA fallback by disabling Holt-Winters
    import agents.skill_modules.financial_analyst as fa_mod

    monkeypatch.setattr(fa_mod, "ExponentialSmoothing", None, raising=False)

    skill = FinancialAnalystSkill(agent_id="A1", event_bus=None, config={})
    # Seed revenue history (simulate 10 daily sales)
    now = datetime.now()
    for i in range(10):
        skill.revenue_history.append(
            {
                "timestamp": now - timedelta(days=9 - i),
                "revenue": Money(1500 + i * 100),  # $15.00 + incremental
                "profit": Money(500 + i * 50),
                "asin": "X",
                "units": 1,
            }
        )
    # Seed expense history for burn rate
    for i in range(7):
        skill.expense_history.append(
            {
                "timestamp": now - timedelta(days=6 - i),
                "amount": 200,  # $2.00 per day
                "category": "ops",
                "description": "daily cost",
            }
        )

    forecast = await skill._generate_financial_forecast("7_days")
    assert isinstance(forecast, FinancialForecast)
    assert forecast.revenue_projection.cents > 0
    assert forecast.expense_projection.cents > 0
    assert (
        forecast.profit_projection.cents
        == forecast.revenue_projection.cents - forecast.expense_projection.cents
    )
    assert 0.0 < forecast.confidence_level <= 0.99


@pytest.mark.asyncio
async def test_financial_analyst_skill_params(tmp_path, monkeypatch):
    _reset_params_cache()
    # Override FinancialAnalystParams via YAML
    p = tmp_path / "fa_params.yaml"
    p.write_text(
        "\n".join(
            [
                "version: '1.0'",
                "financial_analyst:",
                "  default_burn_rate_cents: 50",  # Default $0.50 per day
                "  burn_rate_history_window: 5",
                "  margin_score_weight: 0.5",
                "  runway_score_weight: 0.3",
                "  burn_score_weight: 0.2",
                "  target_cash_runway_days: 60",
                "  max_reallocation_cents: 5000",  # $50 max reallocation
                "  default_cost_reduction_target: 0.1",  # 10% reduction
                "  max_investment_cents: 100000",  # $1000 max investment
                "  default_expected_roi: 2.0",  # 200% ROI
                "  default_investment_risk_level: 'high'",
                "  low_profit_margin_threshold: 0.05",  # 5% margin
                "  high_fee_percentage_threshold: 0.30",  # 30% fees
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("MODEL_PARAMS_YAML", str(p))
    params = get_model_params(force_reload=True)
    fa_p = params.financial_analyst

    skill = FinancialAnalystSkill(agent_id="FA1", event_bus=None, config={})

    # Test _calculate_burn_rate
    now = datetime.now()
    for i in range(
        fa_p.burn_rate_history_window + 2
    ):  # Enough history plus a bit extra
        skill.expense_history.append(
            {
                "timestamp": now - timedelta(days=i),
                "amount": 300,
                "category": "ops",
                "description": "some cost",
            }
        )
    burn_rate = skill._calculate_burn_rate()
    assert burn_rate.cents == 300  # Should average to 300

    # Test _calculate_financial_health_score
    skill.current_cash = Money(fa_p.min_cash_reserve_cents * 2)  # Healthy cash level
    skill.total_revenue = Money(100000)
    skill.total_expenses = Money(50000)
    profit_margin = skill._calculate_profit_margin()  # Should be 0.5
    cash_runway = skill._calculate_cash_runway()  # Depends on burn_rate

    health_score = skill._calculate_financial_health_score(
        profit_margin, cash_runway, burn_rate
    )
    # Expected score calculation:
    # margin_score = min(0.5, max(0.0, 0.5 * (0.5 / 0.2))) = min(0.5, 1.25) = 0.5
    # runway_score = min(0.3, runway_days(approx 600 days from current_cash/burn_rate) / 60 * 0.3) = 0.3
    # burn_score = if total_revenue > 0: 1.0 - min(1.0, (300 * 30)/100000) = 1.0 - 0.09 = 0.91 * 0.2 = 0.182
    # total_score = 0.5 + 0.3 + 0.182 = 0.982
    assert 0.9 <= health_score <= 1.0  # Approximate check

    # Test _create_budget_reallocation_action
    skill.budget_allocations[mc.ExpenseCategory.INVENTORY].utilization_rate = (
        0.5  # Underutilized
    )
    skill.budget_allocations[mc.ExpenseCategory.INVENTORY].remaining_amount = Money(
        200000
    )
    skill.budget_allocations[mc.ExpenseCategory.MARKETING].utilization_rate = (
        0.95  # Overutilized
    )
    financial_state = {"cash_position": "warning"}
    realloc_action = await skill._create_budget_reallocation_action(financial_state)
    assert realloc_action is not None
    assert realloc_action.parameters["reallocation_amount"] == min(
        fa_p.max_reallocation_cents, 100000
    )  # (200000 // 2)

    # Test _generate_cost_reduction_actions
    cost_reduction_actions = await skill._generate_cost_reduction_actions({})
    assert len(cost_reduction_actions) == 1
    assert (
        pytest.approx(
            cost_reduction_actions[0].parameters["reduction_target"], rel=0, abs=1e-9
        )
        == fa_p.default_cost_reduction_target
    )
    expected_savings = skill.total_expenses.cents * fa_p.default_cost_reduction_target
    assert (
        pytest.approx(
            cost_reduction_actions[0].expected_outcome["monthly_savings"],
            rel=0,
            abs=1e-9,
        )
        == expected_savings
    )

    # Test _generate_investment_recommendations
    skill.current_cash = Money(fa_p.min_cash_reserve_cents * 4)  # Ensure enough cash
    investment_actions = await skill._generate_investment_recommendations(
        SimpleNamespace(), {}
    )  # Empty context/constraints
    assert len(investment_actions) == 1
    assert investment_actions[0].parameters["investment_amount"] == min(
        fa_p.max_investment_cents,
        (skill.current_cash.cents - fa_p.min_cash_reserve_cents) // 2,
    )
    assert (
        pytest.approx(investment_actions[0].parameters["expected_roi"], rel=0, abs=1e-9)
        == fa_p.default_expected_roi
    )
    assert (
        investment_actions[0].parameters["risk_level"]
        == fa_p.default_investment_risk_level
    )

    # Test _analyze_profitability
    sale_low_margin = SimpleNamespace(
        asin="PROFIT-LOW",
        total_revenue=Money(100000),
        total_profit=Money(4000),
        units_sold=10,
        total_fees=Money(0),
    )
    profit_action = await skill._analyze_profitability(sale_low_margin)
    assert profit_action is not None
    assert (
        pytest.approx(profit_action.parameters["profit_margin"], rel=0, abs=1e-9)
        == 0.04
    )
    assert (
        pytest.approx(profit_action.parameters["profit_margin"], rel=0, abs=1e-9)
        < fa_p.low_profit_margin_threshold
    )

    # Test _analyze_fee_impact
    sale_high_fees = SimpleNamespace(
        asin="FEES-HIGH",
        total_revenue=Money(100000),
        total_profit=Money(10000),
        units_sold=10,
        total_fees=Money(35000),
    )
    fee_action = await skill._analyze_fee_impact(sale_high_fees)
    assert fee_action is not None
    assert (
        pytest.approx(fee_action.parameters["fee_percentage"], rel=0, abs=1e-9) == 0.35
    )
    assert (
        pytest.approx(fee_action.parameters["fee_percentage"], rel=0, abs=1e-9)
        > fa_p.high_fee_percentage_threshold
    )


def test_dynamic_pricing_elasticity_and_history(tmp_path, monkeypatch):
    _reset_params_cache()
    # Ensure defaults loaded and get pricing parameters
    pp = get_model_params(force_reload=True).pricing

    # Instantiate DynamicPricingStrategy with an agent_id
    strat = DynamicPricingStrategy(agent_id="test_agent")

    product = {
        "asin": "ASIN-ELAS",
        "cost": 10.0,
        "current_price": 12.0,
        "inventory": int(pp.high_inventory_threshold),
        "sales_rank": 200000,
    }
    # Synthetic data: as price rises, sales drop -> negative elasticity
    market = {
        "market_demand": 1.0,
        "seasonality": 1.0,
        "recent_prices": [10, 12, 14, 16, 18, 20],
        "recent_sales": [100, 80, 65, 55, 47, 40],
    }

    price = strat.calculate_price(product, market)
    # Must respect minimum margin over cost
    min_price = product["cost"] * (1.0 + pp.minimum_margin_over_cost)
    assert price >= pytest.approx(min_price, rel=1e-6)

    # History should be capped by window
    for _ in range(int(pp.price_history_window) + 5):
        _ = strat.calculate_price(product, market)
    assert len(strat.price_history[product["asin"]]) == int(pp.price_history_window)


@pytest.mark.asyncio
async def test_planner_strategy_and_cleanup(monkeypatch):
    _reset_params_cache()
    # Force overrides for planner parameters
    override = dict(
        planner=dict(
            recovery_profit_margin_lt=0.50,
            recovery_revenue_growth_lt=0.50,
            defensive_competitive_pressure_gt=0.90,
            growth_revenue_growth_gt=0.90,
            growth_profit_margin_gt=0.90,
            exploratory_volatility_gt=0.90,
            strategy_refresh_days=1,  # Refresh every day for testing
            tactical_action_cleanup_days=1,  # Cleanup every day for testing
        )
    )
    merged_params = get_model_params(force_reload=True, override=override)
    planner_skill = StrategicPlanner(
        agent_id="P1", event_bus=None
    )  # Pass in real event_bus if available
    planner_skill._planner_params = (
        merged_params.planner
    )  # Ensure the planner skill uses the overridden params

    # Test _determine_strategy_type (already partially covered by original, but re-run for safety)
    context_recovery = {
        "current_metrics": {"profit_margin": 0.10, "revenue_growth": 0.10},
        "market_conditions": {"competitive_pressure": 0.4, "volatility": 0.2},
    }
    chosen_strategy = planner_skill._determine_strategy_type(context_recovery)
    assert chosen_strategy == PlanType.RECOVERY

    # Test _should_create_new_strategy
    # Should create new strategy if not created yet
    assert planner_skill._should_create_new_strategy(datetime.now(), PlanType.GROWTH)

    # After creation, should not create new immediately
    planner_skill.strategy_created_at = datetime.now()
    planner_skill.current_strategy_type = PlanType.OPTIMIZATION
    assert not planner_skill._should_create_new_strategy(
        datetime.now(), PlanType.OPTIMIZATION
    )

    # Should create new after refresh days
    old_time = datetime.now() - timedelta(
        days=planner_skill._planner_params.strategy_refresh_days + 1
    )
    planner_skill.strategy_created_at = old_time
    assert planner_skill._should_create_new_strategy(
        datetime.now(), PlanType.OPTIMIZATION
    )

    # Test _archive_completed_objectives and _cleanup_old_actions logic (requires more direct manipulation)
    # Create some dummy objectives and actions for testing cleanup
    obj_id1 = "obj1"
    obj_id2 = "obj2"

    # Mock some objectives
    planner_skill.strategic_objectives[obj_id1] = mc.StrategicObjective(  # type: ignore
        objective_id=obj_id1,
        title="Test Objective 1",
        description="Desc",
        target_metrics={},
        timeframe_days=10,
        priority=mc.PlanPriority.LOW,  # type: ignore
        status=mc.PlanStatus.COMPLETED,  # type: ignore
        created_at=datetime.now() - timedelta(days=5),
        target_completion=datetime.now() + timedelta(days=5),
    )
    planner_skill.strategic_objectives[obj_id2] = mc.StrategicObjective(  # type: ignore
        objective_id=obj_id2,
        title="Test Objective 2",
        description="Desc",
        target_metrics={},
        timeframe_days=10,
        priority=mc.PlanPriority.LOW,  # type: ignore
        status=mc.PlanStatus.ACTIVE,  # type: ignore
        created_at=datetime.now() - timedelta(minutes=30),
        target_completion=datetime.now() + timedelta(days=5),
    )

    # Mock some tactical actions
    action_id1 = "act1"
    action_id2 = "act2"

    mock_tactical_planner = SimpleNamespace(
        tactical_actions={
            action_id1: mc.TacticalAction(  # type: ignore
                action_id=action_id1,
                title="Action 1",
                description="Desc",
                action_type="type",
                parameters={},
                strategic_objective_id=obj_id1,
                priority=mc.PlanPriority.LOW,
                status=mc.PlanStatus.COMPLETED,
                created_at=datetime.now() - timedelta(days=2),
                scheduled_execution=datetime.now() - timedelta(days=2),
                estimated_duration_hours=1.0,
                expected_impact={},
            ),
            action_id2: mc.TacticalAction(  # type: ignore
                action_id=action_id2,
                title="Action 2",
                description="Desc",
                action_type="type",
                parameters={},
                strategic_objective_id=obj_id2,
                priority=mc.PlanPriority.LOW,
                status=mc.PlanStatus.ACTIVE,
                created_at=datetime.now() - timedelta(minutes=10),
                scheduled_execution=datetime.now() + timedelta(hours=1),
                estimated_duration_hours=1.0,
                expected_impact={},
            ),
        },
        _planner_params=merged_params.planner,  # Use the overridden planner params
    )

    # Test _archive_completed_objectives
    initial_objective_count = len(planner_skill.strategic_objectives)
    initial_archived_count = len(planner_skill.archived_objectives)

    await planner_skill._archive_completed_objectives()

    assert (
        len(planner_skill.strategic_objectives) == initial_objective_count - 1
    )  # One completed objective removed
    assert (
        len(planner_skill.archived_objectives) == initial_archived_count + 1
    )  # One objective archived
    assert obj_id1 not in planner_skill.strategic_objectives
    assert planner_skill.archived_objectives[0].objective_id == obj_id1

    # Test _cleanup_old_actions
    initial_action_count = len(mock_tactical_planner.tactical_actions)
    await mock_tactical_planner._cleanup_old_actions()

    # Action 1 was created 2 days ago, well past 1 day cleanup threshold
    assert len(mock_tactical_planner.tactical_actions) == initial_action_count - 1
    assert action_id1 not in mock_tactical_planner.tactical_actions
    assert (
        action_id2 in mock_tactical_planner.tactical_actions
    )  # Action 2 is still active and recent
