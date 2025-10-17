import asyncio
from datetime import datetime

import pytest
from money import Money
from services.supply_chain_service import SupplyChainService
from services.world_store import WorldStore, set_world_store

from agents.multi_domain_controller import MultiDomainController
from agents.skill_coordinator import SkillCoordinator
from agents.skill_modules.base_skill import SkillAction
from agents.skill_modules.product_sourcing import ProductSourcingSkill
from event_bus import get_event_bus, set_event_bus
from fba_events.supplier import PlaceOrderCommand
from fba_events.time_events import TickEvent


@pytest.mark.asyncio
async def test_product_sourcing_end_to_end_place_order_to_inventory_update():
    """
    End-to-end sourcing pipeline:

    - Initialize EventBus and start recording
    - Initialize WorldStore and SupplyChainService; load supplier_catalog into WorldStore
    - Create SkillCoordinator + MultiDomainController + register ProductSourcingSkill
    - Dispatch an early TickEvent (tick 0) to generate place_order SkillAction
    - CEO arbitration approves it
    - Execute by publishing PlaceOrderCommand on EventBus
    - Advance ticks to trigger SupplyChainService delivery
    - Assert inventory increased for sourced ASIN
    """
    # Setup EventBus (use process-local in-memory singleton)
    bus = get_event_bus()
    await bus.start()
    bus.start_recording()
    set_event_bus(bus)

    # Setup WorldStore
    ws = WorldStore(event_bus=bus)
    await ws.start()
    # Register as the global WorldStore so ProductSourcingSkill can access the supplier catalog
    set_world_store(ws)
    # Ensure ProductSourcingSkill resolves the exact world store instance used in this test
    # by overriding the imported getter inside the module namespace.
    from agents.skill_modules import product_sourcing as _ps  # type: ignore

    _ps.get_world_store = lambda: ws  # type: ignore[assignment]

    # Load a minimal supplier catalog into WorldStore (matches ProductSourcingSkill expectations)
    supplier_catalog = {
        "premium_gadgets_inc": {
            "supplier_id": "premium_gadgets_inc",
            "product_id": "PG-001",
            "product_name": "Premium Gadget",
            "unit_cost": 2.50,  # $2.50/unit
            "lead_time": 1,  # 1 tick
            "reliability": 0.95,
        },
        "value_basics_llc": {
            "supplier_id": "value_basics_llc",
            "product_id": "VB-101",
            "product_name": "Value Widget",
            "unit_cost": 2.60,
            "lead_time": 2,
            "reliability": 0.90,
        },
    }
    # WorldStore has helper to set the catalog
    ws.set_supplier_catalog(supplier_catalog)

    # Ensure product state exists prior to arrival to measure delta; initialize with zero inventory
    asin = "PG-001"
    if not ws.get_product_state(asin):
        ws.initialize_product(asin, Money.from_dollars("9.99"), initial_inventory=0)

    # Setup SupplyChainService (subscribes to PlaceOrderCommand & TickEvent)
    supply = SupplyChainService(world_store=ws, event_bus=bus, base_lead_time=1)
    await supply.start()

    # Coordinator + Controller
    agent_id = "agent-greenfield"
    coordinator = SkillCoordinator(agent_id=agent_id, event_bus=bus, config={})
    controller = MultiDomainController(
        agent_id=agent_id,
        skill_coordinator=coordinator,
        config={
            "total_budget_cents": 50_00  # $50 budget headroom for arbitration even if not used here
        },
    )

    # Register ProductSourcingSkill for TickEvent
    sourcing = ProductSourcingSkill(
        agent_id=agent_id,
        event_bus=bus,
        config={
            "initial_investment_cents": 25_00,  # $25
            "investment_ratio": 0.80,  # invest $20
            "max_units_cap": 1000,
        },
    )
    ok = await coordinator.register_skill(
        sourcing, sourcing.get_supported_event_types(), priority_multiplier=1.0
    )
    assert ok, "Failed to register ProductSourcingSkill"

    # Record initial inventory
    inv_before = ws.get_product_inventory_quantity(asin)

    # Dispatch early tick to generate SkillAction
    t0 = TickEvent(
        event_id="tick_0_test",
        timestamp=datetime.now(),
        tick_number=0,
        simulation_time=datetime.now(),
    )
    actions = await coordinator.dispatch_event(t0)
    # Coordinator returns coordinated actions (flat list)
    emitted: list[SkillAction] = actions or []
    assert any(
        a.action_type == "place_order" for a in emitted
    ), "ProductSourcingSkill did not emit place_order on early tick"

    # CEO arbitration
    approved = await controller.arbitrate_actions(emitted)
    assert len(approved) >= 1, "No approved actions from arbitration"

    # Execute approved place_order by publishing a canonical PlaceOrderCommand
    for action in approved:
        if action.action_type != "place_order":
            continue
        params = action.parameters or {}
        po = PlaceOrderCommand(
            event_id="po-e2e-1",
            timestamp=datetime.now(),
            agent_id=agent_id,
            supplier_id=params["supplier_id"],
            asin=params["asin"],
            quantity=int(params["quantity"]),
            max_price=(
                Money.from_dollars(str(params["max_price"]))
                if not isinstance(params["max_price"], Money)
                else params["max_price"]
            ),
            reason=action.reasoning or "e2e-test",
        )
        await bus.publish(po)

    # Advance one tick to process arrival (supplier lead_time for selected catalog is 1)
    t1 = TickEvent(
        event_id="tick_1_test",
        timestamp=datetime.now(),
        tick_number=1,
        simulation_time=datetime.now(),
    )
    await bus.publish(t1)
    # Ensure per-tick processing completes
    await asyncio.sleep(0.05)
    await supply.process_tick()
    await asyncio.sleep(0.05)

    inv_after = ws.get_product_inventory_quantity(asin)
    assert (
        inv_after > inv_before
    ), f"Expected inventory to increase for {asin}. Before={inv_before} After={inv_after}"

    # Cleanup
    await supply.stop()
    await ws.stop()
    await bus.stop()
