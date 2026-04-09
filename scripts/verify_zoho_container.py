#!/usr/bin/env python3
"""
Load .env, build a fresh Settings(), and construct ServiceContainer (Zoho or HubSpot/Smartlead).

Requires project deps: pip install -r requirements.txt

Usage:
  python3 scripts/verify_zoho_container.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(ROOT))

from zoho_oauth_dotenv import load_dotenv


def main() -> int:
    load_dotenv(ROOT / ".env")
    try:
        from salesgpt.config.settings import Settings
        from salesgpt.container import ServiceContainer
    except ImportError as e:
        print("Install dependencies: pip install -r requirements.txt", file=sys.stderr)
        print(e, file=sys.stderr)
        return 1

    settings = Settings()
    if not settings.use_zoho_stack:
        print("use_zoho_stack is false — set USE_ZOHO_STACK=true in .env for Zoho container.", file=sys.stderr)
        return 1

    try:
        c = ServiceContainer(settings)
    except Exception as e:
        print("ServiceContainer failed:", e, file=sys.stderr)
        return 1

    outbound = type(c.smartlead).__name__
    crm = type(c.crm).__name__
    print(f"OK: ServiceContainer(use_zoho_stack=True)")
    print(f"  outbound: {outbound}")
    print(f"  crm: {crm}")
    c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
