#!/bin/bash
# Marketing Events Sync Script
# Run this periodically (e.g., via cron) to sync events from Supabase to SalesGPT

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# Activate virtual environment if it exists
if [ -f "$PROJECT_ROOT/venv/bin/activate" ]; then
    source "$PROJECT_ROOT/venv/bin/activate"
fi

# Add project root to Python path
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Run sync script
python3 "$PROJECT_ROOT/scripts/sync_marketing_events.py" --limit 1000
