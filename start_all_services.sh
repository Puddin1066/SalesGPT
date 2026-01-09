#!/bin/bash
# Start all services locally for browser access

set -e

echo "🚀 Starting SalesGPT Email Platform Services..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp deployment/env.example .env
    echo "✅ Created .env file. Please update with your settings if needed."
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Set default mock API URL if not set
export APOLLO_API_URL=${APOLLO_API_URL:-http://localhost:8001}
export SMARTLEAD_API_URL=${SMARTLEAD_API_URL:-http://localhost:8001}
export HUBSPOT_API_URL=${HUBSPOT_API_URL:-http://localhost:8001}

# Create log directory
mkdir -p logs

echo "📡 Starting Mock API Server on port 8001..."
python3 mock_api_server.py > logs/mock_api.log 2>&1 &
MOCK_API_PID=$!
echo "   PID: $MOCK_API_PID"
sleep 2

echo "🔌 Starting Backend API (Webhook Handler) on port 8000..."
python3 webhook_handler.py > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "   PID: $BACKEND_PID"
sleep 2

echo "📊 Starting Dashboard on port 8501..."
streamlit run dashboard/streamlit_app.py --server.port 8501 --server.address localhost > logs/dashboard.log 2>&1 &
DASHBOARD_PID=$!
echo "   PID: $DASHBOARD_PID"
sleep 3

echo ""
echo "✅ All services started!"
echo ""
echo "📋 Service URLs:"
echo "   🌐 Dashboard:      http://localhost:8501"
echo "   🔌 Backend API:    http://localhost:8000"
echo "   📡 Mock API:       http://localhost:8001"
echo "   ❤️  Health Check:   http://localhost:8000/health"
echo ""
echo "📝 Process IDs:"
echo "   Mock API:    $MOCK_API_PID"
echo "   Backend:     $BACKEND_PID"
echo "   Dashboard:   $DASHBOARD_PID"
echo ""
echo "📄 Logs:"
echo "   tail -f logs/mock_api.log"
echo "   tail -f logs/backend.log"
echo "   tail -f logs/dashboard.log"
echo ""
echo "🛑 To stop all services:"
echo "   ./stop_all_services.sh"
echo "   or: kill $MOCK_API_PID $BACKEND_PID $DASHBOARD_PID"
echo ""

# Save PIDs to file
echo "$MOCK_API_PID" > .service_pids
echo "$BACKEND_PID" >> .service_pids
echo "$DASHBOARD_PID" >> .service_pids

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check health
echo ""
echo "🏥 Checking service health..."
curl -s http://localhost:8001/health > /dev/null && echo "   ✅ Mock API: Healthy" || echo "   ❌ Mock API: Not responding"
curl -s http://localhost:8000/health > /dev/null && echo "   ✅ Backend API: Healthy" || echo "   ❌ Backend API: Not responding"
curl -s http://localhost:8501/_stcore/health > /dev/null && echo "   ✅ Dashboard: Healthy" || echo "   ❌ Dashboard: Not responding"

echo ""
echo "🎉 Ready! Open http://localhost:8501 in your browser to access the dashboard."

