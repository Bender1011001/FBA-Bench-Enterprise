"""
Test configuration fixes for engine tests.

This module provides enhanced fixtures that fix mock attribute issues
for proper test execution.
"""

from unittest.mock import Mock

import pytest

from benchmarking.config.manager import ConfigurationManager
from benchmarking.integration.manager import IntegrationManager


@pytest.fixture
def enhanced_config_manager():
    """Create a mock configuration manager with all expected test attributes."""
    mock = Mock(spec=ConfigurationManager)
    # Add missing attributes that tests expect
    mock.initialize = Mock(return_value=None)
    mock.get_output_path = Mock(return_value="/tmp")
    return mock


@pytest.fixture
def enhanced_integration_manager():
    """Create a mock integration manager with all expected test attributes."""
    mock = Mock(spec=IntegrationManager)
    # Add missing attributes that tests expect
    mock.initialize = Mock(return_value=None)
    return mock
