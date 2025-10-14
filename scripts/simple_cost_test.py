#!/usr/bin/env python3
"""
Simple test script for cost tracking functionality.

Important:
- This script must be safe to import during pytest collection. All executable logic
  is guarded under `if __name__ == "__main__":` to avoid side effects during imports.
- CostTrackingService now requires an EventBus; we provide an in-memory bus.
"""

import os
import sys

# Ensure project root is on sys.path when running this script directly
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def main() -> int:
    # Test basic imports
    try:
        from llm_interface.pricing import MODEL_PRICING, get_model_pricing  # noqa: F401

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
        return 1

    # Test cost tracking service
    try:
        from fba_events.bus import InMemoryEventBus as EventBus  # prefer in-repo bus implementation
        from services.cost_tracking_service import CostTrackingService

        print("✓ Successfully imported CostTrackingService and EventBus")

        # Create service instance with a proper EventBus
        event_bus = EventBus()
        cost_tracker = CostTrackingService(event_bus=event_bus)
        print("✓ Successfully created CostTrackingService instance")

        # Test recording usage
        cost_tracker.record_usage(
            "gpt-4o",
            {
                "prompt_tokens": 1000,
                "completion_tokens": 500,
            },
        )
        print("✓ Successfully recorded usage")

        # Test getting totals
        totals = cost_tracker.get_totals()
        print(
            f"✓ Totals: {totals['total_prompt_tokens']} prompt tokens, {totals['total_completion_tokens']} completion tokens, ${totals['total_cost']:.6f} total cost"
        )

        # Expected cost calculation: (1000 * 5.00 / 1_000_000) + (500 * 15.00 / 1_000_000) = 0.005 + 0.0075 = 0.0125
        expected_cost = 0.0125
        actual_cost = float(totals["total_cost"])
        if abs(actual_cost - expected_cost) < 0.0001:
            print(f"✓ Cost calculation correct: ${actual_cost:.6f}")
        else:
            print(
                f"✗ Cost calculation incorrect: expected ${expected_cost:.6f}, got ${actual_cost:.6f}"
            )
            return 1

    except Exception as e:
        print(f"✗ CostTrackingService test failed: {e}")
        return 1

    # Test event creation
    try:
        from fba_events.cost import LLMUsageReportedEvent

        print("✓ Successfully imported LLMUsageReportedEvent")

        # Create event
        event = LLMUsageReportedEvent(
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
        return 1

    print("\n🎉 All cost tracking tests passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
