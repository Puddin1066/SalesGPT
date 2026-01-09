# Deployment Guide

## Quick Start

### 1. Deploy with Mock APIs (Recommended for Development)

```bash
# Make deployment script executable
chmod +x deployment/deploy.sh

# Run deployment
./deployment/deploy.sh
```

This will:
- ✅ Create `.env` file if it doesn't exist
- ✅ Run database migrations
- ✅ Build all Docker containers
- ✅ Start all services (Mock API, Backend, Dashboard, Queue Builder)
- ✅ Check service health

### 2. Access Services

- **Dashboard**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **Mock API Server**: http://localhost:8001
- **Health Check**: http://localhost:8000/health

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Database
DATABASE_URL=sqlite:///./salesgpt.db

# Mock API Configuration
USE_MOCK_APIS=true
MOCK_API_URL=http://localhost:8001

# API URLs (automatically point to mock server when USE_MOCK_APIS=true)
APOLLO_API_URL=http://localhost:8001
SMARTLEAD_API_URL=http://localhost:8001
HUBSPOT_API_URL=http://localhost:8001

# API Keys (can be mock keys when using mock APIs)
APOLLO_API_KEY=mock_key
SMARTLEAD_API_KEY=mock_key
HUBSPOT_ACCESS_TOKEN=mock_token
OPENAI_API_KEY=your_openai_key_here

# Webhook
WEBHOOK_PORT=8000
WEBHOOK_SECRET_KEY=dev_secret_key

# Default Settings
DEFAULT_GEOGRAPHY=New York, NY
DEFAULT_SPECIALTY=Dermatology
DEFAULT_BATCH_SIZE=50
```

### Using Real APIs

To use real APIs instead of mocks:

```bash
# Set USE_MOCK_APIS=false
USE_MOCK_APIS=false

# Set real API URLs
APOLLO_API_URL=https://api.apollo.io/v1
SMARTLEAD_API_URL=https://server.smartlead.ai/api/v1
HUBSPOT_API_URL=https://api.hubapi.com

# Set real API keys
APOLLO_API_KEY=your_real_apollo_key
SMARTLEAD_API_KEY=your_real_smartlead_key
HUBSPOT_ACCESS_TOKEN=your_real_hubspot_token
```

## Services

### Mock API Server

Provides mock endpoints for:
- **Apollo.io**: `/v1/mixed_people/search`, `/v1/people/{id}`, `/v1/organizations/{id}`
- **Smartlead**: `/api/v1/campaigns`, `/api/v1/campaigns/{id}/leads`, `/api/v1/replies/send`
- **HubSpot**: `/crm/v3/objects/contacts`, `/crm/v3/objects/deals`

**Features:**
- In-memory storage for testing
- Realistic response structures
- Supports all required endpoints

### Backend API

- **Webhook Handler**: Processes Smartlead webhook events
- **Health Check**: `/health` endpoint
- **Port**: 8000

### Dashboard

- **Streamlit Dashboard**: Email review and analytics
- **Port**: 8501
- **Features**: Email review, A/B testing analytics, optimization recommendations

### Queue Builder

- **Background Worker**: Continuously sources leads and generates emails
- **Automatic**: Runs in background, refills queue when needed

## Docker Commands

### Start Services

```bash
docker-compose -f deployment/docker-compose.deploy.yml up -d
```

### Stop Services

```bash
docker-compose -f deployment/docker-compose.deploy.yml down
```

### View Logs

```bash
# All services
docker-compose -f deployment/docker-compose.deploy.yml logs -f

# Specific service
docker-compose -f deployment/docker-compose.deploy.yml logs -f backend
docker-compose -f deployment/docker-compose.deploy.yml logs -f mock-api
docker-compose -f deployment/docker-compose.deploy.yml logs -f dashboard
```

### Rebuild Services

```bash
docker-compose -f deployment/docker-compose.deploy.yml build --no-cache
docker-compose -f deployment/docker-compose.deploy.yml up -d
```

## Development Mode

### Run Services Locally (Without Docker)

#### 1. Start Mock API Server

```bash
python3 mock_api_server.py
```

#### 2. Start Backend API

```bash
python3 webhook_handler.py
```

#### 3. Start Dashboard

```bash
streamlit run dashboard/streamlit_app.py
```

#### 4. Start Queue Builder

```bash
python3 scripts/start_queue_builder.py
```

## Testing

### Test Mock API Server

```bash
# Health check
curl http://localhost:8001/health

# Apollo search
curl -X POST http://localhost:8001/v1/mixed_people/search \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: mock_key" \
  -d '{"api_key": "mock_key", "per_page": 10}'

# Smartlead create campaign
curl -X POST http://localhost:8001/api/v1/campaigns \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: mock_key" \
  -d '{"name": "Test Campaign", "from_email": "test@example.com", "from_name": "Test"}'
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=services --cov=workflows --cov-report=html
```

## Production Deployment

### Using Real APIs

1. Update `.env` with production API keys
2. Set `USE_MOCK_APIS=false`
3. Update API URLs to production endpoints
4. Deploy using Docker Compose or Kubernetes

### Using PostgreSQL (Production Database)

Update `docker-compose.deploy.yml`:

```yaml
environment:
  - DATABASE_URL=postgresql://salesgpt:password@db:5432/salesgpt
```

### Security Considerations

- ✅ Use environment variables for secrets (never commit to git)
- ✅ Enable webhook signature verification
- ✅ Use HTTPS in production
- ✅ Set up proper firewall rules
- ✅ Use secrets management (AWS Secrets Manager, HashiCorp Vault, etc.)

## Troubleshooting

### Services Not Starting

```bash
# Check logs
docker-compose -f deployment/docker-compose.deploy.yml logs

# Check service status
docker-compose -f deployment/docker-compose.deploy.yml ps

# Restart services
docker-compose -f deployment/docker-compose.deploy.yml restart
```

### Database Migration Issues

```bash
# Run migrations manually
python3 -m alembic upgrade head

# Reset database (WARNING: Deletes all data)
rm salesgpt.db
python3 -m alembic upgrade head
```

### Port Conflicts

If ports are already in use:

```bash
# Find process using port
lsof -i :8000
lsof -i :8001
lsof -i :8501

# Kill process or change ports in docker-compose.deploy.yml
```

## Monitoring

### Health Checks

All services have health check endpoints:
- Mock API: `http://localhost:8001/health`
- Backend: `http://localhost:8000/health`
- Dashboard: `http://localhost:8501/_stcore/health`

### Metrics

Monitor service health:
```bash
# Check all services
curl http://localhost:8001/health
curl http://localhost:8000/health
curl http://localhost:8501/_stcore/health
```

## Support

For issues or questions:
1. Check logs: `docker-compose -f deployment/docker-compose.deploy.yml logs`
2. Check service health endpoints
3. Review configuration in `.env`
4. Check Docker container status: `docker ps`

