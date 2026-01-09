#!/bin/bash
# Stop all running services

echo "🛑 Stopping all SalesGPT services..."

# Read PIDs from file if it exists
if [ -f .service_pids ]; then
    while read pid; do
        if ps -p $pid > /dev/null 2>&1; then
            echo "   Stopping process $pid..."
            kill $pid 2>/dev/null || true
        fi
    done < .service_pids
    rm .service_pids
fi

# Also kill by port (in case PIDs file is missing)
echo "   Checking ports..."
lsof -ti:8001 | xargs kill -9 2>/dev/null || true
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:8501 | xargs kill -9 2>/dev/null || true

# Kill any remaining Python processes running our services
pkill -f "mock_api_server.py" 2>/dev/null || true
pkill -f "webhook_handler.py" 2>/dev/null || true
pkill -f "streamlit.*dashboard" 2>/dev/null || true

echo "✅ All services stopped!"

