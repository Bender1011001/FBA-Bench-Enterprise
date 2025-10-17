"""
Agents module for the FBA-Bench benchmarking framework.

This module provides the core components for defining and managing agents
that participate in benchmark scenarios. It includes base classes, configurations,
and a registry for agent implementations.
"""

from llm_interface.llm_config import LLMConfig

from .base import AgentConfig, BaseAgent
from .registry import AgentRegistry, agent_registry
from .unified_agent import (  # Factory; Types and enums; Base classes; Global instance
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
    "LLMConfig",
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
]


# You can add logic here to automatically register built-in agents if desired
def _register_builtin_agents():
    """Register built-in agents on module import (placeholder)."""
    # Example:
    # from .llm_agent import LLMAgent
    # agent_registry.register("llm_agent", LLMAgent)


_register_builtin_agents()
