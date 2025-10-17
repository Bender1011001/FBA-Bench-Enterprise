"""
Agent Registry for FBA-Bench.

Central registry for agent types and configurations, allowing dynamic registration
and lookup by name or type. Used in base.py for agent discovery.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional, Type

if TYPE_CHECKING:
    from .base import AgentConfig, BaseAgent


class AgentRegistry:
    """
    Singleton registry for agent classes and configurations.

    Allows registering agents by name and retrieving them for instantiation.
    """

    _instance = None
    _agents: Dict[str, Type[BaseAgent]] = {}
    _configs: Dict[str, AgentConfig] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register(
        self,
        name: str,
        agent_class: Type[BaseAgent],
        config: Optional[AgentConfig] = None,
    ) -> None:
        """
        Register an agent class and optional config by name.

        Args:
            name (str): Unique name for the agent (e.g., 'advanced_agent').
            agent_class (Type[BaseAgent]): The agent class to register.
            config (Optional[AgentConfig]): Optional default config for this agent.
        """
        self._agents[name] = agent_class
        if config:
            self._configs[name] = config

    def get_agent_class(self, name: str) -> Optional[Type[BaseAgent]]:
        """
        Retrieve the agent class by name.

        Args:
            name (str): The registered name of the agent.

        Returns:
            Optional[Type['BaseAgent']]: The agent class, or None if not found.
        """
        return self._agents.get(name)

    def get_config(self, name: str) -> Optional[AgentConfig]:
        """
        Retrieve the default config for an agent by name.

        Args:
            name (str): The registered name of the agent.

        Returns:
            Optional['AgentConfig']: The config, or None if not found.
        """
        return self._configs.get(name)

    def list_agents(self) -> Dict[str, Type[BaseAgent]]:
        """
        List all registered agents.

        Returns:
            Dict[str, Type[BaseAgent]]: Mapping of names to agent classes.
        """
        return self._agents.copy()

    def unregister(self, name: str) -> bool:
        """
        Unregister an agent by name.

        Args:
            name (str): The name of the agent to unregister.

        Returns:
            bool: True if unregistered, False if not found.
        """
        if name in self._agents:
            del self._agents[name]
            self._configs.pop(name, None)
            return True
        return False


# Global instance
registry = AgentRegistry()
