"""
Set up Stripe webhook endpoint via Stripe API.

This script creates or updates a webhook endpoint in Stripe that points to
the FireGEO webhook route for processing marketing events.

Usage:
  python3 scripts/setup_stripe_webhook.py --url https://your-domain.vercel.app/api/stripe/webhook
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

import stripe
from salesgpt.config import get_settings


def list_webhook_endpoints():
    """List all existing webhook endpoints."""
    try:
        endpoints = stripe.WebhookEndpoint.list(limit=100)
        return endpoints.data
    except stripe.error.StripeError as e:
        print(f"❌ Error listing webhooks: {e}")
        return []


def find_existing_webhook(url: str):
    """Find existing webhook endpoint by URL."""
    endpoints = list_webhook_endpoints()
    for endpoint in endpoints:
        if endpoint.url == url:
            return endpoint
    return None


def create_webhook_endpoint(url: str, enabled_events: list):
    """Create a new webhook endpoint."""
    try:
        endpoint = stripe.WebhookEndpoint.create(
            url=url,
            enabled_events=enabled_events,
            description="FireGEO Marketing Events - Paid Pro conversions",
            api_version="2024-12-18.acacia"  # Use latest API version
        )
        return endpoint
    except stripe.error.StripeError as e:
        print(f"❌ Error creating webhook: {e}")
        return None


def update_webhook_endpoint(endpoint_id: str, url: str, enabled_events: list):
    """Update an existing webhook endpoint."""
    try:
        endpoint = stripe.WebhookEndpoint.modify(
            endpoint_id,
            url=url,
            enabled_events=enabled_events,
            description="FireGEO Marketing Events - Paid Pro conversions"
        )
        return endpoint
    except stripe.error.StripeError as e:
        print(f"❌ Error updating webhook: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Set up Stripe webhook endpoint")
    parser.add_argument(
        "--url",
        type=str,
        required=True,
        help="Webhook URL (e.g., https://your-domain.vercel.app/api/stripe/webhook)"
    )
    parser.add_argument(
        "--create-only",
        action="store_true",
        help="Only create new endpoint, don't update existing"
    )
    args = parser.parse_args()

    # Get Stripe API key
    settings = get_settings()
    if not settings.stripe_api_key:
        print("❌ STRIPE_API_KEY or STRIPE_SECRET_KEY not configured")
        print("   Add it to .env.local:")
        print("   STRIPE_API_KEY=sk_live_...")
        return 1

    # Initialize Stripe
    stripe.api_key = settings.stripe_api_key

    # Required events for marketing attribution
    required_events = [
        "invoice.paid",  # For paid_pro events
        "checkout.session.completed",  # Already handled
        "customer.subscription.updated",  # Already handled
        "customer.subscription.deleted",  # Already handled
    ]

    print(f"\n🔗 Setting up Stripe webhook endpoint")
    print(f"   URL: {args.url}")
    print(f"   Events: {', '.join(required_events)}")

    # Check if webhook already exists
    existing = find_existing_webhook(args.url)
    
    if existing:
        if args.create_only:
            print(f"\n⚠️  Webhook endpoint already exists (ID: {existing.id})")
            print("   Use without --create-only to update it")
            return 0
        
        print(f"\n📝 Updating existing webhook endpoint (ID: {existing.id})")
        endpoint = update_webhook_endpoint(existing.id, args.url, required_events)
        
        if endpoint:
            print(f"✅ Webhook endpoint updated successfully!")
            print(f"\n📋 Webhook Details:")
            print(f"   ID: {endpoint.id}")
            print(f"   URL: {endpoint.url}")
            print(f"   Status: {endpoint.status}")
            
            # Secret is only available on creation, not update
            # Need to retrieve it separately or check existing secret
            try:
                if hasattr(endpoint, 'secret') and endpoint.secret:
                    print(f"   Secret: {endpoint.secret}")
                    print(f"\n⚠️  IMPORTANT: Add this secret to FireGEO environment variables:")
                    print(f"   STRIPE_WEBHOOK_SECRET_LIVE={endpoint.secret}")
                else:
                    print(f"\n⚠️  NOTE: Webhook secret not shown (only available on creation)")
                    print(f"   To get the secret:")
                    print(f"   1. Go to Stripe Dashboard → Developers → Webhooks")
                    print(f"   2. Click on webhook ID: {endpoint.id}")
                    print(f"   3. Click 'Reveal' next to 'Signing secret'")
                    print(f"   4. Add to FireGEO: STRIPE_WEBHOOK_SECRET_LIVE=whsec_...")
            except AttributeError:
                print(f"\n⚠️  NOTE: Webhook secret not shown (only available on creation)")
                print(f"   To get the secret:")
                print(f"   1. Go to Stripe Dashboard → Developers → Webhooks")
                print(f"   2. Click on webhook ID: {endpoint.id}")
                print(f"   3. Click 'Reveal' next to 'Signing secret'")
                print(f"   4. Add to FireGEO: STRIPE_WEBHOOK_SECRET_LIVE=whsec_...")
            return 0
        else:
            return 1
    else:
        print(f"\n➕ Creating new webhook endpoint")
        endpoint = create_webhook_endpoint(args.url, required_events)
        
        if endpoint:
            print(f"✅ Webhook endpoint created successfully!")
            print(f"\n📋 Webhook Details:")
            print(f"   ID: {endpoint.id}")
            print(f"   URL: {endpoint.url}")
            print(f"   Status: {endpoint.status}")
            
            # Secret should be available on creation
            try:
                secret = endpoint.secret if hasattr(endpoint, 'secret') else None
                if secret:
                    print(f"   Secret: {secret}")
                    print(f"\n⚠️  IMPORTANT: Add this secret to FireGEO environment variables:")
                    print(f"   STRIPE_WEBHOOK_SECRET_LIVE={secret}")
                else:
                    print(f"\n⚠️  NOTE: Secret not in response. Get it from Stripe Dashboard:")
                    print(f"   1. Go to Stripe Dashboard → Developers → Webhooks")
                    print(f"   2. Click on webhook ID: {endpoint.id}")
                    print(f"   3. Click 'Reveal' next to 'Signing secret'")
            except AttributeError:
                print(f"\n⚠️  NOTE: Get secret from Stripe Dashboard:")
                print(f"   1. Go to Stripe Dashboard → Developers → Webhooks")
                print(f"   2. Click on webhook ID: {endpoint.id}")
                print(f"   3. Click 'Reveal' next to 'Signing secret'")
            return 0
        else:
            return 1


if __name__ == "__main__":
    sys.exit(main())

