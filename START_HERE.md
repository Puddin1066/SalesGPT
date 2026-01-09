# 🚀 Start Here - Deploy Locally in Browser

## Quick Deployment Steps

### Step 1: Install Missing Dependencies

```bash
# Install Streamlit for dashboard
python3 -m pip install --user streamlit plotly pandas

# Or if that fails, use:
pip3 install streamlit plotly pandas --break-system-packages
```

### Step 2: Start Services (3 Terminals)

#### Terminal 1: Mock API Server
```bash
cd /Users/JJR/SalesGPT
python3 mock_api_server.py
```
**Keep this running** - You should see: `INFO:     Uvicorn running on http://0.0.0.0:8001`

#### Terminal 2: Backend API  
```bash
cd /Users/JJR/SalesGPT
python3 webhook_handler.py
```
**Keep this running** - You should see the API starting on port 8000

#### Terminal 3: Dashboard
```bash
cd /Users/JJR/SalesGPT
streamlit run dashboard/streamlit_app.py --server.port 8501 --server.address localhost
```
**Keep this running** - Streamlit will automatically open your browser!

## 🌐 Access URLs

Once all 3 terminals are running:

1. **📊 Dashboard**: http://localhost:8501
   - **This is your main interface!**
   - Email review and approval
   - Analytics and A/B testing

2. **🔌 Backend API**: http://localhost:8000
   - Health: http://localhost:8000/health

3. **📡 Mock API**: http://localhost:8001
   - Health: http://localhost:8001/health

## ✅ Verify It's Working

Open these URLs in your browser:

1. http://localhost:8001/health - Should show: `{"status":"healthy"...}`
2. http://localhost:8000/health - Should show: `{"status":"healthy"}`
3. http://localhost:8501 - Should show the Streamlit dashboard!

## 🎯 What You'll See

The **Dashboard** (http://localhost:8501) has 4 tabs:

1. **📧 Email Review** - Review and approve emails
2. **📊 Email Analytics** - A/B test results
3. **🔍 Apollo A/B Testing** - Lead sourcing optimization
4. **🎯 Optimization** - AI recommendations

## 🛑 To Stop

Press `Ctrl+C` in each terminal window, or run:
```bash
./stop_all_services.sh
```

## 🔧 Troubleshooting

### "Module not found" errors?

Install missing packages:
```bash
python3 -m pip install --user <package_name>
```

### Port already in use?

Kill processes on ports:
```bash
lsof -ti:8000 | xargs kill -9
lsof -ti:8001 | xargs kill -9
lsof -ti:8501 | xargs kill -9
```

### Dashboard won't load?

1. Check Streamlit is installed: `streamlit --version`
2. Check it's running: Look for "You can now view your Streamlit app in your browser"
3. Manually open: http://localhost:8501

## 📝 Environment Variables

Create `.env` file (optional - defaults work for mocks):
```bash
cp deployment/env.example .env
```

## 🎉 Ready!

Once all 3 services are running, your **Dashboard** will be available at:
**http://localhost:8501**

Open it in your browser and start reviewing emails! 📧

