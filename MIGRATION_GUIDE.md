# Migration Guide: JSON to SQLite Refactoring

This guide documents the breaking changes introduced in the Priority 1 refactoring and how to migrate your existing setup.

## Overview

The refactoring introduces:
1. **SQLite database** replacing JSON file-based state management
2. **Dependency injection** for better testability
3. **Centralized configuration** using Pydantic Settings
4. **Webhook security** with signature verification

## Breaking Changes

### 1. StateManager Constructor

**Before:**
```python
from state import StateManager
state = StateManager()  # Used file paths
```

**After:**
```python
from salesgpt.config import get_settings
from salesgpt.db.connection import DatabaseManager
from state.state_manager import StateManager

settings = get_settings()
db_manager = DatabaseManager(settings.database_url)
state = StateManager(db_manager)  # Requires DatabaseManager
```

### 2. Service Constructors

All service constructors now require explicit API keys/config parameters instead of reading from environment directly.

**Before:**
```python
from services.apollo import ApolloAgent
apollo = ApolloAgent()  # Read from env internally
```

**After:**
```python
from services.apollo.apollo_agent import ApolloAgent
from salesgpt.config import get_settings

settings = get_settings()
apollo = ApolloAgent(api_key=settings.apollo_api_key)
```

### 3. Main Entry Points

**Before:**
```python
from main_agent import ASSCHOrchestrator
orchestrator = ASSCHOrchestrator()  # Initialized internally
```

**After:**
```python
from salesgpt.config import get_settings
from salesgpt.container import ServiceContainer

settings = get_settings()
container = ServiceContainer(settings)
orchestrator = container.orchestrator
```

### 4. Database Required

SQLite database file (`salesgpt.db` by default) replaces JSON files:
- `state/conversation_states.json` → `salesgpt.db` (conversations table)
- `state/lead_states.json` → `salesgpt.db` (leads table)

### 5. Webhook Security

Smartlead webhooks must include valid signature header (if `WEBHOOK_SECRET_KEY` is configured).

## Migration Steps

### Step 1: Install New Dependencies

```bash
pip install -r requirements.txt
# Or with poetry:
poetry install
```

New dependencies:
- `sqlalchemy>=2.0.0`
- `alembic>=1.13.0`
- `pydantic-settings>=2.0.0`
- `slowapi>=0.1.9`

### Step 2: Update Environment Variables

Add to your `.env` file:

```bash
# Database
DATABASE_URL=sqlite:///./salesgpt.db

# Webhook Security
WEBHOOK_SECRET_KEY=your_secret_key_here

# Existing variables remain the same
OPENAI_API_KEY=...
APOLLO_API_KEY=...
SMARTLEAD_API_KEY=...
# etc.
```

### Step 3: Migrate JSON Data to SQLite

Run the migration script to import existing JSON data:

```bash
python scripts/migrate_json_to_sqlite.py
```

This will:
- Create the SQLite database
- Import leads from `state/lead_states.json`
- Import conversations from `state/conversation_states.json`

**Note:** The script will skip existing records, so it's safe to run multiple times.

### Step 4: Update Your Code

#### For CLI Scripts

**Before:**
```python
from main_agent import ASSCHOrchestrator

orchestrator = ASSCHOrchestrator()
await orchestrator.run_daily_pipeline(...)
```

**After:**
```python
from salesgpt.config import get_settings
from salesgpt.container import ServiceContainer

settings = get_settings()
container = ServiceContainer(settings)
orchestrator = container.orchestrator
await orchestrator.run_daily_pipeline(...)
```

#### For Webhook Handlers

The webhook handler (`webhook_handler.py`) has been updated automatically. Just ensure:
- `WEBHOOK_SECRET_KEY` is set in `.env`
- Smartlead webhooks include `X-Smartlead-Signature` header

#### For Custom Integrations

If you're using services directly:

**Before:**
```python
from services.apollo import ApolloAgent
apollo = ApolloAgent()
```

**After:**
```python
from services.apollo.apollo_agent import ApolloAgent
from salesgpt.config import get_settings

settings = get_settings()
apollo = ApolloAgent(api_key=settings.apollo_api_key)
```

### Step 5: Verify Migration

1. Check database file exists: `ls salesgpt.db`
2. Verify data was migrated:
   ```python
   from salesgpt.config import get_settings
   from salesgpt.db.connection import DatabaseManager
   from salesgpt.models.database import Lead
   
   settings = get_settings()
   db_manager = DatabaseManager(settings.database_url)
   
   with db_manager.session() as session:
       lead_count = session.query(Lead).count()
       print(f"Migrated {lead_count} leads")
   ```

3. Test webhook endpoint:
   ```bash
   curl -X POST http://localhost:8001/webhook/smartlead \
     -H "Content-Type: application/json" \
     -d '{"event": "email_replied", ...}'
   ```

## Rollback Plan

If you need to rollback:

1. **Keep JSON files**: The migration script doesn't delete JSON files
2. **Revert code**: Check out previous git commit
3. **Restore dependencies**: Use previous `requirements.txt`

## Troubleshooting

### Database Connection Errors

- Ensure SQLite is available: `sqlite3 --version`
- Check database path permissions
- Verify `DATABASE_URL` in `.env`

### Migration Script Fails

- Check JSON files exist: `ls state/*.json`
- Verify JSON files are valid: `python -m json.tool state/lead_states.json`
- Check for duplicate emails (should be handled automatically)

### Webhook Signature Verification Fails

- Verify `WEBHOOK_SECRET_KEY` matches Smartlead configuration
- Check signature header format: `X-Smartlead-Signature`
- For development, you can temporarily disable verification by not setting `WEBHOOK_SECRET_KEY`

### Import Errors

- Ensure all new dependencies are installed
- Check Python path includes project root
- Verify `salesgpt/` package structure

## Support

For issues or questions:
1. Check existing GitHub issues
2. Review `ARCHITECTURE.md` for system overview
3. Check test files in `tests/` for usage examples

## Next Steps

After migration:
1. Remove old JSON files (after verifying data migration)
2. Set up database backups
3. Configure production `WEBHOOK_SECRET_KEY`
4. Update deployment scripts to include database initialization



