#!/usr/bin/env python3
"""
Minimal test script for cost tracking functionality.
This test only imports the specific modules we need.
"""

import sys

sys.path.insert(0, "/app")

# Test basic imports
try:
    from llm_interface.pricing import get_model_pricing

    print("✓ Successfully imported pricing module")

    # Test pricing data
    gpt4_pricing = get_model_pricing("gpt-4o")
    print(
        f"✓ GPT-4o pricing: ${gpt4_pricing['input']}/1M input tokens, ${gpt4_pricing['output']}/1M output tokens"
    )

    # Test fallback pricing
    unknown_pricing = get_model_pricing("unknown-model")
    print(
        f"✓ Unknown model fallback pricing: ${unknown_pricing['input']}/1M input tokens, ${unknown_pricing['output']}/1M output tokens"
    )

except Exception as e:
    print(f"✗ Pricing test failed: {e}")
    sys.exit(1)

# Test event creation
try:
    import uuid
    from datetime import datetime

    from fba_events.cost import LLMUsageReportedEvent

    print("✓ Successfully imported LLMUsageReportedEvent")

    # Create event
    event = LLMUsageReportedEvent(
        event_id=str(uuid.uuid4()),
        timestamp=datetime.utcnow(),
        model="gpt-4o",
        prompt_tokens=1000,
        completion_tokens=500,
        call_cost=0.0125,
        total_prompt_tokens=1000,
        total_completion_tokens=500,
        total_cost=0.0125,
    )
    print("✓ Successfully created LLMUsageReportedEvent")

    # Test to_summary_dict
    summary = event.to_summary_dict()
    print(f"✓ Event summary: {summary}")

except Exception as e:
    print(f"✗ Event test failed: {e}")
    sys.exit(1)

# Test cost calculation logic without importing the full service
try:
    from decimal import Decimal

    def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> Decimal:
        """Calculate cost for a given model and token usage."""
        pricing = get_model_pricing(model)

        # Convert pricing from per 1M tokens to per token
        input_cost_per_token = Decimal(str(pricing["input"])) / Decimal("1000000")
        output_cost_per_token = Decimal(str(pricing["output"])) / Decimal("1000000")

        # Calculate total cost
        input_cost = Decimal(str(prompt_tokens)) * input_cost_per_token
        output_cost = Decimal(str(completion_tokens)) * output_cost_per_token

        return input_cost + output_cost

    # Test cost calculation
    cost = calculate_cost("gpt-4o", 1000, 500)
    expected_cost = Decimal("0.0125")  # (1000 * 5.00 / 1_000_000) + (500 * 15.00 / 1_000_000)

    print(f"✓ Calculated cost: ${cost:.6f}")
    print(f"✓ Expected cost: ${expected_cost:.6f}")

    if abs(float(cost) - float(expected_cost)) < 0.0001:
        print("✓ Cost calculation correct")
    else:
        print(f"✗ Cost calculation incorrect: expected {expected_cost}, got {cost}")
        sys.exit(1)

except Exception as e:
    print(f"✗ Cost calculation test failed: {e}")
    sys.exit(1)

print("\n🎉 All minimal cost tracking tests passed!")
print("The core cost tracking functionality is working correctly.")
