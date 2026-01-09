#!/bin/bash
# Run E2E test with mocked API responses

set -e

echo "🚀 Starting E2E Test with Mocked APIs"
echo "======================================"
echo ""

# Set environment variables for mock APIs
export APOLLO_API_URL="http://localhost:8001"
export SMARTLEAD_API_URL="http://localhost:8001"
export HUBSPOT_API_URL="http://localhost:8001"
export USE_MOCK_APIS="true"

# Set required API keys (can be dummy values for mocks)
export APOLLO_API_KEY="mock_apollo_key"
export SMARTLEAD_API_KEY="mock_smartlead_key"
export HUBSPOT_ACCESS_TOKEN="mock_hubspot_token"
export OPENAI_API_KEY="${OPENAI_API_KEY:-sk-test-key}"  # Use real OpenAI key if available

# Set other required config
export SMARTLEAD_FROM_EMAIL="test@example.com"
export SMARTLEAD_FROM_NAME="Test Sender"
export SMARTLEAD_CAMPAIGN_NAME="Test Campaign"

# Database
export DATABASE_URL="sqlite:///./test_salesgpt_e2e.db"

# Default settings
export DEFAULT_GEOGRAPHY="New York, NY"
export DEFAULT_SPECIALTY="Dental"
export DEFAULT_BATCH_SIZE="10"  # Smaller batch for testing

echo "📋 Configuration:"
echo "   Apollo API: $APOLLO_API_URL"
echo "   Smartlead API: $SMARTLEAD_API_URL"
echo "   HubSpot API: $HUBSPOT_API_URL"
echo "   Database: $DATABASE_URL"
echo "   Geography: $DEFAULT_GEOGRAPHY"
echo "   Specialty: $DEFAULT_SPECIALTY"
echo "   Batch Size: $DEFAULT_BATCH_SIZE"
echo ""

# Check if mock API server is running
echo "🔍 Checking if mock API server is running..."
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "   ✅ Mock API server is running"
else
    echo "   ⚠️  Mock API server not running, starting it..."
    python3 mock_api_server.py &
    MOCK_API_PID=$!
    sleep 3
    
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo "   ✅ Mock API server started (PID: $MOCK_API_PID)"
    else
        echo "   ❌ Failed to start mock API server"
        exit 1
    fi
fi

echo ""
echo "🎯 Starting Queue Builder (E2E Test)..."
echo "   This will:"
echo "   1. Source 10 leads from Apollo (mocked)"
echo "   2. Generate personalized emails with GEMflush evidence"
echo "   3. Create HubSpot contacts (mocked)"
echo "   4. Store everything in database"
echo ""
echo "   Press Ctrl+C to stop after processing"
echo ""

# Run the queue builder
python3 scripts/start_queue_builder.py

echo ""
echo "✅ E2E test completed!"
echo ""
echo "📊 Check results:"
echo "   Database: $DATABASE_URL"
echo "   View in dashboard: python3 -m streamlit run dashboard/streamlit_app.py"

