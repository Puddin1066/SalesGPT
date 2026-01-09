# Quick Start Deployment Guide

## 🚀 Deploy in 3 Steps

### Step 1: Prepare Environment

```bash
# Copy example environment file
cp deployment/env.example .env

# Edit .env with your settings (optional for mock APIs)
nano .env
```

### Step 2: Deploy

```bash
# Run deployment script
./deployment/deploy.sh
```

### Step 3: Verify

```bash
# Test deployment
./deployment/test_deployment.sh
```

## ✅ That's It!

Your services are now running:
- **Dashboard**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **Mock API Server**: http://localhost:8001

## 📝 What's Deployed?

1. **Mock API Server** - Simulates Apollo, Smartlead, and HubSpot APIs
2. **Backend API** - Webhook handler and core services
3. **Dashboard** - Streamlit interface for email review and analytics
4. **Queue Builder** - Background worker for lead sourcing

## 🔧 Using Real APIs

To switch to real APIs:

1. Update `.env`:
   ```bash
   USE_MOCK_APIS=false
   APOLLO_API_URL=https://api.apollo.io/v1
   SMARTLEAD_API_URL=https://server.smartlead.ai/api/v1
   HUBSPOT_API_URL=https://api.hubapi.com
   ```

2. Add real API keys:
   ```bash
   APOLLO_API_KEY=your_real_key
   SMARTLEAD_API_KEY=your_real_key
   HUBSPOT_ACCESS_TOKEN=your_real_token
   OPENAI_API_KEY=your_openai_key
   ```

3. Restart services:
   ```bash
   docker-compose -f deployment/docker-compose.deploy.yml restart
   ```

## 🛑 Stop Services

```bash
docker-compose -f deployment/docker-compose.deploy.yml down
```

## 📚 Full Documentation

See [DEPLOYMENT_README.md](./DEPLOYMENT_README.md) for detailed documentation.

