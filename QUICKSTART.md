# A.S.S.C.H. Assembly - Quick Start Guide

## 🚀 5-Minute Setup

### Step 1: Install Dependencies
```bash
pip install -r requirements-assch.txt
```

### Step 2: Configure Environment
```bash
cp .env.example .env.local
# Edit .env.local with your API keys
```

**Required API Keys:**
- `APOLLO_API_KEY` - Lead sourcing
- `SMARTLEAD_API_KEY` - Email delivery
- `HUBSPOT_API_KEY` - CRM management
- `GEMFLUSH_API_KEY` - Visibility audits
- `OPENAI_API_KEY` - SalesGPT replies (or `OPENROUTER_API_KEY` for OpenRouter)
- `CAL_BOOKING_LINK` - Your Cal.com link

### Step 2.5: Using OpenRouter (Optional)
If you have an OpenRouter account, set `OPENROUTER_API_KEY` and use an OpenRouter model prefix:
```bash
# In your .env.local
OPENROUTER_API_KEY=your_openrouter_key
GPT_MODEL=openrouter/openai/gpt-4o  # Example OpenRouter model
```

### Step 3: Run Daily Pipeline
```bash
python main_agent.py --geography "New York, NY" --specialty "Dermatology" --limit 20
```

### Step 4: Start Webhook Server
```bash
python webhook_handler.py
# Configure Smartlead webhook: http://your-domain.com/webhook/smartlead
```

## 📋 What Happens Next?

1. **Apollo** finds 20 leads matching your criteria
2. **Smartlead** sends initial email sequence
3. When leads reply, **webhook** triggers
4. **SalesGPT** generates contextual response
5. If interested → **Cal.com** booking link sent
6. If curious → **GEMflush** evidence injected
7. **HubSpot** tracks pipeline stages

## 🔍 Verify Setup

```python
# Test Apollo
from services.apollo import ApolloAgent
apollo = ApolloAgent()
leads = apollo.search_leads("New York, NY", "Dermatology", limit=5)
print(f"✅ Found {len(leads)} leads")

# Test State Manager
from state import StateManager
state = StateManager()
print("✅ State manager initialized")
```

## 📚 Full Documentation

See `ASSCH_README.md` for complete documentation.
