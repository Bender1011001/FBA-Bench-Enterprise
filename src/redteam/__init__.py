"""
Red Team / Adversarial Testing Module for FBA-Bench.

This module implements the adversarial resistance framework for testing agent
susceptibility to various exploit scenarios including phishing, social engineering,
market manipulation, and compliance traps.

Components:
- AdversarialEventInjector: Core system for injecting exploit events
- ExploitRegistry: Registry and management of adversarial scenarios
- AdversaryResistanceScorer: Calculate ARS (Adversary Resistance Score)
- GauntletRunner: CI integration for random exploit selection
"""

from .adversarial_event_injector import AdversarialEventInjector
from .exploit_registry import ExploitRegistry
from .exploit_scenario_generator import ExploitScenarioGenerator  # Added this import
from .gauntlet_runner import GauntletRunner
from .resistance_scorer import AdversarialResponse, AdversaryResistanceScorer

__all__ = [
    "AdversarialEventInjector",
    "ExploitRegistry",
    "AdversaryResistanceScorer",
    "AdversarialResponse",
    "GauntletRunner",
    "ExploitScenarioGenerator",
]
__version__ = "1.0.0"
