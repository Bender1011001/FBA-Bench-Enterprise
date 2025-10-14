import pytest

from money import Money
from services.dispute_service import DisputeDetails, DisputeResolution, DisputeService
from services.double_entry_ledger_service import DoubleEntryLedgerService


@pytest.mark.asyncio
async def test_create_and_resolve_refund_with_inventory_return():
    ledger = DoubleEntryLedgerService(config={})
    svc = DisputeService(ledger)

    # Create dispute: 2 units * $12 price, $5 cost per unit, with inventory return
    rec = svc.create_dispute(
        asin="B00TEST123",
        units=2,
        unit_price=Money.from_dollars("12.00"),
        cost_per_unit=Money.from_dollars("5.00"),
        reason="Customer dissatisfaction",
        return_to_inventory=True,
    )

    # Resolve with refund; posts balanced adjusting entry
    updated = await svc.resolve_refund(rec.dispute_id)

    assert updated.status == "resolved_refund"
    assert updated.resolved_at is not None

    # Expected ledger impacts:
    # - sales_revenue debited $24.00 => revenue credit-normal -> balance becomes -$24.00
    # - cash credited $24.00 => asset debit-normal -> balance becomes -$24.00 (cash out)
    # - inventory debited $10.00 => asset debit-normal -> +$10.00
    # - cost_of_goods_sold credited $10.00 => expense debit-normal -> -$10.00 (expense reduced)
    assert ledger.get_account_balance("sales_revenue").cents == -2400
    assert ledger.get_account_balance("cash").cents == -2400
    assert ledger.get_account_balance("inventory").cents == 1000
    assert ledger.get_account_balance("cost_of_goods_sold").cents == -1000

    # Trial balance must remain balanced
    assert ledger.is_trial_balance_balanced() is True


@pytest.mark.asyncio
async def test_resolve_reject_has_no_ledger_impact():
    ledger = DoubleEntryLedgerService(config={})
    svc = DisputeService(ledger)

    rec = svc.create_dispute(
        asin="B00TESTREJ",
        units=1,
        unit_price=Money.from_dollars("10.00"),
        cost_per_unit=Money.from_dollars("4.00"),
        reason="Invalid claim",
        return_to_inventory=False,
    )

    updated = await svc.resolve_reject(rec.dispute_id)

    assert updated.status == "resolved_reject"
    assert updated.resolved_at is not None

    # No ledger impact expected; balances remain zero
    for acct in ("sales_revenue", "cash", "inventory", "cost_of_goods_sold", "other_expenses"):
        assert ledger.get_account_balance(acct).cents == 0

    assert ledger.is_trial_balance_balanced() is True


@pytest.mark.asyncio
async def test_write_off_recognizes_revenue_reduction():
    ledger = DoubleEntryLedgerService(config={})
    svc = DisputeService(ledger)

    rec = svc.create_dispute(
        asin="B00WRITEOFF",
        units=1,
        unit_price=Money.from_dollars("9.99"),
        cost_per_unit=Money.from_dollars("3.50"),
        reason="Operational adjustment",
        return_to_inventory=False,
    )

    updated = await svc.write_off(rec.dispute_id, Money.from_dollars("6.00"))

    assert updated.status == "written_off"
    assert updated.resolved_at is not None

    # Expected: sales_revenue debited $6 => -$6 on a credit-normal account
    #           other_expenses credited $6 => -$6 on a debit-normal expense account (reduces expense)
    assert ledger.get_account_balance("sales_revenue").cents == -600
    assert ledger.get_account_balance("other_expenses").cents == -600

    assert ledger.is_trial_balance_balanced() is True


@pytest.mark.asyncio
async def test_invalid_ids_and_state_transitions():
    ledger = DoubleEntryLedgerService(config={})
    svc = DisputeService(ledger)

    rec = svc.create_dispute(
        asin="B00STATE",
        units=1,
        unit_price=Money.from_dollars("8.00"),
        cost_per_unit=Money.from_dollars("3.00"),
        reason="State transition test",
        return_to_inventory=True,
    )

    # Unknown dispute_id should raise KeyError
    with pytest.raises(KeyError):
        await svc.resolve_refund("unknown_id")

    with pytest.raises(KeyError):
        await svc.write_off("unknown_id", Money.from_dollars("1.00"))

    # Resolve refund once
    await svc.resolve_refund(rec.dispute_id)

    # Second resolution attempts should fail due to invalid state
    with pytest.raises(ValueError):
        await svc.resolve_refund(rec.dispute_id)

    with pytest.raises(ValueError):
        await svc.resolve_reject(rec.dispute_id)

    with pytest.raises(ValueError):
        await svc.write_off(rec.dispute_id, Money.from_dollars("1.00"))


@pytest.mark.parametrize(
    "dispute_details_input, expected_resolution",
    [
        # Example 1: Customer, damaged_item, high severity, strong evidence
        (
            DisputeDetails(
                type="customer",
                reason="damaged_item",
                amount=100,
                severity="high",
                evidence_strength=0.9,
            ),
            DisputeResolution(
                resolution="approved",
                refund_amount=100.0,
                penalties=[],
                reputation_delta=0.5,
                notes="Customer dispute approved due to strong evidence and high severity.",
                sla_category="priority",
                follow_up_actions=["restock_inspection", "issue_refund"],
            ),
        ),
        # Example 2: Customer, late_delivery, medium severity, medium evidence
        (
            DisputeDetails(
                type="customer",
                reason="late_delivery",
                amount=40,
                severity="medium",
                evidence_strength=0.6,
            ),
            DisputeResolution(
                resolution="partial",
                refund_amount=20.0,
                penalties=[],
                reputation_delta=0.3,
                notes="Customer dispute partially approved due to sufficient evidence and medium severity.",
                sla_category="normal",
                follow_up_actions=["carrier_inquiry"],
            ),
        ),
        # Example 3: Customer, fraud_suspected, low severity, weak evidence
        (
            DisputeDetails(
                type="customer",
                reason="fraud_suspected",
                amount=200,
                severity="low",
                evidence_strength=0.4,
            ),
            DisputeResolution(
                resolution="escalated",
                refund_amount=0.0,
                penalties=["investigate"],
                reputation_delta=-0.2,
                notes="Customer dispute escalated due to suspected fraud.",
                sla_category="priority",
                follow_up_actions=["manual_review"],
            ),
        ),
        # Example 4: Supplier, supplier_shortage, low severity, strong evidence
        (
            DisputeDetails(
                type="supplier",
                reason="supplier_shortage",
                amount=300,
                severity="low",
                evidence_strength=0.8,
            ),
            DisputeResolution(
                resolution="approved",
                refund_amount=300.0,
                penalties=[],
                reputation_delta=0.1,
                notes="Supplier dispute approved due to high severity or strong evidence.",
                sla_category="normal",
                follow_up_actions=["contact_supplier", "issue_refund"],
            ),
        ),
        # Example 5: Supplier, price_discrepancy, low severity, weak evidence
        (
            DisputeDetails(
                type="supplier",
                reason="price_discrepancy",
                amount=120,
                severity="low",
                evidence_strength=0.3,
            ),
            DisputeResolution(
                resolution="partial",
                refund_amount=48.0,
                penalties=[],
                reputation_delta=0.0,
                notes="Supplier dispute partially approved.",
                sla_category="normal",
                follow_up_actions=["contact_supplier", "issue_refund"],
            ),
        ),
        # Additional test case: Customer, damaged_item, low severity, medium evidence
        (
            DisputeDetails(
                type="customer",
                reason="damaged_item",
                amount=50,
                severity="low",
                evidence_strength=0.5,
            ),
            DisputeResolution(
                resolution="partial",
                refund_amount=12.5,
                penalties=[],
                reputation_delta=0.3,
                notes="Customer dispute partially approved due to sufficient evidence and low severity.",
                sla_category="normal",
                follow_up_actions=["restock_inspection", "issue_refund"],
            ),
        ),
        # Additional test case: Customer, item_not_as_described, high severity, weak evidence
        (
            DisputeDetails(
                type="customer",
                reason="item_not_as_described",
                amount=75,
                severity="high",
                evidence_strength=0.4,
            ),
            DisputeResolution(
                resolution="denied",
                refund_amount=0.0,
                penalties=["warning"],
                reputation_delta=-0.5,
                notes="Customer dispute denied due to insufficient evidence.",
                sla_category="normal",
                follow_up_actions=["catalog_review"],
            ),
        ),
    ],
)
def test_handle_dispute(
    dispute_details_input: DisputeDetails, expected_resolution: DisputeResolution
):
    """Tests the handle_dispute method with various inputs."""
    # The ledger service is not used by handle_dispute, so we can pass a mock or None.
    # However, the DisputeService constructor requires it.
    # We can pass a mock or a simple instance if it doesn't interfere.
    # For simplicity, we'll pass a mock.
    mock_ledger_service = None  # type: ignore
    svc = DisputeService(ledger_service=mock_ledger_service)  # type: ignore

    result = svc.handle_dispute(dispute_details_input)

    assert result.resolution == expected_resolution.resolution
    assert result.refund_amount == expected_resolution.refund_amount
    assert result.penalties == expected_resolution.penalties
    assert result.reputation_delta == expected_resolution.reputation_delta
    assert result.notes == expected_resolution.notes
    assert result.sla_category == expected_resolution.sla_category
    assert result.follow_up_actions == expected_resolution.follow_up_actions
