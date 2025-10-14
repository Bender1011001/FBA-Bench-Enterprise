#!/bin/bash

# Start local development setup (no Docker builds)
set -euo pipefail

# Resolve Python interpreter (prefer injected venv python via PYTHON_BIN)
if [ -n "${PYTHON_BIN:-}" ]; then
  PYTHON_CMD="$PYTHON_BIN"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_CMD="python"
else
  echo "❌ No Python interpreter found on PATH."
  exit 1
fi

echo "🚀 Starting FBA-Bench in local development mode..."

# Start Redis in Docker (idempotent)
if docker ps -a --format '{{.Names}}' | grep -q '^fba-redis-local$'; then
    echo "📦 Redis container exists, ensuring it's running..."
    docker start fba-redis-local >/dev/null 2>&1 || true
else
    echo "📦 Starting Redis container..."
    docker run -d --name fba-redis-local -p 6379:6379 redis:7-alpine redis-server --appendonly yes
fi

# Wait for Redis
echo "⏳ Waiting for Redis..."
sleep 3

# Set environment variables
export DATABASE_URL="sqlite+aiosqlite:///./fba_bench.db"
export REDIS_URL="redis://localhost:6379/0"
export PYTHONPATH="$(pwd)"
export FBA_BENCH_REDIS_URL="redis://localhost:6379/0"

# Start API server in background
echo "🔧 Starting API server..."
nohup poetry run uvicorn fba_bench_api.main:app --host 0.0.0.0 --port 8000 --reload >/dev/null 2>&1 &
API_PID=$!

# Start frontend in background
echo "🌐 Starting frontend..."
cd frontend
if [ ! -d "node_modules" ]; then
  echo "📦 Installing frontend dependencies (npm ci)..."
  npm ci
fi
nohup npm run dev -- --host 0.0.0.0 >/dev/null 2>&1 &
FRONTEND_PID=$!
cd ..

# Services launching in background; CLI will perform health checks.
sleep 2

# Browser will be opened by CLI

echo "✅ Local development setup complete!"
echo ""
echo "📱 Frontend: http://localhost:5173"
echo "🔧 API: http://localhost:8000"
echo "📊 Health: http://localhost:8000/api/v1/health"
echo ""
echo "To stop: ./scripts/stop-local.sh"

# Save PIDs for cleanup
echo $API_PID > .api.pid
echo $FRONTEND_PID > .frontend.pid

# Processes started; exiting without blocking
: