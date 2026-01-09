#!/bin/bash
# Test deployment script - verifies all services are working

set -e

echo "🧪 Testing Deployment..."

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test functions
test_endpoint() {
    local url=$1
    local name=$2
    
    echo -n "Testing $name... "
    if curl -f -s "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}"
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        return 1
    fi
}

# Wait for services
echo "⏳ Waiting for services to start..."
sleep 5

# Test endpoints
echo ""
echo "📋 Testing Service Endpoints:"
echo ""

FAILED=0

# Mock API Server
test_endpoint "http://localhost:8001/health" "Mock API Server Health" || FAILED=1
test_endpoint "http://localhost:8001/" "Mock API Server Root" || FAILED=1

# Backend API
test_endpoint "http://localhost:8000/health" "Backend API Health" || FAILED=1

# Dashboard
test_endpoint "http://localhost:8501/_stcore/health" "Dashboard Health" || FAILED=1

# Test Mock API endpoints
echo ""
echo "📋 Testing Mock API Endpoints:"
echo ""

# Test Apollo search
echo -n "Testing Apollo Search... "
RESPONSE=$(curl -s -X POST http://localhost:8001/v1/mixed_people/search \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: mock_key" \
  -d '{"api_key": "mock_key", "per_page": 5}')
if echo "$RESPONSE" | grep -q "people"; then
    echo -e "${GREEN}✅ PASS${NC}"
else
    echo -e "${RED}❌ FAIL${NC}"
    FAILED=1
fi

# Test Smartlead campaign creation
echo -n "Testing Smartlead Campaign... "
RESPONSE=$(curl -s -X POST http://localhost:8001/api/v1/campaigns \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: mock_key" \
  -d '{"name": "Test Campaign", "from_email": "test@example.com", "from_name": "Test"}')
if echo "$RESPONSE" | grep -q "campaign_id"; then
    echo -e "${GREEN}✅ PASS${NC}"
else
    echo -e "${RED}❌ FAIL${NC}"
    FAILED=1
fi

# Test HubSpot contact creation
echo -n "Testing HubSpot Contact... "
RESPONSE=$(curl -s -X POST http://localhost:8001/crm/v3/objects/contacts \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer mock_token" \
  -d '{"properties": {"email": "test@example.com", "firstname": "Test", "lastname": "User"}}')
if echo "$RESPONSE" | grep -q "id"; then
    echo -e "${GREEN}✅ PASS${NC}"
else
    echo -e "${RED}❌ FAIL${NC}"
    FAILED=1
fi

# Summary
echo ""
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo ""
    echo "🚀 Deployment is working correctly!"
    echo ""
    echo "Access services at:"
    echo "  - Dashboard: http://localhost:8501"
    echo "  - Backend API: http://localhost:8000"
    echo "  - Mock API: http://localhost:8001"
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Check service logs.${NC}"
    echo ""
    echo "View logs with:"
    echo "  docker-compose -f deployment/docker-compose.deploy.yml logs"
    exit 1
fi

