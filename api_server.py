"""FBA-Bench Enterprise API Server Runner.

This script serves the FastAPI application using Uvicorn when invoked directly.
Intended for local development and testing.

Usage:
    python api_server.py

This will start the server at http://localhost:8000 (configurable via env vars).
"""

import os

import uvicorn

if __name__ == "__main__":
    host = os.getenv("UVICORN_HOST", "0.0.0.0")
    port = int(os.getenv("UVICORN_PORT", "8000"))
    reload = os.getenv("UVICORN_RELOAD", "false").lower() == "true"

    uvicorn.run(
        "api_server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )