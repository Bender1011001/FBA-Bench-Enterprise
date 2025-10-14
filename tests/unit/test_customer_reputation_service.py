from unittest.mock import MagicMock

import pytest

from services.customer_reputation_service import CustomerReputationService, ReputationEvent


@pytest.mark.parametrize(
    "event_input, expected_score",
    [
        # Example 1: positive_review, high severity
        (
            ReputationEvent(
                customer_id="cust1",
                type="positive_review",
                severity="high",
                current_score=50.0,
            ),
            52.0,
        ),
        # Example 2: policy_violation
        (
            ReputationEvent(
                customer_id="cust2",
                type="policy_violation",
                current_score=90.0,
            ),
            86.0,
        ),
        # Example 3: negative_review, high severity, weight=2
        (
            ReputationEvent(
                customer_id="cust3",
                type="negative_review",
                severity="high",
                weight=2.0,
                current_score=10.0,
            ),
            4.0,
        ),
        # Additional test cases
        # sale_success
        (
            ReputationEvent(
                customer_id="cust4",
                type="sale_success",
                current_score=75.0,
            ),
            75.3,
        ),
        # positive_review, medium severity (default)
        (
            ReputationEvent(
                customer_id="cust5",
                type="positive_review",
                severity="medium",
                current_score=60.0,
            ),
            61.0,
        ),
        # negative_review, medium severity
        (
            ReputationEvent(
                customer_id="cust6",
                type="negative_review",
                severity="medium",
                current_score=60.0,
            ),
            58.5,
        ),
        # dispute_approved
        (
            ReputationEvent(
                customer_id="cust7",
                type="dispute_approved",
                current_score=80.0,
            ),
            80.5,
        ),
        # dispute_denied, medium severity
        (
            ReputationEvent(
                customer_id="cust8",
                type="dispute_denied",
                severity="medium",
                current_score=80.0,
            ),
            78.0,
        ),
        # dispute_denied, low severity
        (
            ReputationEvent(
                customer_id="cust9",
                type="dispute_denied",
                severity="low",
                current_score=80.0,
            ),
            79.0,
        ),
        # dispute_escalated
        (
            ReputationEvent(
                customer_id="cust10",
                type="dispute_escalated",
                current_score=70.0,
            ),
            69.5,
        ),
        # late_shipping, high severity
        (
            ReputationEvent(
                customer_id="cust11",
                type="late_shipping",
                severity="high",
                current_score=70.0,
            ),
            69.0,
        ),
        # late_shipping, low severity
        (
            ReputationEvent(
                customer_id="cust12",
                type="late_shipping",
                severity="low",
                current_score=70.0,
            ),
            69.5,
        ),
        # return
        (
            ReputationEvent(
                customer_id="cust13",
                type="return",
                current_score=70.0,
            ),
            69.3,
        ),
        # unknown type
        (
            ReputationEvent(
                customer_id="cust14",
                type="unknown_event_type",
                current_score=70.0,
            ),
            70.0,
        ),
        # Test clipping at 0
        (
            ReputationEvent(
                customer_id="cust15",
                type="policy_violation",
                weight=10.0,  # Large weight to force below 0
                current_score=5.0,
            ),
            0.0,
        ),
        # Test clipping at 100
        (
            ReputationEvent(
                customer_id="cust16",
                type="positive_review",
                severity="high",
                weight=10.0,  # Large weight to force above 100
                current_score=95.0,
            ),
            100.0,
        ),
        # Test with metadata (should be ignored)
        (
            ReputationEvent(
                customer_id="cust17",
                type="sale_success",
                current_score=50.0,
                metadata={"some_key": "some_value"},
            ),
            50.3,
        ),
    ],
)
def test_update_reputation_score(event_input: ReputationEvent, expected_score: float):
    """Tests the update_reputation_score method with various inputs."""
    # Create mock dependencies
    mock_event_bus = MagicMock()
    mock_world_store = MagicMock()

    # Create the service with mocked dependencies
    svc = CustomerReputationService(mock_event_bus, mock_world_store)

    result = svc.update_reputation_score(event_input)
    assert result == expected_score
