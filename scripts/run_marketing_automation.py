#!/usr/bin/env python3
"""
Marketing & sales automation entrypoint.

- daily-send: Apollo → Smartlead (sequences) → HubSpot contacts (see main_agent).
- review-queue: Apollo → SalesGPT personalized copy → HubSpot → DB pending_review (Streamlit/dashboard).
- webhook-info: how to run reply handler (SalesGPT + Cal + HubSpot).

Set MARKETING_AUTOMATION_ENABLED=true when ready, or pass --force for ad-hoc runs.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _require_automation(settings, force: bool) -> None:
    if not settings.marketing_automation_enabled and not force:
        print(
            "Marketing automation is disabled. Set MARKETING_AUTOMATION_ENABLED=true in .env "
            "or pass --force to run anyway."
        )
        sys.exit(1)


async def cmd_daily_send(args, settings) -> None:
    from salesgpt.container import ServiceContainer

    container = ServiceContainer(settings)
    orchestrator = container.orchestrator
    await orchestrator.run_daily_pipeline(
        geography=args.geography,
        specialty=args.specialty,
        lead_limit=args.limit,
    )


async def cmd_review_queue(args, settings) -> None:
    """One batch of AI-generated emails into HubSpot + pending_review (no Smartlead)."""
    from salesgpt.db.connection import DatabaseManager
    from state.state_manager import StateManager
    from services.apollo.apollo_agent import ApolloAgent
    from services.salesgpt.salesgpt_wrapper import SalesGPTWrapper
    from services.crm.hubspot_agent import HubSpotAgent
    from services.crm.zoho_crm_agent import ZohoCRMAgent
    from services.analytics import ABTestManager, ApolloABManager
    from services.competitor.competitor_agent import CompetitorAgent
    from services.visibility.gemflush_agent import GEMflushAgent
    from services.scoring.geo_scorer import GEOScorer
    from workflows.background_queue_builder import BackgroundQueueBuilder

    db_manager = DatabaseManager(settings.database_url)
    db_manager.create_tables()
    state_manager = StateManager(db_manager)

    apollo = ApolloAgent(api_key=settings.apollo_api_key)
    salesgpt = SalesGPTWrapper(
        config_path=settings.salesgpt_config_path,
        model_name=settings.gpt_model,
        verbose=settings.salesgpt_verbose,
    )

    if settings.use_zoho_stack:
        hubspot = ZohoCRMAgent(
            client_id=settings.zoho_client_id,
            client_secret=settings.zoho_client_secret,
            refresh_token=settings.zoho_refresh_token,
            accounts_domain=settings.zoho_accounts_domain,
            crm_api_base=settings.zoho_crm_api_base,
        )
    elif (
        settings.hubspot_client_id
        and settings.hubspot_client_secret
        and settings.hubspot_refresh_token
    ):
        hubspot = HubSpotAgent(
            client_id=settings.hubspot_client_id,
            client_secret=settings.hubspot_client_secret,
            refresh_token=settings.hubspot_refresh_token,
        )
    else:
        hubspot = HubSpotAgent(api_key=settings.hubspot_access_token)

    ab_manager = ABTestManager(state_manager)
    apollo_ab = ApolloABManager(state_manager)
    visibility = GEMflushAgent(
        api_key=settings.gemflush_api_key,
        api_base_url=settings.gemflush_api_url,
        use_real_api=settings.gemflush_use_real_api,
        model_name=settings.gpt_model,
    )
    competitor = CompetitorAgent(visibility_agent=visibility)
    scorer = GEOScorer()

    builder = BackgroundQueueBuilder(
        apollo=apollo,
        salesgpt=salesgpt,
        hubspot=hubspot,
        state_manager=state_manager,
        ab_manager=ab_manager,
        apollo_ab=apollo_ab,
        competitor=competitor,
        visibility=visibility,
        scorer=scorer,
    )

    n = await builder.run_once(
        geography=args.geography,
        specialty=args.specialty,
        batch_size=args.batch_size,
        min_score=args.min_score,
        queue_refill_threshold=args.queue_threshold,
        force=args.force_batch,
    )
    print(f"Done. Leads processed this run: {n}")


def cmd_webhook_info(args, settings) -> None:
    port = args.port
    print(
        "Agent-supported replies: run the FastAPI webhook (payload matches Smartlead-style fields).\n"
        f"  uvicorn webhook_handler:app --host 0.0.0.0 --port {port}\n"
        "Point Smartlead webhooks here, or adapt the handler for Zoho Mail inbound notifications.\n"
        "Optional: WEBHOOK_SECRET_KEY for X-Smartlead-Signature verification."
    )


def main() -> None:
    from salesgpt.config import get_settings

    settings = get_settings()
    parser = argparse.ArgumentParser(
        description="SalesGPT marketing automation (Smartlead + SalesGPT + HubSpot)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Run even if MARKETING_AUTOMATION_ENABLED is false",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    p_daily = sub.add_parser("daily-send", help="Apollo → Smartlead + HubSpot (main_agent pipeline)")
    p_daily.add_argument("--geography", type=str, default=settings.default_geography)
    p_daily.add_argument("--specialty", type=str, default=settings.default_specialty)
    p_daily.add_argument("--limit", type=int, default=50)

    p_queue = sub.add_parser(
        "review-queue",
        help="One batch: personalized AI emails → HubSpot + pending_review queue",
    )
    p_queue.add_argument("--geography", type=str, default=settings.default_geography)
    p_queue.add_argument("--specialty", type=str, default=settings.default_specialty)
    p_queue.add_argument("--batch-size", type=int, default=settings.default_batch_size)
    p_queue.add_argument("--min-score", type=int, default=10)
    p_queue.add_argument(
        "--queue-threshold",
        type=int,
        default=20,
        help="Skip fetch if pending_review count is at or above this (unless --force-batch)",
    )
    p_queue.add_argument(
        "--force-batch",
        action="store_true",
        help="Fetch and process even if review queue is already full",
    )

    p_wh = sub.add_parser("webhook-info", help="Print how to start the Smartlead reply webhook")
    p_wh.add_argument("--port", type=int, default=settings.webhook_port)

    args = parser.parse_args()

    if args.command == "webhook-info":
        cmd_webhook_info(args, settings)
        return

    _require_automation(settings, args.force)

    if args.command == "daily-send":
        asyncio.run(cmd_daily_send(args, settings))
    elif args.command == "review-queue":
        asyncio.run(cmd_review_queue(args, settings))


if __name__ == "__main__":
    main()
