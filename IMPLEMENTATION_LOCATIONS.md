# 📍 Real Implementation Locations

## Main Email Pipeline Implementations

### 1. **Background Queue Builder** (Manual Review Flow)
**File**: `workflows/background_queue_builder.py`

This is the implementation that:
- Sources leads from Apollo
- Prioritizes them by ELM score
- Generates personalized emails with AI
- Creates HubSpot contacts
- Stores leads in database for manual review

**Key Methods**:
- `async def run()` - Main loop that continuously sources leads
- `async def _process_lead()` - Processes individual lead (lines 166-360)
- `def _compute_elaboration_score()` - ELM scoring (lines 362-399)

**Email Generation** (line 241):
```python
email = self.ab_manager.generate_email_from_variant(
    variant=variant,
    salesgpt_wrapper=self.salesgpt,
    lead=lead_dict,
    evidence=evidence,
    competitor=competitor_dict
)
```

---

### 2. **ASSCH Orchestrator** (Automated Sending Flow)
**File**: `main_agent.py`

This orchestrates the full automated pipeline:
- Sources leads from Apollo (line 114)
- Scores leads (line 142)
- Creates Smartlead campaign (line 147)
- Adds leads to Smartlead for automated sending (line 173)
- Creates HubSpot contacts (line 278)

**Key Method**: `async def run_daily_pipeline()` (lines 86-350)

This flow **actually sends emails** via Smartlead API.

---

### 3. **Email Generation with AI**
**File**: `services/analytics/ab_test_manager.py`

Contains `ABTestManager.generate_email_from_variant()` which:
- Takes lead data, evidence, competitor info
- Calls SalesGPT wrapper to generate personalized email
- Returns subject and body

---

### 4. **SalesGPT Wrapper** (AI Email Generation)
**File**: `services/salesgpt/salesgpt_wrapper.py`

This wraps the SalesGPT AI agent to:
- Generate personalized email content
- Use lead data, evidence, competitor info
- Apply persuasion routes (central/peripheral)

---

### 5. **Manual Review & Sending**
**File**: `workflows/manual_review_workflow.py`

Contains functions for:
- `load_pending_leads()` - Load leads from database
- `approve_and_send()` - Send approved emails via Smartlead
- `update_email_content()` - Edit email before sending

---

## Flow Comparison

### Manual Review Flow (Dashboard):
```
Apollo → BackgroundQueueBuilder → Database (pending_review) 
→ Dashboard Review → approve_and_send() → Smartlead
```

**Entry Point**: `scripts/start_queue_builder.py`

---

### Automated Flow (Direct Sending):
```
Apollo → ASSCHOrchestrator → Smartlead (direct send) → HubSpot
```

**Entry Point**: `main_agent.py` - `ASSCHOrchestrator.run_daily_pipeline()`

---

## Key Service Implementations

### Apollo Lead Sourcing
**File**: `services/apollo/apollo_agent.py`
- `search_leads()` - Search by geography, specialty
- `score_leads()` - Score by relevance

### Smartlead Email Sending
**File**: `services/outbound/smartlead_agent.py`
- `create_campaign()` - Create email campaign
- `add_leads_to_campaign()` - Queue leads for sending

### HubSpot CRM
**File**: `services/crm/hubspot_agent.py`
- `create_contact()` - Create contact in HubSpot
- `create_deal()` - Create deal for contact

---

## Quick Start Commands

### Run Manual Review Flow:
```bash
python3 scripts/start_queue_builder.py
```
Then review in dashboard: http://localhost:8501

### Run Automated Flow:
```python
from main_agent import ASSCHOrchestrator
from salesgpt.container import ServiceContainer

container = ServiceContainer()
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
```
