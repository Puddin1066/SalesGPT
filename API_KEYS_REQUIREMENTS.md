# 🔑 API Keys Requirements & What Will Work

## ✅ Yes, the dashboard will work once you add API keys!

The dashboard is designed to work with real API keys. Here's what you need and what will work:

---

## 📋 Required API Keys

### **Critical (Required for Core Functionality)**

1. **OpenAI API Key** (`OPENAI_API_KEY`)
   - **Purpose**: AI email generation and reply handling
   - **Required for**: 
     - Generating personalized emails
     - Analyzing replies
     - Intent classification
   - **Where to get**: https://platform.openai.com/api-keys
   - **Cost**: Pay-per-use (GPT-3.5-turbo is ~$0.0015 per 1K tokens)

2. **Apollo API Key** (`APOLLO_API_KEY`)
   - **Purpose**: Lead sourcing and enrichment
   - **Required for**:
     - Finding leads
     - Enriching contact data
     - Lead scoring
   - **Where to get**: https://app.apollo.io/#/settings/integrations/api
   - **Cost**: Varies by plan (some plans include free searches)

3. **Smartlead API Key** (`SMARTLEAD_API_KEY`)
   - **Purpose**: Email delivery infrastructure
   - **Required for**:
     - Actually sending emails
     - Email sequences
     - Reply webhooks
   - **Where to get**: https://app.smartlead.ai/settings/api
   - **Cost**: Subscription-based

4. **HubSpot Access Token** (`HUBSPOT_ACCESS_TOKEN` or OAuth)
   - **Purpose**: CRM contact management
   - **Required for**:
     - Creating contacts
     - Updating pipeline stages
     - Storing email content
   - **Where to get**: 
     - Private App: https://app.hubspot.com/settings/integrations/private-apps
     - OAuth: https://developers.hubspot.com/docs/api/working-with-oauth
   - **Cost**: Free tier available

---

## 🔧 Optional API Keys

5. **GEMflush API Key** (`GEMFLUSH_API_KEY`)
   - **Purpose**: Visibility audits and competitive analysis
   - **Status**: Optional (system has LLM-based simulation fallback)
   - **Required for**: Real competitive data (not required for testing)
   - **Where to get**: Contact alex@gemflush.com

6. **Cal.com Booking Link** (`CAL_BOOKING_LINK`)
   - **Purpose**: Generate booking links for interested leads
   - **Status**: Optional (can be added later)
   - **Required for**: Automated booking links

---

## 🎯 What Will Work With API Keys

### ✅ **Dashboard Features**

1. **Email Review Tab**
   - ✅ Load and display leads from database
   - ✅ Show email content (subject/body)
   - ✅ Edit email content
   - ✅ Approve and send emails (via Smartlead)
   - ✅ Skip/reject leads
   - ✅ View lead details and scores

2. **Email Analytics Tab**
   - ✅ Display performance metrics
   - ✅ Show A/B test variant performance
   - ✅ Display conversion funnels
   - ✅ Niche performance analysis

3. **Apollo A/B Testing Tab**
   - ✅ Show Apollo config performance
   - ✅ Display multi-armed bandit results
   - ✅ Configuration comparison

4. **Optimization Tab**
   - ✅ AI-powered recommendations
   - ✅ Performance improvement suggestions

### ✅ **Background Queue Builder**

Once API keys are added, you can run:

```bash
python3 scripts/start_queue_builder.py
```

This will:
- ✅ Source leads from Apollo
- ✅ Generate personalized emails (OpenAI)
- ✅ Create HubSpot contacts
- ✅ Store leads in database for review
- ✅ Assign A/B test variants

### ✅ **Full Pipeline**

With all API keys, the complete flow works:

```
1. Apollo → Sources leads ✅
2. SalesGPT → Generates emails ✅
3. HubSpot → Creates contacts ✅
4. Dashboard → Review emails ✅
5. Smartlead → Sends emails ✅
6. Webhook → Handles replies ✅
7. SalesGPT → Generates responses ✅
8. HubSpot → Updates pipeline ✅
```

---

## ⚠️ What Happens Without API Keys

### **Current Behavior (Without Keys)**

The dashboard has **graceful error handling**:

1. **Dashboard loads** but shows warning:
   ```
   ⚠️ Error initializing services: ValueError
   Dashboard will work in read-only mode. Some features may be limited.
   ```

2. **What still works**:
   - ✅ View existing leads in database
   - ✅ View analytics (if data exists)
   - ✅ Navigate all tabs
   - ✅ See UI components

3. **What doesn't work**:
   - ❌ Generate new emails
   - ❌ Source new leads
   - ❌ Send emails
   - ❌ Create HubSpot contacts
   - ❌ Update pipeline stages

### **With Mock APIs (For Testing)**

You can test without real API keys by using mock APIs:

```bash
# Set in .env
USE_MOCK_APIS=true
APOLLO_API_URL=http://localhost:8001
SMARTLEAD_API_URL=http://localhost:8001
HUBSPOT_API_URL=http://localhost:8001
```

Then run the mock API server:
```bash
python3 mock_api_server.py
```

This allows you to:
- ✅ Test the full flow
- ✅ See how everything works
- ✅ Develop without API costs
- ❌ Won't send real emails
- ❌ Won't source real leads

---

## 🔧 Setting Up API Keys

### **Step 1: Create `.env` File**

```bash
# Required
OPENAI_API_KEY=sk-...
APOLLO_API_KEY=...
SMARTLEAD_API_KEY=...
HUBSPOT_ACCESS_TOKEN=...

# Optional
GEMFLUSH_API_KEY=...
CAL_BOOKING_LINK=https://cal.com/your-link

# Smartlead Configuration
SMARTLEAD_FROM_EMAIL=your-email@domain.com
SMARTLEAD_FROM_NAME=Your Name
SMARTLEAD_CAMPAIGN_NAME=My Campaign

# Database (defaults to SQLite)
DATABASE_URL=sqlite:///./salesgpt.db
```

### **Step 2: Verify Keys Work**

Test each service:

```bash
# Test Apollo
python3 -c "from services.apollo.apollo_agent import ApolloAgent; a = ApolloAgent(); print('✅ Apollo OK')"

# Test Smartlead
python3 -c "from services.outbound.smartlead_agent import SmartleadAgent; s = SmartleadAgent(); print('✅ Smartlead OK')"

# Test HubSpot
python3 -c "from services.crm.hubspot_agent import HubSpotAgent; h = HubSpotAgent(); print('✅ HubSpot OK')"
```

### **Step 3: Start Dashboard**

```bash
streamlit run dashboard/streamlit_app.py
```

The dashboard will:
- ✅ Initialize all services
- ✅ Connect to database
- ✅ Be ready to use

---

## 🚀 What Happens After Adding Keys

### **Immediate Benefits**

1. **Dashboard fully functional**:
   - All tabs work
   - No error warnings
   - Full feature access

2. **Can generate emails**:
   - Run queue builder
   - Generate personalized emails
   - Review in dashboard

3. **Can send emails**:
   - Approve emails in dashboard
   - Smartlead sends them
   - Track delivery

4. **Can handle replies**:
   - Webhook receives replies
   - SalesGPT analyzes intent
   - Generates responses

5. **Can track in CRM**:
   - HubSpot contacts created
   - Pipeline stages updated
   - Deals tracked

---

## 📊 Feature Matrix

| Feature | Without Keys | With Mock APIs | With Real Keys |
|---------|-------------|----------------|---------------|
| **View Dashboard** | ✅ Yes | ✅ Yes | ✅ Yes |
| **View Existing Data** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Generate Emails** | ❌ No | ✅ Yes (mock) | ✅ Yes (real) |
| **Source Leads** | ❌ No | ✅ Yes (mock) | ✅ Yes (real) |
| **Send Emails** | ❌ No | ✅ Yes (mock) | ✅ Yes (real) |
| **Handle Replies** | ❌ No | ✅ Yes (mock) | ✅ Yes (real) |
| **Update CRM** | ❌ No | ✅ Yes (mock) | ✅ Yes (real) |
| **Analytics** | ⚠️ Limited | ✅ Yes | ✅ Yes |

---

## ✅ Summary

**Yes, the dashboard will work once you add API keys!**

1. **Add API keys** to `.env` file
2. **Restart dashboard** (or refresh browser)
3. **All features work** - no more errors
4. **Full pipeline operational** - can source, generate, send, and track

The dashboard is designed to:
- ✅ Handle missing keys gracefully (read-only mode)
- ✅ Work fully with real keys
- ✅ Support mock APIs for testing

**Next Steps**:
1. Get API keys from each service
2. Add to `.env` file
3. Restart dashboard
4. Start using! 🚀



