#!/bin/sh
set -e

# Start Uvicorn in background
cd /app
poetry run uvicorn fba_bench_api.main:create_app --factory --host 0.0.0.0 --port 8001 --workers ${UVICORN_WORKERS:-4} --timeout-keep-alive ${UVICORN_TIMEOUT:-120} &

# Run Alembic migrations if needed (idempotent)
poetry run alembic upgrade head || true

# Wait for Uvicorn to be ready
sleep 5

# Start Nginx in foreground
exec nginx -g 'daemon off;'