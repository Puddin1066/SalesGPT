"""
Verify Stripe webhook endpoint configuration.

Checks:
1. Webhook endpoint is accessible
2. Environment variables are set correctly
3. Webhook secret format is valid
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv
import requests

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load .env.local if it exists
env_file = project_root / '.env.local'
if env_file.exists():
    load_dotenv(env_file)

import stripe
from salesgpt.config import get_settings


def check_webhook_endpoint(webhook_id: str):
    """Check webhook endpoint status in Stripe."""
    settings = get_settings()
    if not settings.stripe_api_key:
        print("❌ STRIPE_API_KEY not configured")
        return False
    
    stripe.api_key = settings.stripe_api_key
    
    try:
        endpoint = stripe.WebhookEndpoint.retrieve(webhook_id)
        print(f"\n✅ Webhook Endpoint Status:")
        print(f"   ID: {endpoint.id}")
        print(f"   URL: {endpoint.url}")
        print(f"   Status: {endpoint.status}")
        print(f"   Enabled Events: {', '.join(endpoint.enabled_events)}")
        
        if endpoint.status == 'enabled':
            print(f"\n✅ Webhook is enabled and active")
            return True
        else:
            print(f"\n⚠️  Webhook status: {endpoint.status}")
            return False
            
    except stripe.error.StripeError as e:
        print(f"❌ Error retrieving webhook: {e}")
        return False


def check_environment_variables():
    """Check if required environment variables are set."""
    print("\n🔍 Checking Environment Variables:")
    
    # Check SalesGPT
    settings = get_settings()
    has_stripe_key = bool(settings.stripe_api_key)
    has_webhook_secret = bool(settings.stripe_webhook_secret)
    
    print(f"   SalesGPT:")
    print(f"   - STRIPE_API_KEY: {'✅ SET' if has_stripe_key else '❌ NOT SET'}")
    print(f"   - STRIPE_WEBHOOK_SECRET: {'✅ SET' if has_webhook_secret else '❌ NOT SET'}")
    
    # Check FireGEO (from .env.local)
    webhook_secret_key = os.getenv("WEBHOOK_SECRET_KEY")
    stripe_webhook_secret_live = os.getenv("STRIPE_WEBHOOK_SECRET_LIVE")
    stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    
    print(f"\n   FireGEO (.env.local):")
    print(f"   - WEBHOOK_SECRET_KEY: {'✅ SET' if webhook_secret_key else '❌ NOT SET'}")
    print(f"   - STRIPE_WEBHOOK_SECRET_LIVE: {'✅ SET' if stripe_webhook_secret_live else '❌ NOT SET'}")
    print(f"   - STRIPE_WEBHOOK_SECRET: {'✅ SET' if stripe_webhook_secret else '❌ NOT SET'}")
    
    # Note: FireGEO expects STRIPE_WEBHOOK_SECRET_LIVE or STRIPE_WEBHOOK_SECRET
    if webhook_secret_key and not stripe_webhook_secret_live and not stripe_webhook_secret:
        print(f"\n⚠️  NOTE: FireGEO expects STRIPE_WEBHOOK_SECRET_LIVE or STRIPE_WEBHOOK_SECRET")
        print(f"   You have WEBHOOK_SECRET_KEY set. Consider renaming it or adding:")
        print(f"   STRIPE_WEBHOOK_SECRET_LIVE={webhook_secret_key}")
    
    # Check secret format
    secret_to_check = stripe_webhook_secret_live or stripe_webhook_secret or webhook_secret_key
    if secret_to_check:
        if secret_to_check.startswith("whsec_"):
            print(f"\n✅ Webhook secret format is correct (starts with whsec_)")
        else:
            print(f"\n⚠️  Webhook secret format may be incorrect")
            print(f"   Expected format: whsec_...")
            print(f"   Current format: {secret_to_check[:10]}...")
    
    return True


def test_webhook_accessibility(url: str):
    """Test if webhook endpoint is accessible."""
    print(f"\n🌐 Testing Webhook Endpoint Accessibility:")
    print(f"   URL: {url}")
    
    try:
        # Send a simple GET request to check if endpoint exists
        # (Stripe webhooks are POST only, but we can check if the route exists)
        response = requests.get(url, timeout=5)
        print(f"   GET Response: {response.status_code}")
        if response.status_code == 405:  # Method Not Allowed is expected for POST-only endpoints
            print(f"   ✅ Endpoint exists (405 = POST only, which is correct)")
            return True
        elif response.status_code == 404:
            print(f"   ❌ Endpoint not found (404)")
            return False
        else:
            print(f"   ⚠️  Unexpected status: {response.status_code}")
            return True  # Endpoint exists, just unexpected method
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error accessing endpoint: {e}")
        return False


def main():
    print("\n" + "="*60)
    print("Stripe Webhook Verification")
    print("="*60)
    
    # Check environment variables
    check_environment_variables()
    
    # Check webhook endpoint in Stripe
    webhook_id = "we_1Sj2gzQg9yJEawqIqatd7Cos"  # From previous setup
    print(f"\n" + "="*60)
    check_webhook_endpoint(webhook_id)
    
    # Test endpoint accessibility
    print(f"\n" + "="*60)
    test_webhook_accessibility("https://gemflush.com/api/stripe/webhook")
    
    print(f"\n" + "="*60)
    print("Verification Complete")
    print("="*60)
    print("\n💡 To test with a real Stripe event:")
    print("   1. Use Stripe CLI: stripe listen --forward-to https://gemflush.com/api/stripe/webhook")
    print("   2. Trigger test event: stripe trigger invoice.paid")
    print("   3. Or complete a test checkout in Stripe Dashboard")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

