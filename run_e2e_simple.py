#!/usr/bin/env python3
"""
Simple E2E test with mocked APIs.
Runs the queue builder with mocked API responses.
"""
import asyncio
import os
import sys
from pathlib import Path

# Load environment variables from .env.local if it exists
env_local = Path(__file__).parent / ".env.local"
if env_local.exists():
    print(f"📄 Loading environment from {env_local}")
    with open(env_local, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                # Only set if not already set
                if key not in os.environ:
                    os.environ[key] = value

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Set environment variables for mock APIs (override real APIs)
os.environ["APOLLO_API_URL"] = "http://localhost:8001"
os.environ["SMARTLEAD_API_URL"] = "http://localhost:8001"
os.environ["HUBSPOT_API_URL"] = "http://localhost:8001"
os.environ["USE_MOCK_APIS"] = "true"

# Set required API keys (dummy values for mocks, but keep OpenAI real)
os.environ["APOLLO_API_KEY"] = "mock_apollo_key"
os.environ["SMARTLEAD_API_KEY"] = "mock_smartlead_key"
os.environ["HUBSPOT_ACCESS_TOKEN"] = "mock_hubspot_token"
os.environ["SMARTLEAD_FROM_EMAIL"] = "test@example.com"
os.environ["SMARTLEAD_FROM_NAME"] = "Test Sender"
os.environ["SMARTLEAD_CAMPAIGN_NAME"] = "Test Campaign"
os.environ["DATABASE_URL"] = "sqlite:///./test_e2e.db"
os.environ["DEFAULT_BATCH_SIZE"] = "5"
os.environ["DEFAULT_GEOGRAPHY"] = "New York, NY"
os.environ["DEFAULT_SPECIALTY"] = "Dental"

# Disable tools to avoid LLMSingleActionAgent issue
os.environ["SALESGPT_USE_TOOLS"] = "false"

# Ensure OpenAI API key is set (from .env.local)
if not os.environ.get("OPENAI_API_KEY"):
    print("⚠️  Warning: OPENAI_API_KEY not found. Email generation may fail.")
else:
    print(f"✅ OpenAI API key loaded (length: {len(os.environ.get('OPENAI_API_KEY', ''))})")

from salesgpt.config import get_settings
from salesgpt.container import ServiceContainer


async def main():
    """Run E2E test."""
    print("🚀 Starting E2E Test with Mocked APIs")
    print("=" * 50)
    print()
    
    # Check if mock API is running
    import urllib.request
    try:
        response = urllib.request.urlopen("http://localhost:8001/health", timeout=2)
        print("✅ Mock API server is running")
    except:
        print("❌ Mock API server not running!")
        print("   Start it with: python3 mock_api_server.py")
        sys.exit(1)
    
    print()
    print("📋 Configuration:")
    print(f"   Apollo API: {os.environ.get('APOLLO_API_URL')}")
    print(f"   Smartlead API: {os.environ.get('SMARTLEAD_API_URL')}")
    print(f"   HubSpot API: {os.environ.get('HUBSPOT_API_URL')}")
    print(f"   Database: {os.environ.get('DATABASE_URL')}")
    print(f"   Batch Size: {os.environ.get('DEFAULT_BATCH_SIZE')}")
    print()
    
    # Get settings
    settings = get_settings()
    
    # Override to disable tools
    settings.salesgpt_verbose = False
    
    # Create container
    print("🔧 Initializing services...")
    container = ServiceContainer(settings)
    print("✅ Services initialized")
    print()
    
    # Run queue builder for one batch
    print("🎯 Processing leads...")
    print(f"   Geography: {settings.default_geography}")
    print(f"   Specialty: {settings.default_specialty}")
    print(f"   Batch Size: {settings.default_batch_size}")
    print()
    
    try:
        # Run for one iteration
        await container.queue_builder.run(
            geography=settings.default_geography,
            specialty=settings.default_specialty,
            batch_size=settings.default_batch_size,
            min_score=10
        )
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        container.close()
        print("\n✅ E2E test completed!")
        print()
        print("📊 Check results:")
        print(f"   Database: {os.environ.get('DATABASE_URL')}")
        print("   View in dashboard: streamlit run dashboard/streamlit_app.py")


if __name__ == "__main__":
    asyncio.run(main())

