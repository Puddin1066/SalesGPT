"""
Sync Supabase Auth signups into SalesGPT lead DB.

Usage:
  python3 scripts/sync_supabase_signups.py --days-back 30

Environment:
  - SUPABASE_DATABASE_URL (preferred) or DATABASE_URL (if DATABASE_URL points to Supabase)
  - SALESGPT_DATABASE_URL (preferred) or DATABASE_URL for SalesGPT DB
"""

import argparse

from salesgpt.config import get_settings
from salesgpt.container import ServiceContainer
from services.attribution.supabase_signup_ingestor import SupabaseSignupIngestor


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days-back", type=int, default=30)
    parser.add_argument("--limit", type=int, default=5000)
    args = parser.parse_args()

    settings = get_settings()
    if not settings.supabase_database_url:
        raise SystemExit(
            "SUPABASE_DATABASE_URL not configured. "
            "Set SUPABASE_DATABASE_URL (recommended) or DATABASE_URL to the Supabase pooler URL."
        )

    container = ServiceContainer(settings)
    ingestor = SupabaseSignupIngestor(settings.supabase_database_url, container.state_manager)
    matched, updated = ingestor.sync_recent_signups(days_back=args.days_back, limit=args.limit)
    print(f"Matched leads: {matched}")
    print(f"Updated leads (free_signup_at set): {updated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


