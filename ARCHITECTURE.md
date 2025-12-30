# A.S.S.C.H. Assembly Architecture

## System Overview

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

## Directory Structure

```
/workspace/
├── services/
│   ├── apollo/              # Lead sourcing
│   │   ├── __init__.py
│   │   └── apollo_agent.py
│   ├── outbound/            # Email delivery
│   │   ├── __init__.py
│   │   └── smartlead_agent.py
│   ├── salesgpt/            # Reply agent
│   │   ├── __init__.py
│   │   └── salesgpt_wrapper.py
│   ├── scheduler/           # Booking links
│   │   ├── __init__.py
│   │   └── cal_scheduler.py
│   ├── crm/                 # CRM management
│   │   ├── __init__.py
│   │   └── hubspot_agent.py
│   └── visibility/          # Audit scores
│       ├── __init__.py
│       └── gemflush_agent.py
├── state/                   # State persistence
│   ├── __init__.py
│   ├── state_manager.py
│   ├── conversation_states.json  # Generated
│   └── lead_states.json          # Generated
├── ui/                      # Future dashboard
│   └── README.md
├── main_agent.py            # Main orchestrator
├── webhook_handler.py       # Smartlead webhook
├── .env.local               # Configuration (gitignored)
├── .env.example             # Template
├── .cursor/
│   └── rules.json          # Cursor agent rules
└── requirements-assch.txt  # Dependencies
```

## Service Contracts

### Apollo Agent
**Input**: Geography, specialty, filters  
**Output**: List of scored `Lead` objects  
**Atomic**: ✅ Can edit independently

### Smartlead Agent
**Input**: Campaign config, leads, sequences  
**Output**: Campaign ID, delivery status  
**Atomic**: ✅ Can edit independently

### SalesGPT Wrapper
**Input**: Email body, conversation history  
**Output**: Reply + intent classification  
**Atomic**: ✅ Can edit independently

### Cal Scheduler
**Input**: Lead name/email (optional)  
**Output**: Booking link URL  
**Atomic**: ✅ Can edit independently

### HubSpot Agent
**Input**: Contact data, pipeline stage  
**Output**: Contact/Deal ID  
**Atomic**: ✅ Can edit independently

### GEMflush Agent
**Input**: Clinic ID, competitor names  
**Output**: Audit scores, comparisons  
**Atomic**: ✅ Can edit independently

## Data Flow

### Daily Pipeline
1. `main_agent.py` → `ApolloAgent.search_leads()`
2. `ApolloAgent.score_leads()` → Scored leads
3. `SmartleadAgent.create_campaign()` → Campaign ID
4. `SmartleadAgent.add_leads_to_campaign()` → Queued emails
5. `HubSpotAgent.create_contact()` → Contact IDs
6. `StateManager.update_lead_state()` → Persisted state

### Reply Handling
1. Smartlead webhook → `webhook_handler.py`
2. `ASSCHOrchestrator.handle_reply()` → Intent classification
3. `SalesGPTWrapper.generate_reply()` → Contextual reply
4. Intent-based action:
   - Interested → `CalScheduler.get_booking_link()`
   - Curious/Neutral → `GEMflushAgent.get_competitor_comparison()`
   - Objection → `GEMflushAgent.format_evidence_message()`
5. `SmartleadAgent.send_reply()` → Reply delivered
6. `HubSpotAgent.update_pipeline_stage()` → CRM updated
7. `StateManager.add_conversation_message()` → History saved

## State Management

### Conversation States
```json
{
  "thread_abc123": [
    "USER: I'm interested in learning more.",
    "AGENT: Great! Here's a booking link..."
  ]
}
```

### Lead States
```json
{
  "lead@clinic.com": {
    "status": "engaged",
    "clinic_name": "Example Clinic",
    "website": "https://example.com",
    "campaign_id": 123,
    "hubspot_contact_id": "456",
    "specialty": "Dermatology"
  }
}
```

## Error Handling

Each service handles errors independently:
- API failures → Logged, graceful degradation
- Missing data → Default values or skip
- State corruption → Reinitialize files

## Extension Points

### Add New Service
1. Create `services/new_service/`
2. Implement agent class
3. Add to orchestrator
4. Update `.cursor/rules.json` if needed

### Add New Intent Handler
1. Extend `SalesGPTWrapper.classify_intent()`
2. Add handler in `ASSCHOrchestrator.handle_reply()`
3. Update state management

### Add New CRM Stage
1. Add to `HubSpotAgent.PIPELINE_STAGES`
2. Update `ASSCHOrchestrator.handle_reply()`
3. Add state transitions

## Performance Considerations

- **State Files**: JSON-based, suitable for <10K leads
- **API Rate Limits**: Services handle rate limiting internally
- **Async Operations**: Webhook handler uses async/await
- **Scaling**: Replace StateManager with Redis/DB for production

## Security

- API keys in `.env.local` (gitignored)
- Webhook validation (add signature verification)
- Input sanitization in SalesGPT wrapper
- Error messages don't leak sensitive data

## Testing Strategy

Each service can be tested independently:

```python
# Test Apollo
from services.apollo import ApolloAgent
apollo = ApolloAgent()
leads = apollo.search_leads("NYC", "Cardiology", limit=5)
assert len(leads) > 0

# Test State Manager
from state import StateManager
state = StateManager()
state.set_lead_status("test@example.com", "idle")
assert state.get_lead_state("test@example.com")["status"] == "idle"
```

## Deployment Architecture

### Local Development
- Single process: `python main_agent.py`
- Webhook server: `python webhook_handler.py`
- State files: Local JSON

### Production (Railway/Vercel)
- Cron job: Daily pipeline execution
- Webhook endpoint: Public URL
- State storage: Upgrade to Redis/PostgreSQL

## Monitoring

### Key Metrics
- Leads sourced per day
- Email delivery rate
- Reply rate
- Intent distribution
- Conversion rate (idle → booked)

### Logging
- Service-level logging
- Error tracking
- State file monitoring

## Future Enhancements

- [ ] Redis for state management
- [ ] Database persistence
- [ ] UI dashboard
- [ ] Analytics pipeline
- [ ] A/B testing framework
- [ ] Multi-language support
