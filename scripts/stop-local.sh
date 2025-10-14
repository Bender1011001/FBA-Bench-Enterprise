#!/bin/bash

echo "🛑 Stopping local development setup..."

# Stop background processes
if [ -f .api.pid ]; then
    API_PID=$(cat .api.pid)
    if kill -0 $API_PID 2>/dev/null; then
        echo "🔧 Stopping API server..."
        kill $API_PID
    fi
    rm -f .api.pid
fi

if [ -f .frontend.pid ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "🌐 Stopping frontend..."
        kill $FRONTEND_PID
    fi
    rm -f .frontend.pid
fi

# Stop Redis container
echo "📦 Stopping Redis..."
docker stop fba-redis-local 2>/dev/null || true
docker rm fba-redis-local 2>/dev/null || true

echo "✅ Local development setup stopped."