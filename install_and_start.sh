#!/bin/bash
# Install dependencies and start all services

set -e

cd /Users/JJR/SalesGPT

echo "📦 Installing dependencies..."
python3 -m pip install --user --break-system-packages streamlit plotly pandas pydantic-settings sqlalchemy alembic requests langchain langchain-core langchain-community langchain-openai langchain-text-splitters langchain-classic boto3 aioboto3 2>&1 | grep -v "WARNING" || true

echo ""
echo "✅ Dependencies installed!"
echo ""
echo "🚀 Starting all services..."
echo ""

# Start Mock API
echo "📡 Starting Mock API Server (port 8001)..."
python3 mock_api_server.py > logs/mock_api.log 2>&1 &
MOCK_PID=$!
echo "   PID: $MOCK_PID"
sleep 2

# Start Backend API
echo "🔌 Starting Backend API (port 8000)..."
python3 webhook_handler.py > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "   PID: $BACKEND_PID"
sleep 2

# Start Dashboard
echo "📊 Starting Dashboard (port 8501)..."
python3 -m streamlit run dashboard/streamlit_app.py --server.port 8501 --server.address localhost > logs/dashboard.log 2>&1 &
DASH_PID=$!
echo "   PID: $DASH_PID"
sleep 5

echo ""
echo "✅ All services started!"
echo ""
echo "📋 Service URLs:"
echo "   🌐 Dashboard:      http://localhost:8501"
echo "   🔌 Backend API:    http://localhost:8000"
echo "   📡 Mock API:       http://localhost:8001"
echo ""

# Save PIDs
echo "$MOCK_PID" > .service_pids
echo "$BACKEND_PID" >> .service_pids
echo "$DASH_PID" >> .service_pids

# Check health
echo "🏥 Checking service health..."
sleep 3

curl -s http://localhost:8001/health > /dev/null && echo "   ✅ Mock API: Healthy" || echo "   ⚠️  Mock API: Starting..."
curl -s http://localhost:8000/health > /dev/null && echo "   ✅ Backend API: Healthy" || echo "   ⚠️  Backend API: Starting..."
curl -s http://localhost:8501 > /dev/null && echo "   ✅ Dashboard: Healthy" || echo "   ⚠️  Dashboard: Starting..."

echo ""
echo "🎉 Services are running!"
echo ""
echo "🌐 Open in browser: http://localhost:8501"
echo ""
echo "📄 View logs:"
echo "   tail -f logs/mock_api.log"
echo "   tail -f logs/backend.log"
echo "   tail -f logs/dashboard.log"
echo ""
echo "🛑 To stop: ./stop_all_services.sh"

