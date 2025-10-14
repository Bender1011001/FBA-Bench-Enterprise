import os

import uvicorn

from fba_bench_api.server.app_factory import create_app

# Expose app at module level for tests and ASGI servers
app = create_app()


def run():
    """Creates and runs the FastAPI application."""
    host = os.environ.get("FBA_BENCH_HOST", "0.0.0.0")
    port = int(os.environ.get("FBA_BENCH_PORT", 8000))
    reload = os.environ.get("FBA_BENCH_RELOAD", "true").lower() == "true"
    uvicorn.run(app, host=host, port=port, reload=reload)


if __name__ == "__main__":
    run()
