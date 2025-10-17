"""
Runner Factory for agent_runners.

Factory for creating AgentRunner instances based on configuration or framework.
Resolves lazy import in __init__.py for RunnerFactory.
"""

from typing import Dict, Type

from ..agents.base import AgentConfig  # type: ignore[import-not-found]
from .base_runner import AgentRunner


class RunnerFactory:
    """
    Factory for creating AgentRunner instances.

    Supports creating runners for different frameworks (e.g., 'diy', 'langchain').
    """

    _runners: Dict[str, Type[AgentRunner]] = {}

    @classmethod
    def register_runner(cls, framework: str, runner_class: Type[AgentRunner]) -> None:
        """
        Register a runner class for a specific framework.

        Args:
            framework (str): The framework name (e.g., 'diy', 'langchain').
            runner_class (Type[AgentRunner]): The runner class to register.
        """
        cls._runners[framework] = runner_class

    @classmethod
    def create(cls, framework: str, config: AgentConfig, **kwargs) -> AgentRunner:
        """
        Create an AgentRunner instance for the given framework.

        Args:
            framework (str): The framework to use.
            config (AgentConfig): The agent configuration.
            **kwargs: Additional keyword arguments for runner initialization.

        Returns:
            AgentRunner: The created runner instance.

        Raises:
            ValueError: If no runner is registered for the framework.
        """
        runner_class = cls._runners.get(framework)
        if runner_class is None:
            raise ValueError(
                f"No runner registered for framework '{framework}'. Available: {list(cls._runners.keys())}"
            )
        return runner_class(config, **kwargs)

    @classmethod
    def get_available_frameworks(cls) -> list[str]:
        """
        Get list of available frameworks.

        Returns:
            list[str]: List of registered framework names.
        """
        return list(cls._runners.keys())


# Register default DIY runner (minimal implementation)
try:
    from .diy_runner import DIYRunner

    RunnerFactory.register_runner("diy", DIYRunner)
except ImportError:
    pass  # DIYRunner may not be available yet
