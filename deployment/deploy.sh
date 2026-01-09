#!/bin/bash
# Deployment script for SalesGPT Email Platform

set -e

echo "🚀 Deploying SalesGPT Email Platform..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cat > .env << EOF
# Database
DATABASE_URL=sqlite:///./salesgpt.db

# API Keys (use mock APIs if not set)
APOLLO_API_KEY=mock_key
SMARTLEAD_API_KEY=mock_key
HUBSPOT_ACCESS_TOKEN=mock_token
OPENAI_API_KEY=your_openai_key_here

# Mock API Configuration
USE_MOCK_APIS=true
MOCK_API_URL=http://localhost:8001

# Service URLs (point to mock server when mocking)
APOLLO_API_URL=http://localhost:8001
SMARTLEAD_API_URL=http://localhost:8001
HUBSPOT_API_URL=http://localhost:8001

# Webhook
WEBHOOK_PORT=8000
WEBHOOK_SECRET_KEY=dev_secret_key

# Default Settings
DEFAULT_GEOGRAPHY=New York, NY
DEFAULT_SPECIALTY=Dermatology
DEFAULT_BATCH_SIZE=50
QUEUE_REFILL_THRESHOLD=20

# Analytics
AB_TESTING_ENABLED=true
MIN_SAMPLE_SIZE_FOR_RECOMMENDATIONS=10
EOF
    echo "✅ Created .env file. Please update with your API keys."
fi

# Run database migrations
echo "📊 Running database migrations..."
python3 -m alembic upgrade head || echo "⚠️  Alembic not configured, skipping migrations"

# Build and start services
echo "🐳 Building Docker containers..."
docker-compose -f deployment/docker-compose.deploy.yml build

echo "🚀 Starting services..."
docker-compose -f deployment/docker-compose.deploy.yml up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo "🏥 Checking service health..."
curl -f http://localhost:8001/health && echo "✅ Mock API Server: Healthy" || echo "❌ Mock API Server: Unhealthy"
curl -f http://localhost:8000/health && echo "✅ Backend API: Healthy" || echo "❌ Backend API: Unhealthy"
curl -f http://localhost:8501/_stcore/health && echo "✅ Dashboard: Healthy" || echo "❌ Dashboard: Unhealthy"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 Service URLs:"
echo "   - Mock API Server: http://localhost:8001"
echo "   - Backend API: http://localhost:8000"
echo "   - Dashboard: http://localhost:8501"
echo "   - Health Check: http://localhost:8000/health"
echo ""
echo "📝 To view logs:"
echo "   docker-compose -f deployment/docker-compose.deploy.yml logs -f"
echo ""
echo "🛑 To stop services:"
echo "   docker-compose -f deployment/docker-compose.deploy.yml down"

