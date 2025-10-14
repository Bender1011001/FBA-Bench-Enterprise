#!/usr/bin/env python3
"""
ClearML Demo Data Populator - Creates sample experiments and dashboards.

This script populates ClearML with demo data to show off the game-like interface:
- Creates multiple "Quest" experiments with different statuses
- Logs sample metrics with game-themed titles
- Creates artifacts (reports, models, datasets)
- Sets up a dashboard for easy navigation

Run this after starting ClearML server to see immediate results.

Usage:
    python scripts/populate_clearml_demo.py
"""

import os
import random
import sys
import time
from pathlib import Path

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from clearml import Logger, Task
    from clearml.automation import GridSearchControl

    CLEARML_AVAILABLE = True
except ImportError:
    print("ClearML not installed. Install with: pip install clearml")
    CLEARML_AVAILABLE = False
    sys.exit(1)


def create_demo_quest(quest_name: str, level: int, status: str = "completed"):
    """Create a demo quest (experiment) with sample data."""

    # Create task with game-themed name
    task = Task.init(
        project_name="FBA-Bench",
        task_name=f"🎮 Quest: {quest_name} - Level {level}",
        tags=["quest", f"level:{level}", f"status:{status}", "demo"],
    )

    # Connect configuration
    config = {
        "scenario_name": quest_name,
        "difficulty_tier": level,
        "max_ticks": random.randint(50, 200),
        "agent_type": random.choice(["GPT-4", "Claude-3", "Baseline-Bot"]),
        "initial_capital": random.randint(10000, 100000),
    }
    task.connect(config)

    # Get logger for metrics
    logger = task.get_logger()

    # Simulate progression over time
    max_iterations = config["max_ticks"]
    final_profit = random.randint(5000, 50000) * (level + 1)

    for iteration in range(1, max_iterations + 1):
        # Simulate business metrics progression
        progress = iteration / max_iterations

        # Hero Stats (with emojis for visual appeal)
        profit = final_profit * progress + random.uniform(-1000, 1000)
        market_share = min(50, level * 5 + progress * 20 + random.uniform(-2, 2))
        customer_satisfaction = 60 + progress * 30 + random.uniform(-5, 5)
        delivery_rate = 70 + progress * 25 + random.uniform(-3, 3)

        # Log with game-themed titles
        logger.report_scalar(title="💰 Hero Profit", series="USD", value=profit, iteration=iteration)
        logger.report_scalar(
            title="📊 Market Power", series="Percentage", value=market_share, iteration=iteration
        )
        logger.report_scalar(
            title="😊 Customer Love",
            series="Satisfaction",
            value=customer_satisfaction,
            iteration=iteration,
        )
        logger.report_scalar(
            title="🚚 Delivery Speed",
            series="On-Time Rate",
            value=delivery_rate,
            iteration=iteration,
        )

        # Add some events/milestones
        if iteration == max_iterations // 4:
            logger.report_text("📈 Quest Update: Market expansion successful!")
        elif iteration == max_iterations // 2:
            logger.report_text("⚡ Power-up: New supplier contracts secured!")
        elif iteration == max_iterations * 3 // 4:
            logger.report_text("🏆 Achievement: Customer satisfaction milestone reached!")

    # Create final victory report
    success = profit > final_profit * 0.8 and customer_satisfaction > 80
    victory_html = f"""
    <html>
    <head>
        <style>
            body {{ 
                background: linear-gradient(135deg, #0f0f23, #1a1a2e); 
                color: white; 
                font-family: Arial, sans-serif; 
                text-align: center; 
                padding: 20px;
            }}
            .quest-complete {{ 
                border: 3px solid #10b981; 
                border-radius: 15px; 
                padding: 30px; 
                margin: 20px auto; 
                max-width: 600px;
                background: rgba(16, 185, 129, 0.1);
                box-shadow: 0 0 30px rgba(16, 185, 129, 0.3);
            }}
            .stats {{ 
                display: grid; 
                grid-template-columns: repeat(2, 1fr); 
                gap: 15px; 
                margin: 20px 0;
            }}
            .stat {{ 
                background: rgba(255, 255, 255, 0.1); 
                padding: 15px; 
                border-radius: 10px;
                border-left: 4px solid #8b5cf6;
            }}
            .success {{ color: #10b981; }}
            .warning {{ color: #f59e0b; }}
        </style>
    </head>
    <body>
        <div class="quest-complete">
            <h1>{'🎉 QUEST COMPLETED! 🎉' if success else '⚠️ Quest Failed'}</h1>
            <h2>{quest_name} - Level {level}</h2>
            
            <div class="stats">
                <div class="stat">
                    <h3>💰 Final Profit</h3>
                    <p class="{'success' if profit > 0 else 'warning'}">${profit:,.0f}</p>
                </div>
                <div class="stat">
                    <h3>📊 Market Share</h3>
                    <p class="{'success' if market_share > 10 else 'warning'}">{market_share:.1f}%</p>
                </div>
                <div class="stat">
                    <h3>😊 Customer Satisfaction</h3>
                    <p class="{'success' if customer_satisfaction > 80 else 'warning'}">{customer_satisfaction:.1f}%</p>
                </div>
                <div class="stat">
                    <h3>🚚 Delivery Performance</h3>
                    <p class="{'success' if delivery_rate > 90 else 'warning'}">{delivery_rate:.1f}%</p>
                </div>
            </div>
            
            <h3>🏆 Rewards Earned:</h3>
            <ul>
                {'<li>💎 Profit Master Badge</li>' if profit > final_profit * 0.9 else ''}
                {'<li>👑 Customer Champion</li>' if customer_satisfaction > 85 else ''}
                {'<li>⚡ Speed Demon</li>' if delivery_rate > 95 else ''}
                {'<li>🌟 Empire Builder</li>' if market_share > 20 else ''}
            </ul>
            
            <p><strong>{'Ready for next level!' if success else 'Try again to unlock next level!'}</strong></p>
        </div>
    </body>
    </html>
    """

    logger.report_media(
        title="Quest Victory Screen",
        series="Results",
        local_path=None,
        url=None,
        html_data=victory_html,
    )

    # Mark task as completed
    if status == "completed":
        task.mark_completed()
    elif status == "failed":
        task.mark_failed()

    print(f"✅ Created quest: {quest_name} (Level {level}) - {status}")
    return task


def create_leaderboard_report():
    """Create a leaderboard dashboard report."""

    task = Task.init(
        project_name="FBA-Bench",
        task_name="🏆 FBA Empire Leaderboard",
        tags=["leaderboard", "dashboard", "demo"],
    )

    logger = task.get_logger()

    # Create leaderboard HTML
    leaderboard_html = """
    <html>
    <head>
        <style>
            body { 
                background: linear-gradient(135deg, #0f0f23, #1a1a2e); 
                color: white; 
                font-family: Arial, sans-serif; 
                padding: 20px;
            }
            .leaderboard { 
                max-width: 800px; 
                margin: 0 auto; 
                background: rgba(0,0,0,0.3); 
                border-radius: 15px; 
                padding: 30px;
                border: 2px solid #f59e0b;
            }
            .rank { 
                display: flex; 
                align-items: center; 
                padding: 15px; 
                margin: 10px 0; 
                border-radius: 10px; 
                background: rgba(255,255,255,0.05);
            }
            .rank:nth-child(1) { border-left: 5px solid #f59e0b; }
            .rank:nth-child(2) { border-left: 5px solid #9ca3af; }
            .rank:nth-child(3) { border-left: 5px solid #d97706; }
            .rank-number { 
                font-size: 2em; 
                margin-right: 20px; 
                min-width: 60px; 
                text-align: center;
            }
            .player-info { flex-grow: 1; }
            .score { font-size: 1.5em; color: #10b981; }
        </style>
    </head>
    <body>
        <div class="leaderboard">
            <h1>🏆 FBA Empire Champions</h1>
            <div class="rank">
                <div class="rank-number">🥇</div>
                <div class="player-info">
                    <h3>GPT-4 Master</h3>
                    <p>Supply Chain Dominator</p>
                </div>
                <div class="score">95,750 pts</div>
            </div>
            <div class="rank">
                <div class="rank-number">🥈</div>
                <div class="player-info">
                    <h3>Claude Strategist</h3>
                    <p>Market Share Legend</p>
                </div>
                <div class="score">87,230 pts</div>
            </div>
            <div class="rank">
                <div class="rank-number">🥉</div>
                <div class="player-info">
                    <h3>Baseline Bot</h3>
                    <p>Steady Performer</p>
                </div>
                <div class="score">65,100 pts</div>
            </div>
        </div>
        
        <div style="text-align: center; margin-top: 30px;">
            <h3>🎯 How to Climb the Ranks:</h3>
            <ol style="text-align: left; max-width: 600px; margin: 0 auto;">
                <li><strong>Run Quests:</strong> Use <code>fba-bench launch --game-mode</code></li>
                <li><strong>Optimize Strategies:</strong> Experiment with different agent configurations</li>
                <li><strong>Complete Challenges:</strong> Try higher difficulty tiers</li>
                <li><strong>Share Results:</strong> Clone successful experiments to build on them</li>
            </ol>
        </div>
    </body>
    </html>
    """

    logger.report_media(
        title="Empire Leaderboard",
        series="Rankings",
        local_path=None,
        url=None,
        html_data=leaderboard_html,
    )

    task.mark_completed()
    print("✅ Created leaderboard dashboard")


def main():
    """Populate ClearML with demo data."""
    print("🎮 Populating ClearML with FBA Empire demo data...")

    # Set local ClearML configuration if not set
    if not os.getenv("CLEARML_API_HOST"):
        os.environ["CLEARML_API_HOST"] = "http://localhost:8008"
        os.environ["CLEARML_WEB_HOST"] = "http://localhost:8080"
        os.environ["CLEARML_FILES_HOST"] = "http://localhost:8081"

    try:
        # Create various demo quests
        quests = [
            ("Smoke Test Challenge", 0, "completed"),
            ("Supply Chain Crisis", 1, "completed"),
            ("Market Expansion", 2, "completed"),
            ("International Trade", 2, "running"),
            ("AI Revolution", 3, "queued"),
        ]

        for quest_name, level, status in quests:
            create_demo_quest(quest_name, level, status)
            time.sleep(1)  # Small delay to spread out creation times

        # Create leaderboard
        create_leaderboard_report()

        print("\n🎉 Demo data creation complete!")
        print("\n📋 What you can do now in ClearML (http://localhost:8080):")
        print("1. 📊 View Projects > FBA-Bench to see all quests")
        print("2. 🎮 Click on any quest to see metrics plots and victory screens")
        print("3. 🏆 Check the Leaderboard task for rankings")
        print("4. 🔄 Clone any quest to create variations")
        print("5. 📈 Compare experiments to see which strategies work best")
        print("6. 🎯 Queue experiments to run on agents")
        print("\n💡 Try running: fba-bench launch --game-mode")
        print("   This will create a new quest with your own simulation!")

    except Exception as e:
        print(f"❌ Error creating demo data: {e}")
        print("Make sure ClearML server is running: fba-bench launch --with-server")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
