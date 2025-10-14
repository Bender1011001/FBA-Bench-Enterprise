#!/usr/bin/env python
"""
API router for Project Medusa, the autonomous agent evolution framework.
Provides endpoints to start, stop, monitor, and analyze the Medusa trainer.
"""

import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel

# Configure logging
logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory state for the trainer process
# For a production system, consider a more robust solution like a task queue (Celery)
# or a process manager (Supervisor), but this is sufficient for this application.
medusa_process: Optional[subprocess.Popen] = None

# Define file paths
BASE_DIR = Path("medusa_experiments")
LOG_FILE = BASE_DIR / "logs" / "medusa_trainer.log"


class MedusaStatusResponse(BaseModel):
    status: str
    pid: Optional[int] = None


class MedusaActionResponse(BaseModel):
    status: str
    message: str


@router.post("/medusa/start", response_model=MedusaActionResponse)
async def start_medusa_trainer():
    """
    Starts the Medusa trainer as a background process.
    Ensures that only one instance of the trainer can run at a time.
    """
    global medusa_process
    logger.info("Received request to start Medusa trainer.")

    if medusa_process and medusa_process.poll() is None:
        logger.warning("Medusa trainer is already running.")
        raise HTTPException(status_code=409, detail="Medusa trainer is already running.")

    try:
        # Using poetry run to ensure the correct environment is used.
        # Starting the process in a way that it won't be terminated when the API worker exits.
        command = ["poetry", "run", "python", "medusa_trainer.py"]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        medusa_process = process
        logger.info(f"Medusa trainer started successfully with PID: {process.pid}")
        return MedusaActionResponse(status="started", message=f"Medusa trainer started with PID: {process.pid}")
    except Exception as e:
        logger.error(f"Failed to start Medusa trainer: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start Medusa trainer: {str(e)}")


@router.post("/medusa/stop", response_model=MedusaActionResponse)
async def stop_medusa_trainer():
    """
    Stops the currently running Medusa trainer process gracefully.
    """
    global medusa_process
    logger.info("Received request to stop Medusa trainer.")

    if not medusa_process or medusa_process.poll() is not None:
        logger.warning("Medusa trainer is not running.")
        raise HTTPException(status_code=404, detail="Medusa trainer is not running.")

    try:
        pid = medusa_process.pid
        medusa_process.terminate()  # Sends SIGTERM for graceful shutdown
        await asyncio.sleep(5)  # Give it a moment to shut down
        if medusa_process.poll() is None:
            medusa_process.kill() # Force kill if it's still running
        medusa_process = None
        logger.info(f"Medusa trainer with PID {pid} stopped.")
        return MedusaActionResponse(status="stopped", message=f"Medusa trainer with PID {pid} stopped.")
    except Exception as e:
        logger.error(f"Failed to stop Medusa trainer: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred while stopping the trainer: {str(e)}")


@router.get("/medusa/status", response_model=MedusaStatusResponse)
async def get_medusa_status():
    """
    Checks and returns the current status of the Medusa trainer process.
    """
    global medusa_process
    if medusa_process and medusa_process.poll() is None:
        return MedusaStatusResponse(status="running", pid=medusa_process.pid)
    
    # Clean up the reference if the process has ended
    if medusa_process and medusa_process.poll() is not None:
        medusa_process = None
        
    return MedusaStatusResponse(status="stopped")


@router.get("/medusa/logs", response_class=PlainTextResponse)
async def get_medusa_logs():
    """
    Retrieves and returns the content of the Medusa trainer log file.
    """
    logger.info("Fetching Medusa logs.")
    if not LOG_FILE.exists():
        return "Log file not found. The trainer may not have run yet."
    try:
        return LOG_FILE.read_text(encoding="utf-8")
    except Exception as e:
        logger.error(f"Could not read log file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to read Medusa log file.")


@router.get("/medusa/analysis")
async def get_medusa_analysis():
    """
    Runs the Medusa analyzer and returns the full JSON report.
    This is a synchronous operation and may take a moment.
    """
    logger.info("Running Medusa analysis.")
    try:
        # Import the analyzer here to avoid circular dependencies at startup
        from medusa_experiments.medusa_analyzer import MedusaAnalyzer
        
        analyzer = MedusaAnalyzer()
        report = analyzer.analyze_medusa_run()
        
        # Using JSONResponse to handle serialization of complex data types
        return JSONResponse(content=report)
    except Exception as e:
        logger.error(f"Medusa analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate Medusa analysis report: {str(e)}")