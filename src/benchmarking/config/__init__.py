"""
Configuration management for benchmarking.

This module provides comprehensive configuration management for FBA-Bench,
including schema validation, environment-specific settings, and configuration templates.

DEPRECATED: The legacy schema-based configuration system is deprecated and will be removed in a future version.
Please use the Pydantic-based configuration models (e.g., PydanticBenchmarkConfig) instead.
"""

import warnings

# Issue a deprecation warning when importing from the legacy schema system
warnings.warn(
    "The legacy schema-based configuration system in 'benchmarking.config' is deprecated and will be removed in a future version. "
    "Please use the Pydantic-based configuration models (e.g., PydanticBenchmarkConfig) instead.",
    DeprecationWarning,
    stacklevel=2,
)


from .manager import ConfigurationManager, ConfigurationProfile, config_manager
from .pydantic_config import (  # Builders and managers; Enums  # Builders and managers; Enums  # Builders and managers; Enums  # Builders and managers; Enums
    AgentCapability,  # Builders and managers; Enums
    ConfigBuilder,  # Builders and managers; Enums
    ConfigTemplate,  # Builders and managers; Enums
    EnvironmentConfig,
    EnvironmentType,
    FrameworkType,  # Builders and managers; Enums
    LLMProvider,
    LogLevel,
    MetricType,  # Builders and managers; Enums
    ScenarioType,  # Builders and managers; Enums
)
from .pydantic_config import AgentConfig as PydanticAgentConfig
from .pydantic_config import BaseConfig as PydanticBaseConfig  # Configuration models
from .pydantic_config import BenchmarkConfig as PydanticBenchmarkConfig
from .pydantic_config import ConfigProfile as PydanticConfigProfile
from .pydantic_config import ConfigurationManager as PydanticConfigurationManager
from .pydantic_config import CrewConfig as PydanticCrewConfig
from .pydantic_config import ExecutionConfig as PydanticExecutionConfig
from .pydantic_config import LLMConfig as PydanticLLMConfig
from .pydantic_config import MemoryConfig as PydanticMemoryConfig
from .pydantic_config import MetricsCollectionConfig as PydanticMetricsConfig
from .pydantic_config import ScenarioConfig as PydanticScenarioConfig
from .pydantic_config import UnifiedAgentRunnerConfig as PydanticUnifiedAgentRunnerConfig
from .pydantic_config import config_manager as pydantic_config_manager  # Global instance

__all__ = [
    # Primary Pydantic configuration (canonical)
    "EnvironmentType",
    "LogLevel",
    "FrameworkType",
    "LLMProvider",
    "MetricType",
    "ScenarioType",
    "PydanticBaseConfig",
    "PydanticLLMConfig",
    "AgentCapability",
    "PydanticAgentConfig",
    "PydanticMemoryConfig",
    "PydanticCrewConfig",
    "PydanticExecutionConfig",
    "PydanticMetricsConfig",
    "PydanticScenarioConfig",
    "PydanticBenchmarkConfig",
    "EnvironmentConfig",
    "ConfigTemplate",
    "PydanticConfigProfile",
    "PydanticUnifiedAgentRunnerConfig",
    "ConfigBuilder",
    "PydanticConfigurationManager",
    "pydantic_config_manager",
    # Manager interfaces
    "ConfigurationProfile",
    "ConfigurationManager",
    "config_manager",
]
