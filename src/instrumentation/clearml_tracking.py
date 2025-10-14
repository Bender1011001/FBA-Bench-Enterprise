"""
ClearML tracking integration for FBA-Bench.

Provides init_clearml function to initialize ClearML task for experiment tracking.
Handles optional ClearML installation and API key configuration.
"""

import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)

try:
    from clearml import Task

    CLEARML_AVAILABLE = True
except ImportError:
    CLEARML_AVAILABLE = False
    Task = None


def init_clearml(
    project_name: str = "FBA-Bench", task_name: str = "FBA-Simulation"
) -> Optional[Task]:
    """
    Initialize ClearML task if ClearML is available and configured.

    Args:
        project_name (str): ClearML project name.
        task_name (str): ClearML task name.

    Returns:
        Optional[Task]: The ClearML Task instance, or None if not available.
    """
    if not CLEARML_AVAILABLE:
        logger.info("ClearML not installed; skipping initialization")
        return None

    api_key = os.getenv("CLEARML_API_KEY")
    if not api_key:
        logger.info("CLEARML_API_KEY not set; skipping ClearML initialization")
        return None

    try:
        task = Task.init(
            project_name=project_name, task_name=task_name, auto_push=True, output_uri=True
        )
        logger.info(f"ClearML task initialized: {task_name} in project {project_name}")
        return task
    except Exception as e:
        logger.warning(f"Failed to initialize ClearML task: {e}")
        return None
