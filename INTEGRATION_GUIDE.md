# A.S.S.C.H. Assembly - Integration Guide

## Overview

**A.S.S.C.H. Assembly** is an automated sales pipeline that orchestrates multiple services to:
1. Find leads (Apollo)
2. Send email sequences (Smartlead)
3. Generate AI-powered replies (SalesGPT)
4. Schedule meetings (Cal.com)
5. Track pipeline stages (HubSpot)
6. Provide competitive insights (GEMflush)

## How It Works

### Architecture Flow

```
┌─────────────┐
│   Apollo    │ → Lead Sourcing + Enrichment
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Smartlead  │ → Email Sequences + Delivery
└──────┬──────┘
       │
       ▼ (Webhook)
┌─────────────┐
│  SalesGPT   │ → Reply Generation + Intent Classification
└──────┬──────┘
       │
       ├─→ Interested? → Cal.com Booking Link
       ├─→ Curious? → GEMflush Evidence
       └─→ Objection? → GEMflush Full Audit
       │
       ▼
┌─────────────┐
│  HubSpot    │ → Pipeline Stage Updates
└─────────────┘
```

### Daily Pipeline Process

1. **Lead Sourcing** (`main_agent.py`)
   - Apollo searches for leads by geography and specialty
   - Leads are scored based on website presence, title relevance, employee count
   - Top-scored leads are selected

2. **Email Campaign Setup**
   - Smartlead campaign is created/retrieved
   - Email sequences are configured (initial + follow-up)
   - Leads are added to the campaign

3. **CRM Integration**
   - Contacts are created in HubSpot
   - Lead states are persisted locally (JSON files)

4. **Reply Handling** (`webhook_handler.py`)
   - When leads reply via Smartlead, webhook triggers
   - SalesGPT analyzes the reply and classifies intent:
     - **Interested** → Sends Cal.com booking link, updates HubSpot to "booked"
     - **Curious/Neutral** → Injects GEMflush competitive evidence
     - **Objection** → Provides full GEMflush audit with detailed comparison
   - AI-generated reply is sent back via Smartlead
   - Conversation history is saved

## Required Integrations

### 1. Apollo API
**Purpose**: Lead sourcing and enrichment  
**Required**: `APOLLO_API_KEY`  
**Setup**:
- Sign up at [Apollo.io](https://www.apollo.io/)
- Get your API key from settings
- Add to `.env.local`: `APOLLO_API_KEY=your_key_here`

**What it does**:
- Searches for leads by location, specialty, job title
- Enriches lead data with company info, website, LinkedIn
- Returns scored leads ready for outreach

### 2. Smartlead API
**Purpose**: Email delivery and sequence management  
**Required**: `SMARTLEAD_API_KEY`, `SMARTLEAD_FROM_EMAIL`, `SMARTLEAD_FROM_NAME`, `SMARTLEAD_REPLY_TO`  
**Setup**:
- Sign up at [Smartlead.ai](https://www.smartlead.ai/)
- Get your API key
- Configure sending domain and mailboxes
- Add to `.env.local`:
  ```
  SMARTLEAD_API_KEY=your_key_here
  SMARTLEAD_FROM_EMAIL=noreply@yourdomain.com
  SMARTLEAD_FROM_NAME=Your Name
  SMARTLEAD_REPLY_TO=noreply@yourdomain.com
  ```

**What it does**:
- Creates email campaigns
- Manages email sequences (initial + follow-ups)
- Handles inbox warm-up and domain rotation
- Sends emails and tracks replies
- Triggers webhooks on reply events

**Webhook Configuration**:
- Point Smartlead webhook to: `http://your-domain.com/webhook/smartlead`
- Or use local tunnel (ngrok) for development: `ngrok http 8001`

### 3. OpenAI API (for SalesGPT)
**Purpose**: AI-powered reply generation  
**Required**: `OPENAI_API_KEY`  
**Setup**:
- Get API key from [OpenAI Platform](https://platform.openai.com/)
- Add to `.env.local`: `OPENAI_API_KEY=sk-xxx`

**What it does**:
- Generates contextual email replies
- Classifies intent (interested/objection/curious/neutral)
- Maintains conversation context
- Uses SalesGPT framework for stage-aware responses

### 4. HubSpot API
**Purpose**: CRM pipeline management  
**Required**: `HUBSPOT_API_KEY`  
**Setup**:
- Create HubSpot account
- Generate API key from Settings → Integrations → Private Apps
- Add to `.env.local`: `HUBSPOT_API_KEY=your_key_here`

**What it does**:
- Creates contacts for new leads
- Updates pipeline stages: idle → engaged → booked → closed
- Tracks deal progression
- Associates contacts with deals

### 5. GEMflush API
**Purpose**: Competitive visibility insights  
**Required**: `GEMFLUSH_API_KEY`, `GEMFLUSH_API_URL`  
**Setup**:
- Sign up for GEMflush API access
- Get API key and base URL
- Add to `.env.local`:
  ```
  GEMFLUSH_API_KEY=your_key_here
  GEMFLUSH_API_URL=https://api.gemflush.com/v1
  ```

**What it does**:
- Provides clinic visibility audit scores
- Compares clinics against competitors
- Generates evidence for email replies
- Shows visibility gaps and opportunities

### 6. Cal.com
**Purpose**: Meeting scheduling  
**Required**: `CAL_BOOKING_LINK`  
**Setup**:
- Create Cal.com account
- Set up your booking link
- Add to `.env.local`: `CAL_BOOKING_LINK=https://cal.com/your-link`

**What it does**:
- Generates personalized booking links
- Sends links to interested leads
- Pre-fills lead information (optional)

## Configuration Files

### Environment Variables (`.env.local`)

Copy `.env.example` to `.env.local` and fill in all required keys:

```bash
# Apollo
APOLLO_API_KEY=your_apollo_api_key_here

# Smartlead
SMARTLEAD_API_KEY=your_smartlead_api_key_here
SMARTLEAD_FROM_EMAIL=noreply@yourdomain.com
SMARTLEAD_FROM_NAME=ASSCH Team
SMARTLEAD_REPLY_TO=noreply@yourdomain.com
SMARTLEAD_CAMPAIGN_NAME=ASSCH Outreach
SMARTLEAD_INITIAL_SUBJECT=Quick question about your clinic's visibility
SMARTLEAD_INITIAL_BODY=Hi {{first_name}},\n\nI noticed {{clinic_name}}...
SMARTLEAD_FOLLOWUP_SUBJECT=Following up on visibility
SMARTLEAD_FOLLOWUP_BODY=Hi {{first_name}},\n\nJust wanted to follow up...

# SalesGPT
SALESGPT_CONFIG_PATH=examples/example_agent_setup.json
GPT_MODEL=gpt-3.5-turbo-0613

# Cal.com
CAL_BOOKING_LINK=https://cal.com/your-booking-link

# HubSpot
HUBSPOT_API_KEY=your_hubspot_api_key_here

# GEMflush
GEMFLUSH_API_KEY=your_gemflush_api_key_here
GEMFLUSH_API_URL=https://api.gemflush.com/v1
DEFAULT_COMPETITOR=local competitors

# Defaults
DEFAULT_GEOGRAPHY=New York, NY
DEFAULT_SPECIALTY=Dermatology

# Webhook
WEBHOOK_PORT=8001

# OpenAI
OPENAI_API_KEY=your_openai_api_key_here
```

## Running the System

### 1. Install Dependencies

```bash
pip install -r requirements-assch.txt
```

### 2. Run Daily Pipeline

```bash
python main_agent.py --geography "New York, NY" --specialty "Dermatology" --limit 20
```

This will:
- Find 20 leads in NYC specializing in Dermatology
- Score and rank them
- Create Smartlead campaign
- Add leads to campaign
- Create HubSpot contacts

### 3. Start Webhook Server

```bash
python webhook_handler.py
```

This starts a FastAPI server on port 8001 that:
- Listens for Smartlead webhook events
- Processes email replies
- Generates AI responses
- Updates CRM stages

**For Production**: Deploy webhook server to a public URL (Railway, Vercel, etc.) and configure Smartlead webhook endpoint.

## State Management

The system uses local JSON files for state persistence:

- `state/conversation_states.json` - Email thread conversations
- `state/lead_states.json` - Lead metadata and status

**For Production**: Replace with Redis or PostgreSQL for scalability.

## Testing Integrations

### Test Apollo
```python
from services.apollo import ApolloAgent
apollo = ApolloAgent()
leads = apollo.search_leads("New York, NY", "Dermatology", limit=5)
print(f"Found {len(leads)} leads")
```

### Test Smartlead
```python
from services.outbound import SmartleadAgent
smartlead = SmartleadAgent()
mailboxes = smartlead.get_mailboxes()
print(f"Available mailboxes: {len(mailboxes)}")
```

### Test HubSpot
```python
from services.crm import HubSpotAgent
crm = HubSpotAgent()
contact = crm.get_contact_by_email("test@example.com")
print(f"Contact: {contact}")
```

### Test GEMflush
```python
from services.visibility import GEMflushAgent
gemflush = GEMflushAgent()
audit = gemflush.get_audit("example-clinic.com")
print(f"Visibility score: {audit.get('visibility_score')}")
```

## Cost Considerations

- **Apollo**: Pay-per-credit pricing (varies by plan)
- **Smartlead**: Subscription-based (varies by volume)
- **OpenAI**: Pay-per-token usage (GPT-3.5-turbo is cost-effective)
- **HubSpot**: Free tier available, paid plans for advanced features
- **GEMflush**: Contact for pricing
- **Cal.com**: Free tier available

## Security Notes

- Never commit `.env.local` to git (already in `.gitignore`)
- Use environment variables for all API keys
- Validate webhook signatures in production
- Rate limit API calls to avoid hitting limits
- Monitor API usage and costs

## Troubleshooting

### Common Issues

1. **"API key not found"**
   - Check `.env.local` file exists and has correct variable names
   - Ensure you're loading from `.env.local` (not `.env`)

2. **Webhook not receiving events**
   - Verify webhook URL is publicly accessible
   - Check Smartlead webhook configuration
   - Test with ngrok for local development

3. **Rate limit errors**
   - Implement retry logic with exponential backoff
   - Reduce batch sizes
   - Check API plan limits

4. **State file errors**
   - Ensure `state/` directory exists
   - Check file permissions
   - Verify JSON format is valid

## Next Steps

1. Set up all API accounts and get keys
2. Configure `.env.local` with all credentials
3. Test each integration individually
4. Run a small test pipeline (5-10 leads)
5. Monitor webhook events and replies
6. Scale up once verified working

## Support

For issues or questions:
- Check service-specific API documentation
- Review error logs in console output
- Test integrations individually
- Verify environment variables are set correctly
