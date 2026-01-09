# 🚀 Best Way to Run the Email Pipeline Sequence

## 📋 Overview

There are **3 main ways** to run the email pipeline sequence, each optimized for different use cases:

1. **Manual Review Flow** (Recommended for Production) - Review emails before sending
2. **Automated Flow** (Direct Sending) - Fully automated, sends immediately
3. **Test/Development** - Mock all APIs for testing

---

## 🎯 Option 1: Manual Review Flow (RECOMMENDED)

**Best for**: Production use where you want to review emails before sending

### Step 1: Start Background Queue Builder

This continuously sources leads, generates emails, and stores them for review:

```bash
python3 scripts/start_queue_builder.py
```

**What it does**:
- Sources leads from Apollo (50 per batch)
- Prioritizes by ELM score
- Generates personalized emails with AI
- Creates HubSpot contacts
- Stores in database with `pending_review` status
- Runs continuously (refills queue when < 20 pending)

**Configuration** (via `.env` or `salesgpt/config/settings.py`):
```python
DEFAULT_GEOGRAPHY="New York, NY"
DEFAULT_SPECIALTY="Sales"
DEFAULT_BATCH_SIZE=50
```

### Step 2: Review & Send via Dashboard

Open the dashboard in your browser:
```bash
# Dashboard should already be running at:
http://localhost:8501
```

If not running, start it:
```bash
python3 -m streamlit run dashboard/streamlit_app.py --server.port 8501
```

**In Dashboard**:
1. Go to **"📧 Email Review"** tab
2. Review generated emails
3. Edit if needed
4. Click **"✅ APPROVE & SEND"** to send via Smartlead
5. Or **"⏭️ SKIP"** or **"🗑️ REJECT"** as needed

**Benefits**:
- ✅ Review every email before sending
- ✅ Edit email content if needed
- ✅ A/B testing built-in
- ✅ Full audit trail
- ✅ Can send 20+ emails per minute with fast review

---

## 🤖 Option 2: Automated Flow (Direct Sending)

**Best for**: Fully automated campaigns where you trust the AI

### Run the Full Pipeline

```bash
python3 main_agent.py --geography "New York, NY" --specialty "Sales" --limit 50
```

**What it does**:
1. Sources 50 leads from Apollo
2. Scores leads
3. Creates Smartlead campaign
4. Adds leads to Smartlead (emails sent automatically)
5. Creates HubSpot contacts
6. Stores in database

**Command-line options**:
```bash
python3 main_agent.py \
  --geography "Los Angeles, CA" \
  --specialty "Cardiology" \
  --limit 30 \
  --campaign "My Campaign Name"
```

**Configuration** (via `.env`):
```
APOLLO_API_KEY=your_key
SMARTLEAD_API_KEY=your_key
HUBSPOT_ACCESS_TOKEN=your_token
OPENAI_API_KEY=your_key
SMARTLEAD_FROM_EMAIL=noreply@yourdomain.com
SMARTLEAD_FROM_NAME=Your Name
```

**Benefits**:
- ✅ Fully automated
- ✅ No manual intervention needed
- ✅ Good for high-volume campaigns
- ⚠️ No email review (sends immediately)

---

## 🧪 Option 3: Test/Development Mode

**Best for**: Testing without using real API credits

### Run with Mock APIs

1. **Start Mock API Server**:
```bash
python3 mock_api_server.py
# Runs on http://localhost:8001
```

2. **Configure to use mock APIs** (in `.env`):
```
USE_MOCK_APIS=true
APOLLO_API_URL=http://localhost:8001
SMARTLEAD_API_URL=http://localhost:8001
HUBSPOT_API_URL=http://localhost:8001
```

3. **Run test pipeline**:
```bash
python3 tests/test_full_email_pipeline.py
```

Or use the real queue builder with mocked APIs:
```bash
python3 scripts/start_queue_builder.py
```

**Benefits**:
- ✅ No API costs
- ✅ Fast iteration
- ✅ Safe testing
- ✅ All APIs mocked

---

## 📊 Complete Setup (All Services)

### Terminal 1: Background Queue Builder
```bash
python3 scripts/start_queue_builder.py
```

### Terminal 2: Dashboard
```bash
python3 -m streamlit run dashboard/streamlit_app.py --server.port 8501
```

### Terminal 3: Webhook Handler (for reply processing)
```bash
python3 webhook_handler.py
# Handles Smartlead webhook replies
# Configure Smartlead webhook: http://your-domain:8000/webhook/smartlead
```

### Terminal 4: Mock API (if testing)
```bash
python3 mock_api_server.py
```

---

## 🎯 Recommended Production Workflow

### Daily Routine:

1. **Morning**: Start background queue builder
   ```bash
   python3 scripts/start_queue_builder.py &
   ```

2. **Throughout Day**: Review & send emails via dashboard
   - Open: http://localhost:8501
   - Review emails in "Email Review" tab
   - Approve and send high-quality emails
   - Monitor analytics in "Email Analytics" tab

3. **Evening**: Check analytics and optimize
   - Review A/B test results
   - Check Apollo config performance
   - Adjust targeting based on data

4. **24/7**: Webhook handler processes replies
   ```bash
   python3 webhook_handler.py &
   ```

---

## ⚙️ Advanced: Programmatic Usage

### Using Python API

```python
import asyncio
from salesgpt.container import ServiceContainer
from salesgpt.config import get_settings

async def run_custom_pipeline():
    settings = get_settings()
    container = ServiceContainer(settings)
    
    # Option A: Manual review flow
    await container.queue_builder.run(
        geography="New York, NY",
        specialty="Sales",
        batch_size=50,
        min_score=10
    )
    
    # Option B: Automated flow
    from main_agent import ASSCHOrchestrator
    orchestrator = ASSCHOrchestrator(
        apollo=container.apollo,
        smartlead=container.smartlead,
        salesgpt=container.salesgpt,
        scheduler=container.scheduler,
        crm=container.crm,
        visibility=container.visibility,
        competitor=container.competitor,
        scorer=container.scorer,
        state=container.state_manager,
        ab_manager=container.ab_test_manager,
        apollo_ab=container.apollo_ab_manager
    )
    
    await orchestrator.run_daily_pipeline(
        geography="New York, NY",
        specialty="Sales",
        lead_limit=50
    )

if __name__ == "__main__":
    asyncio.run(run_custom_pipeline())
```

---

## 🔧 Troubleshooting

### Queue Builder Not Finding Leads
- Check Apollo API key: `echo $APOLLO_API_KEY`
- Verify geography format: "City, State" or "City, Country"
- Check specialty spelling matches Apollo's taxonomy

### Dashboard Not Loading
- Check if Streamlit is installed: `pip install streamlit`
- Verify port 8501 is available: `lsof -i :8501`
- Check dashboard logs: `tail -f logs/dashboard.log`

### Emails Not Sending
- Verify Smartlead API key
- Check Smartlead campaign exists
- Ensure `SMARTLEAD_FROM_EMAIL` is configured
- Check Smartlead inbox warm-up status

### Database Errors
- Initialize database: `python -c "from salesgpt.db.connection import DatabaseManager; from salesgpt.models.database import Base; from salesgpt.config import get_settings; s = get_settings(); db = DatabaseManager(s.database_url); db.create_tables()"`
- Check database path in `.env`: `DATABASE_URL=sqlite:///./salesgpt.db`

---

## 📈 Performance Tips

### For High Volume (20+ emails/minute):

1. **Pre-generate queue**: Let queue builder run overnight
2. **Batch review**: Review 50-100 emails in one session
3. **Use bulk actions**: Dashboard supports "Approve Top 10"
4. **Optimize targeting**: Use Apollo A/B testing to find best configs
5. **Monitor bottlenecks**: Check dashboard analytics for slow points

### For Quality Over Speed:

1. **Manual review**: Review every email
2. **Edit before sending**: Use dashboard edit feature
3. **Higher min_score**: Set `min_score=15` in queue builder
4. **Smaller batches**: Use `batch_size=25` for better quality

---

## 🎓 Quick Reference

| Use Case | Command | Output |
|----------|---------|--------|
| **Manual Review** | `python3 scripts/start_queue_builder.py` | Database (pending_review) |
| **Automated Send** | `python3 main_agent.py --geography "NY, NY" --specialty "Sales"` | Smartlead (direct send) |
| **Test Mode** | `python3 tests/test_full_email_pipeline.py` | Mock APIs |
| **Dashboard** | `python3 -m streamlit run dashboard/streamlit_app.py` | http://localhost:8501 |
| **Webhook Handler** | `python3 webhook_handler.py` | Reply processing |

---

## ✅ Checklist Before Running

- [ ] All API keys configured in `.env`
- [ ] Database initialized
- [ ] Mock APIs running (if testing)
- [ ] Dashboard accessible (if manual review)
- [ ] Webhook handler running (if processing replies)
- [ ] Smartlead inbox warm-up complete
- [ ] HubSpot pipeline stages configured

---

**🎯 RECOMMENDED: Start with Option 1 (Manual Review Flow)** for the best balance of automation and quality control!

