# A.S.S.C.H. Assembly — Sales Automation System

**A**pollo → **S**martlead → **S**alesGPT → **C**al.com → **H**ubSpot

A modular, Cursor-agent-friendly sales automation pipeline designed for clinic lead generation and conversion.

---

## 🏗️ Architecture Overview

```
/services/apollo/        → Lead sourcing + enrichment
/services/outbound/      → Smartlead API wrapper (send + sequences)
/services/salesgpt/      → Reply agent model + context memory
/services/scheduler/     → Cal.com booking link routing
/services/crm/           → HubSpot pipeline stage updates
/services/visibility/    → GEMflush audit score API wrapper
/state/                  → conversation + lead_states.json
/ui/                     → Optional dashboard (future)
main_agent.py            → Central orchestrator (runs daily)
webhook_handler.py       → Smartlead reply event processor
```

**Critical Design**: Each service is atomic so Cursor agents can edit one without breaking others.

---

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.8-3.11
- API keys for:
  - Apollo
  - Smartlead (with inbox warm-up started)
  - Cal.com booking link
  - HubSpot (free CRM account)
  - GEMflush audit endpoint
  - OpenAI (or OpenRouter) for SalesGPT

### 2. Installation

```bash
# Clone repository (or navigate to workspace)
cd /workspace

# Install dependencies
pip install -r requirements-assch.txt

# Copy environment template
cp .env.example .env.local

# Edit .env.local with your API keys
nano .env.local  # or use your preferred editor
```

### 3. Configuration

Edit `.env.local` with your credentials:

```bash
# Required API Keys
APOLLO_API_KEY=your_key_here
SMARTLEAD_API_KEY=your_key_here
HUBSPOT_API_KEY=your_key_here
GEMFLUSH_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
# Optional: Use OpenRouter instead of OpenAI
OPENROUTER_API_KEY=your_openrouter_key
GPT_MODEL=openrouter/openai/gpt-4o

# Cal.com Booking Link
CAL_BOOKING_LINK=https://cal.com/your-link

# Smartlead Configuration
SMARTLEAD_FROM_EMAIL=noreply@yourdomain.com
SMARTLEAD_FROM_NAME=Your Name
SMARTLEAD_REPLY_TO=noreply@yourdomain.com
```

### 4. Run Daily Pipeline

```bash
# Run with defaults
python main_agent.py

# Custom parameters
python main_agent.py \
  --geography "Los Angeles, CA" \
  --specialty "Cardiology" \
  --limit 30
```

### 5. Start Webhook Server

```bash
# In a separate terminal
python webhook_handler.py

# Server runs on http://localhost:8001
# Configure Smartlead webhook to POST to:
# http://your-domain.com/webhook/smartlead
```

---

## 📋 Pipeline Flow

### Daily Execution (`main_agent.py`)

1. **Apollo Lead Sourcing**
   - Search for 20-50 leads by geography + specialty
   - Score leads by website presence, title relevance, employee count
   - Returns enriched lead data

2. **Smartlead Campaign Setup**
   - Create campaign with domain rotation
   - Add initial email sequence
   - Add follow-up sequence (3-day delay)
   - Queue leads for sending

3. **HubSpot Contact Creation**
   - Create contacts for top leads
   - Initialize pipeline stage: "idle"

4. **State Management**
   - Store lead metadata in `state/lead_states.json`
   - Track campaign associations

### Reply Handling (`webhook_handler.py`)

When Smartlead receives a reply:

1. **Webhook Trigger**
   - POST to `/webhook/smartlead`
   - Extract thread_id, sender_email, email_body

2. **SalesGPT Processing**
   - Load conversation history from state
   - Classify intent: `interested`, `objection`, `curious`, `neutral`, `not_interested`
   - Generate contextual reply

3. **Intent-Based Actions**

   **If "interested":**
   - Generate Cal.com booking link
   - Send confirmation message
   - Update HubSpot → "booked"
   - Update lead state → "booked"

   **If "curious" or "neutral":**
   - Query GEMflush for visibility audit
   - Inject evidence: "17% less visible than {{competitor}}..."
   - Update HubSpot → "engaged"
   - Update lead state → "engaged"

   **If "objection":**
   - Query GEMflush for full audit
   - Format evidence with competitor comparison
   - Update HubSpot → "engaged"
   - Update lead state → "engaged"

4. **Reply Delivery**
   - Send reply via Smartlead API
   - Store conversation in `state/conversation_states.json`

---

## 🔧 Service Details

### Apollo Agent (`services/apollo/`)

**Purpose**: Lead sourcing and enrichment

**Key Methods**:
- `search_leads()` - Search by geography, specialty, filters
- `score_leads()` - Score by relevance
- `enrich_lead()` - Add additional metadata

**Output**: List of `Lead` objects with email, name, website, clinic metadata

---

### Smartlead Agent (`services/outbound/`)

**Purpose**: Email delivery and sequence management

**Key Methods**:
- `create_campaign()` - Create new email campaign
- `add_sequence()` - Add email to sequence
- `add_leads_to_campaign()` - Queue leads for sending
- `send_reply()` - Send reply to thread
- `get_mailboxes()` - List available mailboxes
- `check_warmup_status()` - Check inbox warm-up

**Features**:
- Domain rotation via multiple mailboxes
- Template field support (`{{first_name}}`, `{{clinic_name}}`)
- Automatic follow-up sequences

---

### SalesGPT Wrapper (`services/salesgpt/`)

**Purpose**: Context-aware reply generation

**Key Methods**:
- `classify_intent()` - Classify email intent
- `generate_reply()` - Generate contextual reply
- `should_send_booking_link()` - Determine if booking link needed

**Integration**: Uses existing SalesGPT from `/salesgpt/` directory

**Critical**: Only operates when conversation context exists (no hallucinated cold outreach)

---

### Cal Scheduler (`services/scheduler/`)

**Purpose**: Booking link generation

**Key Methods**:
- `get_booking_link()` - Get booking link for lead
- `generate_confirmation_message()` - Format confirmation with link

**Configuration**: Set `CAL_BOOKING_LINK` in `.env.local`

---

### HubSpot Agent (`services/crm/`)

**Purpose**: CRM pipeline management

**Pipeline Stages**:
- `idle` → Initial lead
- `engaged` → Responded, in conversation
- `booked` → Booking link sent/accepted
- `closed` → Deal closed

**Key Methods**:
- `create_contact()` - Create new contact
- `update_pipeline_stage()` - Update deal stage
- `create_deal()` - Create deal for contact
- `get_contact_by_email()` - Lookup contact

---

### GEMflush Agent (`services/visibility/`)

**Purpose**: Visibility audit and competitor comparison

**Key Methods**:
- `get_audit()` - Get clinic audit score
- `get_competitor_comparison()` - Compare with competitor
- `format_evidence_message()` - Format evidence for email

**Evidence Format**:
```
"17% less visible than {{competitor_name}} in GPT-based patient searches.
I can show you the full audit on a short call."
```

---

## 📊 State Management

### Files

- `state/conversation_states.json` - Thread ID → conversation history
- `state/lead_states.json` - Email → lead metadata + status

### Structure

**conversation_states.json**:
```json
{
  "thread_123": [
    "USER: Hi, I'm interested in learning more.",
    "AGENT: Great! I'd love to show you..."
  ]
}
```

**lead_states.json**:
```json
{
  "lead@example.com": {
    "status": "engaged",
    "clinic_name": "Example Clinic",
    "website": "https://example.com",
    "campaign_id": 123,
    "hubspot_contact_id": "456"
  }
}
```

---

## 🎯 Cursor Agent Rules

The system follows `.cursor/rules.json`:

- **Atomic Services**: Each service can be edited independently
- **DRY & SOLID**: No code duplication, single responsibility
- **Type Hints**: All functions have type annotations
- **Error Handling**: Specific exception types, graceful failures
- **Environment Variables**: All configuration via `.env.local`
- **State Management**: File-based JSON for simplicity

---

## 🚢 Deployment

### Local Development

```bash
# Run pipeline manually
python main_agent.py

# Start webhook server
python webhook_handler.py
```

### Production (Railway/Vercel)

1. **Set Environment Variables**
   - Add all `.env.local` variables to platform

2. **Deploy Webhook Handler**
   ```bash
   # Railway example
   railway up
   ```

3. **Configure Cron Job**
   ```bash
   # Daily at 9 AM
   0 9 * * * cd /app && python main_agent.py
   ```

4. **Configure Smartlead Webhook**
   - URL: `https://your-domain.com/webhook/smartlead`
   - Event: `email_replied`

### Optional: Supabase Storage

For scaling async reply backlogs:

```python
# Replace StateManager with Supabase backend
# See: services/state/supabase_manager.py (future)
```

---

## 📈 Monitoring & Debugging

### Check Lead States

```python
from state import StateManager

state = StateManager()
leads = state.get_all_leads_by_status("engaged")
print(f"Engaged leads: {len(leads)}")
```

### View Conversation History

```python
from state import StateManager

state = StateManager()
history = state.get_conversation_history("thread_123")
for message in history:
    print(message)
```

### Test Individual Services

```python
# Test Apollo
from services.apollo import ApolloAgent
apollo = ApolloAgent()
leads = apollo.search_leads("New York, NY", "Dermatology", limit=5)
print(f"Found {len(leads)} leads")

# Test SalesGPT
from services.salesgpt import SalesGPTWrapper
salesgpt = SalesGPTWrapper()
reply = salesgpt.generate_reply(
    email_body="I'm interested in learning more.",
    sender_name="John Doe",
    sender_email="john@example.com",
    conversation_history=[]
)
print(reply)
```

---

## 🔒 Security Best Practices

1. **Never commit `.env.local`** - Already in `.gitignore`
2. **Rotate API keys regularly**
3. **Use environment-specific keys** (dev/staging/prod)
4. **Monitor webhook endpoints** for unauthorized access
5. **Rate limit webhook endpoints** in production

---

## 🐛 Troubleshooting

### "API key not found" errors

- Check `.env.local` exists and has correct keys
- Verify key names match exactly (case-sensitive)
- Ensure `.env.local` is in workspace root

### Smartlead campaign creation fails

- Verify inbox warm-up is started
- Check mailbox IDs are valid
- Ensure `SMARTLEAD_FROM_EMAIL` domain is verified

### SalesGPT not generating replies

- Check `OPENAI_API_KEY` is set
- Verify `SALESGPT_CONFIG_PATH` points to valid config
- Check conversation history exists in state

### Webhook not receiving events

- Verify webhook URL is publicly accessible
- Check Smartlead webhook configuration
- Review webhook logs: `python webhook_handler.py`

---

## 📝 Example Usage

### Run Daily Pipeline

```bash
python main_agent.py \
  --geography "San Francisco, CA" \
  --specialty "Orthopedics" \
  --limit 25
```

### Manual Reply Processing

```python
from main_agent import ASSCHOrchestrator
import asyncio

orchestrator = ASSCHOrchestrator()

asyncio.run(orchestrator.handle_reply(
    thread_id="thread_abc123",
    sender_email="lead@clinic.com",
    sender_name="Dr. Smith",
    email_body="I'd like to learn more about your services."
))
```

---

## 🗺️ Roadmap

- [ ] Add UI dashboard for queued conversations
- [ ] Implement Redis for scalable session storage
- [ ] Add database persistence (PostgreSQL)
- [ ] Create more email sequence templates
- [ ] Add A/B testing for email templates
- [ ] Implement lead scoring ML model
- [ ] Add analytics dashboard
- [ ] Support multiple Cal.com event types
- [ ] Add Slack notifications for booked calls

---

## 📞 Support

For issues or questions:
1. Check `.cursor/rules.json` for coding standards
2. Review service docstrings for API details
3. Test individual services in isolation
4. Check state files for data issues

---

## 📄 License

Same as parent SalesGPT repository (Apache-2.0).

---

**Built for Cursor Agents** 🤖  
**Designed for Atomic Service Editing** 🧱  
**Optimized for Clinic Lead Conversion** 🏥
