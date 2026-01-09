# SalesGPT Refactored Architecture Guide

## Overview

This document explains how the refactored SalesGPT system operates. The refactoring introduced:
- **SQLite database** for state persistence (replacing JSON files)
- **Dependency injection** for better testability and modularity
- **Centralized configuration** using Pydantic Settings
- **Webhook security** with signature verification and rate limiting

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Configuration Layer                        │
│  Pydantic Settings (salesgpt/config/settings.py)        │
│  - Loads from .env file                                 │
│  - Validates all configuration                          │
└──────────────────┬──────────────────────────────────────┘
                    │
┌──────────────────▼──────────────────────────────────────┐
│         Dependency Injection Container                   │
│  ServiceContainer (salesgpt/container.py)               │
│  - Initializes all services with injected dependencies  │
│  - Manages database connections                         │
│  - Provides configured orchestrator                     │
└──────────────────┬──────────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
┌───────▼──────┐ ┌─▼──────┐ ┌─▼──────────┐
│   Database   │ │ Services│ │ Orchestrator│
│   Manager    │ │ (Apollo,│ │ (main_agent│
│              │ │ Smartlead│ │ .py)       │
│ SQLite DB    │ │ etc.)   │ │            │
└──────────────┘ └─────────┘ └────────────┘
```

## Key Components

### 1. Configuration Management

**Location:** `salesgpt/config/settings.py`

All configuration is centralized using Pydantic Settings. Configuration is loaded from:
1. Environment variables
2. `.env` file
3. Default values (for optional settings)

**Usage:**
```python
from salesgpt.config import get_settings

settings = get_settings()
print(settings.database_url)
print(settings.apollo_api_key)
```

**Required Environment Variables:**
- `OPENAI_API_KEY` - OpenAI API key
- `APOLLO_API_KEY` - Apollo API key
- `SMARTLEAD_API_KEY` - Smartlead API key
- `HUBSPOT_ACCESS_TOKEN` - HubSpot Private App token
- `SMARTLEAD_FROM_EMAIL` - Email address for Smartlead campaigns
- `WEBHOOK_SECRET_KEY` - Secret key for webhook signature verification

**Optional Environment Variables:**
- `DATABASE_URL` - Database connection string (default: `sqlite:///./salesgpt.db`)
- `CAL_BOOKING_LINK` - Cal.com booking link
- `GEMFLUSH_API_KEY` - GEMflush API key
- `WEBHOOK_PORT` - Webhook server port (default: 8001)

### 2. Database Layer

**Location:** `salesgpt/models/database.py`, `salesgpt/db/connection.py`

The system uses SQLite (by default) for state persistence. The database contains:

- **Leads Table** - Stores lead information and metadata
- **Conversations Table** - Stores conversation threads
- **ConversationMessages Table** - Stores individual messages
- **Campaigns Table** - Tracks email campaigns

**Database Manager:**
```python
from salesgpt.config import get_settings
from salesgpt.db.connection import DatabaseManager

settings = get_settings()
db_manager = DatabaseManager(settings.database_url)
db_manager.create_tables()  # Create tables if they don't exist

# Use context manager for sessions
with db_manager.session() as session:
    # Use session here
    pass
```

### 3. State Management

**Location:** `state/state_manager.py`

StateManager replaces the old JSON file-based storage with database operations.

**Key Methods:**
- `get_lead_state(email)` - Get lead information by email
- `set_lead_status(email, status, metadata)` - Set lead status and metadata
- `update_lead_state(email, state)` - Update lead state (merges with existing)
- `get_conversation_history(thread_id)` - Get conversation messages
- `add_conversation_message(thread_id, message, sender)` - Add message to conversation
- `get_all_leads_by_status(status)` - Get all leads with specific status

**Usage:**
```python
from salesgpt.config import get_settings
from salesgpt.db.connection import DatabaseManager
from state.state_manager import StateManager

settings = get_settings()
db_manager = DatabaseManager(settings.database_url)
db_manager.create_tables()

state_manager = StateManager(db_manager)

# Set lead status
state_manager.set_lead_status(
    "lead@example.com",
    "engaged",
    {"apollo_person_id": "12345", "score": 85}
)

# Get lead state
lead = state_manager.get_lead_state("lead@example.com")

# Add conversation message
state_manager.add_conversation_message(
    "thread_123",
    "Hello, I'm interested!",
    "user"
)
```

### 4. Dependency Injection Container

**Location:** `salesgpt/container.py`

The ServiceContainer manages all service initialization and dependency wiring.

**How it works:**
1. Loads settings from configuration
2. Initializes database manager
3. Creates StateManager with database
4. Initializes all services (Apollo, Smartlead, SalesGPT, etc.)
5. Provides configured orchestrator

**Usage:**
```python
from salesgpt.config import get_settings
from salesgpt.container import ServiceContainer

# Load settings
settings = get_settings()

# Create container (initializes all services)
container = ServiceContainer(settings)

# Get orchestrator with all dependencies injected
orchestrator = container.orchestrator

# Use orchestrator
await orchestrator.run_daily_pipeline(
    geography="New York, NY",
    specialty="Dermatology",
    lead_limit=50
)
```

**Accessing Individual Services:**
```python
# Get individual services if needed
apollo = container.apollo
smartlead = container.smartlead
state_manager = container.state_manager
```

### 5. Main Orchestrator

**Location:** `main_agent.py`

The ASSCHOrchestrator coordinates the entire sales pipeline. It now uses dependency injection instead of initializing services internally.

**Key Methods:**
- `run_daily_pipeline(geography, specialty, lead_limit)` - Run daily lead sourcing and outreach
- `handle_reply(thread_id, sender_email, sender_name, email_body)` - Handle email replies
- `run_gemflush_campaign_with_competitors(...)` - Run GEMflush campaign

**Pipeline Flow:**
```
1. Apollo → Search and score leads
2. Smartlead → Create campaign and add leads
3. HubSpot → Create contacts
4. StateManager → Persist lead data
5. Webhook → Handle replies → SalesGPT → Update pipeline
```

### 6. Webhook Handler

**Location:** `webhook_handler.py`

The webhook handler processes Smartlead reply events with security features:

- **Signature Verification** - Validates HMAC signatures
- **Rate Limiting** - Limits requests to 100/minute
- **Request Validation** - Validates payload structure

**Security:**
```python
# Webhook signature is verified automatically
# Smartlead must send X-Smartlead-Signature header
# Signature is HMAC-SHA256 of request body using WEBHOOK_SECRET_KEY
```

**Usage:**
```bash
# Start webhook server
python webhook_handler.py

# Or with uvicorn
uvicorn webhook_handler:app --host 0.0.0.0 --port 8001
```

## Setup and Installation

### 1. Install Dependencies

```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

New dependencies added:
- `sqlalchemy>=2.0.0` - Database ORM
- `alembic>=1.13.0` - Database migrations
- `pydantic-settings>=2.0.0` - Configuration management
- `slowapi>=0.1.9` - Rate limiting

### 2. Configure Environment

Create or update `.env` file:

```bash
# Database
DATABASE_URL=sqlite:///./salesgpt.db

# API Keys (Required)
OPENAI_API_KEY=sk-...
APOLLO_API_KEY=apollo_...
SMARTLEAD_API_KEY=smartlead_...
HUBSPOT_ACCESS_TOKEN=pat-na1-...

# Smartlead Configuration
SMARTLEAD_FROM_EMAIL=your-email@example.com
SMARTLEAD_FROM_NAME=Your Name
SMARTLEAD_CAMPAIGN_NAME=ASSCH Outreach

# Webhook Security
WEBHOOK_SECRET_KEY=your_secret_key_here

# Optional
CAL_BOOKING_LINK=https://cal.com/your-link
GEMFLUSH_API_KEY=gemflush_...
WEBHOOK_PORT=8001
```

### 3. Initialize Database

```bash
# Create database and tables
python -c "
from salesgpt.config import get_settings
from salesgpt.db.connection import DatabaseManager

settings = get_settings()
db = DatabaseManager(settings.database_url)
db.create_tables()
print('Database initialized!')
"
```

### 4. Migrate Existing Data (if applicable)

If you have existing JSON state files:

```bash
python scripts/migrate_json_to_sqlite.py
```

This will:
- Create database tables
- Import leads from `state/lead_states.json`
- Import conversations from `state/conversation_states.json`

## Usage Examples

### Running Daily Pipeline

```python
import asyncio
from salesgpt.config import get_settings
from salesgpt.container import ServiceContainer

async def main():
    # Load settings and create container
    settings = get_settings()
    container = ServiceContainer(settings)
    
    # Get orchestrator
    orchestrator = container.orchestrator
    
    # Run pipeline
    await orchestrator.run_daily_pipeline(
        geography="New York, NY",
        specialty="Dermatology",
        lead_limit=50
    )

if __name__ == "__main__":
    asyncio.run(main())
```

Or via command line:
```bash
python main_agent.py --campaign daily --geography "New York, NY" --specialty "Dermatology" --limit 50
```

### Handling Webhooks

The webhook handler automatically:
1. Verifies signature (if `WEBHOOK_SECRET_KEY` is set)
2. Validates payload structure
3. Routes to orchestrator for processing
4. Updates database state

**Smartlead Webhook Configuration:**
- URL: `https://your-domain.com/webhook/smartlead`
- Method: POST
- Headers: Include `X-Smartlead-Signature` with HMAC-SHA256 signature

### Accessing State Directly

```python
from salesgpt.config import get_settings
from salesgpt.db.connection import DatabaseManager
from state.state_manager import StateManager

settings = get_settings()
db = DatabaseManager(settings.database_url)
state = StateManager(db)

# Get all engaged leads
engaged_leads = state.get_all_leads_by_status("engaged")
for lead in engaged_leads:
    print(f"{lead['email']}: {lead['status']}")

# Get conversation history
history = state.get_conversation_history("thread_123")
for message in history:
    print(message)
```

## Testing

### Running Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest

# Run specific test file
pytest tests/test_database_migration.py -v

# Run with coverage
pytest --cov=salesgpt --cov=state tests/
```

### Test Fixtures

Test fixtures are available in `tests/fixtures/`:
- `services.py` - Mock service fixtures
- `database.py` - In-memory database fixtures

**Example test:**
```python
import pytest
from tests.fixtures.database import test_state_manager

def test_lead_operations(test_state_manager):
    test_state_manager.set_lead_status("test@example.com", "idle")
    lead = test_state_manager.get_lead_state("test@example.com")
    assert lead["status"] == "idle"
```

## Database Migrations

### Using Alembic

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Manual Migration

For one-time JSON to SQLite migration:
```bash
python scripts/migrate_json_to_sqlite.py
```

## Troubleshooting

### Database Connection Issues

**Problem:** `sqlite3.OperationalError: unable to open database file`

**Solution:**
- Check file permissions on database directory
- Ensure `DATABASE_URL` path is correct
- Verify SQLite is installed: `sqlite3 --version`

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'pydantic_settings'`

**Solution:**
```bash
pip install -r requirements.txt
```

### Configuration Validation Errors

**Problem:** `pydantic.ValidationError: Field required`

**Solution:**
- Check `.env` file has all required variables
- Verify variable names match exactly (case-sensitive)
- See `MIGRATION_GUIDE.md` for required variables

### Webhook Signature Verification Fails

**Problem:** `401 Invalid webhook signature`

**Solution:**
- Verify `WEBHOOK_SECRET_KEY` matches Smartlead configuration
- Check signature header format: `X-Smartlead-Signature`
- For development, you can temporarily disable by not setting `WEBHOOK_SECRET_KEY`

## Architecture Benefits

### Before Refactoring
- ❌ JSON files (not scalable, no concurrency control)
- ❌ Hardcoded service initialization
- ❌ Scattered configuration
- ❌ No webhook security
- ❌ Difficult to test

### After Refactoring
- ✅ SQLite database (scalable, ACID transactions)
- ✅ Dependency injection (testable, modular)
- ✅ Centralized configuration (validated, type-safe)
- ✅ Webhook security (signature verification, rate limiting)
- ✅ Easy to test (mockable services, test fixtures)

## Next Steps

1. **Production Deployment:**
   - Replace SQLite with PostgreSQL for production
   - Set up proper secrets management
   - Configure production `WEBHOOK_SECRET_KEY`
   - Set up database backups

2. **Monitoring:**
   - Add logging infrastructure
   - Set up error tracking (Sentry, etc.)
   - Monitor database performance

3. **Scaling:**
   - Consider Redis for caching
   - Add message queue for async processing
   - Implement connection pooling

## Related Documentation

- `MIGRATION_GUIDE.md` - Migration from JSON to SQLite
- `ARCHITECTURE.md` - Original architecture documentation
- `README.md` - General project overview

