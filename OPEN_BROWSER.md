# 🚀 Local Deployment - Browser Access

## Quick Start

### Option 1: Use the Simple Launcher (Recommended)

```bash
python3 start_services_simple.py
```

This will:
- ✅ Start all services automatically
- ✅ Check dependencies
- ✅ Open browser to dashboard
- ✅ Show service URLs
- ✅ Keep services running until Ctrl+C

### Option 2: Manual Start

#### Terminal 1: Mock API Server
```bash
python3 mock_api_server.py
```
Access: http://localhost:8001

#### Terminal 2: Backend API
```bash
python3 webhook_handler.py
```
Access: http://localhost:8000

#### Terminal 3: Dashboard
```bash
streamlit run dashboard/streamlit_app.py
```
Access: http://localhost:8501

## 🌐 Browser URLs

Once services are running, access them at:

- **📊 Dashboard (Main Interface)**: http://localhost:8501
  - Email review and approval
  - A/B testing analytics
  - Apollo optimization
  - Recommendations

- **🔌 Backend API**: http://localhost:8000
  - Webhook handler
  - Health check: http://localhost:8000/health

- **📡 Mock API Server**: http://localhost:8001
  - Mock Apollo, Smartlead, HubSpot endpoints
  - Health check: http://localhost:8001/health

## 📝 Environment Setup

If you haven't already, create a `.env` file:

```bash
cp deployment/env.example .env
```

Or manually create `.env` with:

```env
# Mock API URLs
APOLLO_API_URL=http://localhost:8001
SMARTLEAD_API_URL=http://localhost:8001
HUBSPOT_API_URL=http://localhost:8001

# API Keys (can be mock keys)
APOLLO_API_KEY=mock_key
SMARTLEAD_API_KEY=mock_key
HUBSPOT_ACCESS_TOKEN=mock_token
OPENAI_API_KEY=your_key_here

# Database
DATABASE_URL=sqlite:///./salesgpt.db

# Webhook
WEBHOOK_PORT=8000
WEBHOOK_SECRET_KEY=dev_secret
```

## 🔧 Troubleshooting

### Services won't start?

1. **Check dependencies**:
   ```bash
   pip3 install fastapi uvicorn streamlit plotly pandas slowapi
   ```

2. **Check ports are free**:
   ```bash
   lsof -i :8000
   lsof -i :8001
   lsof -i :8501
   ```

3. **Kill existing processes**:
   ```bash
   ./stop_all_services.sh
   ```

### Dashboard not loading?

1. Check Streamlit is installed: `pip3 install streamlit`
2. Check logs: `tail -f logs/dashboard.log`
3. Try accessing directly: http://localhost:8501

### Backend API errors?

1. Check database exists: `ls -la salesgpt.db`
2. Run migrations: `alembic upgrade head`
3. Check logs: `tail -f logs/backend.log`

## 📄 View Logs

```bash
# All services
tail -f logs/*.log

# Individual services
tail -f logs/mock_api.log
tail -f logs/backend.log
tail -f logs/dashboard.log
```

## 🛑 Stop Services

```bash
./stop_all_services.sh
```

Or press `Ctrl+C` if using the simple launcher.

## ✅ Success Indicators

You'll know everything is working when:

1. ✅ Mock API responds at http://localhost:8001/health
2. ✅ Backend API responds at http://localhost:8000/health
3. ✅ Dashboard loads at http://localhost:8501
4. ✅ You can see the email review interface

## 🎯 Next Steps

Once deployed:

1. **Access Dashboard**: Open http://localhost:8501
2. **Review Queue**: Go to "Email Review" tab
3. **Start Queue Builder**: Run `python3 scripts/start_queue_builder.py` in another terminal to populate the queue
4. **Review Analytics**: Check "Email Analytics" tab for A/B test results

Happy emailing! 📧

