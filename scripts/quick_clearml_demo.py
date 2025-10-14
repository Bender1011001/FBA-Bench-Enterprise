#!/usr/bin/env python3
"""
Quick ClearML Demo - Populates ClearML with immediate data so you see results right away.

Run this after starting ClearML to see experiments in the UI at http://localhost:8080
No API keys needed for local setup.
"""

import os

from clearml import Task

# Set local ClearML config
os.environ["CLEARML_API_HOST"] = "http://localhost:8008"
os.environ["CLEARML_WEB_HOST"] = "http://localhost:8080"
os.environ["CLEARML_FILES_HOST"] = "http://localhost:8081"


def create_demo_experiment():
    """Create a simple experiment with metrics and plots."""

    # Initialize task in FBA-Bench project
    task = Task.init(
        project_name="FBA-Bench",
        task_name="🚀 Quick Demo - First Experiment",
        tags=["demo", "quick-start"],
    )

    # Log some sample business metrics
    logger = task.get_logger()

    # Simulate a simple business run
    for i in range(1, 11):
        # Sample metrics
        profit = 1000 + i * 500 + (i * 100)  # Increasing profit
        revenue = profit * 1.5
        cost = revenue - profit
        market_share = min(50, i * 4.5)  # Growing market share

        logger.report_scalar("💰 Profit", "USD", value=profit, iteration=i)
        logger.report_scalar("💵 Revenue", "USD", value=revenue, iteration=i)
        logger.report_scalar("💸 Cost", "USD", value=cost, iteration=i)
        logger.report_scalar("📊 Market Share", "%", value=market_share, iteration=i)

        # Add a plot
        logger.report_plot(
            title="Business Growth", series="Growth Curve", iteration=i, x=i, y=market_share
        )

    # Create a final report
    final_report = f"""
    <h1>🎉 FBA-Bench Quick Demo Complete!</h1>
    <p>This experiment shows a simple business simulation with growing profit and market share.</p>
    <ul>
        <li>📈 Final Profit: ${profit:.0f}</li>
        <li>📊 Final Market Share: {market_share:.1f}%</li>
        <li>🚀 Ready for real simulations!</li>
    </ul>
    <p>Next: Run <code>fba-bench launch</code> for full experiments.</p>
    """

    logger.report_text("Demo Summary", final_report)

    # Mark as completed
    task.mark_completed()

    print("✅ Demo experiment created! Check http://localhost:8080")
    print("   - Go to Projects > FBA-Bench")
    print("   - Click on 'Quick Demo - First Experiment'")
    print("   - See metrics, plots, and summary")


if __name__ == "__main__":
    print("🎮 Creating quick ClearML demo...")
    create_demo_experiment()
    print("\n🌟 ClearML is now populated with data!")
    print("Open http://localhost:8080 to see your experiment.")
