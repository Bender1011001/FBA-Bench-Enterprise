"""
Agents module for FBA-Bench.

This module provides agent-related classes, configurations, and utilities.
"""
# mypy: ignore-errors

from .base import AgentConfig, BaseAgent
from .registry import AgentRegistry, registry as agent_registry
from benchmarking.agents.unified_agent import (
    AgentAction,
    AgentCapability,
    AgentContext,
    AgentFactory,
    AgentMessage,
    AgentObservation,
    AgentState,
    BaseUnifiedAgent,
    NativeFBAAdapter,
    UnifiedAgentRunner,
    agent_factory,
)

__all__ = [
    # Legacy agents
    "AgentRegistry",
    "agent_registry",
    "BaseAgent",
    "AgentConfig",
    # Unified agent framework
    "AgentState",
    "AgentCapability",
    "AgentMessage",
    "AgentObservation",
    "AgentAction",
    "AgentContext",
    "BaseUnifiedAgent",
    "NativeFBAAdapter",
    "UnifiedAgentRunner",
    "AgentFactory",
    "agent_factory",
    "SkillCoordinator",
]


# Auto-register built-in agents if needed
def _register_builtin_agents():
    """Register built-in agents on module import."""
    # Placeholder for future registrations
    pass


_register_builtin_agents()
