"""
Sync marketing events from Supabase into SalesGPT lead DB.

Usage:
  python3 scripts/sync_marketing_events.py --limit 1000

Environment:
  - SUPABASE_DATABASE_URL (preferred) or DATABASE_URL (if DATABASE_URL points to Supabase)
  - SALESGPT_DATABASE_URL (preferred) or DATABASE_URL for SalesGPT DB
"""

import argparse
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load .env.local if it exists
env_file = project_root / '.env.local'
if env_file.exists():
    load_dotenv(env_file)

from salesgpt.config import get_settings
from salesgpt.db.connection import DatabaseManager
from services.attribution.marketing_events_ingestor import MarketingEventsIngestor


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=1000, help="Maximum events to process")
    args = parser.parse_args()

    settings = get_settings()
    if not settings.supabase_database_url:
        raise SystemExit(
            "SUPABASE_DATABASE_URL not configured. "
            "Set SUPABASE_DATABASE_URL (recommended) or DATABASE_URL to the Supabase pooler URL."
        )

    # Initialize SalesGPT database
    db_manager = DatabaseManager(settings.database_url)
    db_manager.create_tables()

    # Create ingestor
    ingestor = MarketingEventsIngestor(settings.supabase_database_url, db_manager)

    # Sync events
    processed, updated, not_found = ingestor.sync_events(limit=args.limit)

    print(f"Events processed: {processed}")
    print(f"Leads updated: {updated}")
    print(f"Events (leads not found): {not_found}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

