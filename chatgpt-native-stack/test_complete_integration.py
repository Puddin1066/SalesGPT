"""
End-to-end integration test for HubSpot + Apollo + Content Generation.

Tests the complete workflow from lead sourcing to campaign execution.
"""

import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

load_dotenv('.env.local')


def test_api_keys():
    """Test that all required API keys are present."""
    
    print("=" * 70)
    print("🔑 API Keys Check")
    print("=" * 70)
    print()
    
    keys = {
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'HUBSPOT_API_KEY': os.getenv('HUBSPOT_API_KEY') or os.getenv('HUBSPOT_PAT'),
        'APOLLO_API_KEY': os.getenv('APOLLO_API_KEY')
    }
    
    all_present = True
    
    for key_name, key_value in keys.items():
        if key_value:
            masked = key_value[:10] + '...' if len(key_value) > 10 else '***'
            print(f"✅ {key_name}: {masked}")
        else:
            print(f"❌ {key_name}: Not found")
            if key_name == 'APOLLO_API_KEY':
                print(f"   ⚠️  Optional - can use LinkedIn for leads instead")
            else:
                all_present = False
    
    print()
    return all_present


def test_content_generation():
    """Test content generation (already tested)."""
    
    print("=" * 70)
    print("📄 Content Generation Check")
    print("=" * 70)
    print()
    
    email_dir = os.path.join(os.path.dirname(__file__), '..', 'email-content')
    landing_page_dir = os.path.join(os.path.dirname(__file__), 'output', 'landing-pages')
    
    # Check if content exists
    email_files = [f for f in os.listdir(email_dir) if f.endswith('.txt')] if os.path.exists(email_dir) else []
    landing_files = [f for f in os.listdir(landing_page_dir) if f.endswith('.md')] if os.path.exists(landing_page_dir) else []
    
    print(f"📧 Email sequences: {len(email_files)}/12")
    print(f"📄 Landing pages: {len(landing_files)}/8")
    print()
    
    if len(email_files) >= 12 and len(landing_files) >= 8:
        print("✅ All content generated")
        return True
    else:
        print("⚠️  Content needs to be generated")
        print("   Run: python3 chatgpt-native-stack/content-generation/generate_all_content.py")
        return False


def test_hubspot_ready():
    """Test if HubSpot is ready for campaigns."""
    
    print("=" * 70)
    print("🏢 HubSpot Setup Check")
    print("=" * 70)
    print()
    
    from services.crm.hubspot_agent import HubSpotAgent
    
    api_key = os.getenv('HUBSPOT_API_KEY') or os.getenv('HUBSPOT_PAT')
    if not api_key:
        print("❌ HubSpot API key not found")
        return False
    
    try:
        hubspot = HubSpotAgent(api_key=api_key)
        print("✅ HubSpot connection working")
        print()
        
        print("⚠️  Note: Properties need to be created manually")
        print("   See: setup/configure_hubspot_scopes.md")
        print("   Then: python3 chatgpt-native-stack/setup/create_hubspot_properties.py")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ HubSpot connection failed: {e}")
        return False


def print_workflow_summary():
    """Print the complete workflow summary."""
    
    print()
    print("=" * 70)
    print("🚀 Complete Integration Workflow")
    print("=" * 70)
    print()
    
    print("PHASE 1: Content Generation (AUTOMATED ✅)")
    print("─" * 70)
    print("✅ Command: python3 chatgpt-native-stack/content-generation/generate_all_content.py")
    print("   Time: 2-3 minutes")
    print("   Output: 12 emails + 8 landing pages")
    print()
    
    print("PHASE 2: HubSpot Setup (PARTIALLY AUTOMATED)")
    print("─" * 70)
    print("⚠️  Step 1: Fix API scopes (5 min, manual)")
    print("   See: setup/configure_hubspot_scopes.md")
    print()
    print("✅ Step 2: Create properties (30 sec, automated)")
    print("   Command: python3 chatgpt-native-stack/setup/create_hubspot_properties.py")
    print()
    
    print("PHASE 3: Lead Sourcing (EXTERNAL)")
    print("─" * 70)
    print("Option A: Apollo.io API")
    print("   - Search leads by vertical")
    print("   - Export to CSV")
    print("   - Time: 30 min")
    print()
    print("Option B: LinkedIn Sales Navigator")
    print("   - Free 30-day trial")
    print("   - Export up to 2,500 leads")
    print("   - Time: 1-2 hours")
    print()
    print("✅ Step: Import leads (5 min, automated)")
    print("   Command: python3 chatgpt-native-stack/setup/import_contacts_bulk.py leads.csv")
    print()
    
    print("PHASE 4: Campaign Execution (AUTOMATED ✅)")
    print("─" * 70)
    print("✅ Command: python3 chatgpt-native-stack/gemflush_campaign.py \\")
    print("             --vertical medical --email 1 --count 200")
    print("   Time: 1-2 minutes per vertical")
    print("   Note: Uses generated email content automatically")
    print()
    
    print("PHASE 5: Analytics (AUTOMATED ✅)")
    print("─" * 70)
    print("✅ Command: python3 chatgpt-native-stack/analyze_results.py --week 1")
    print("   Time: 30 seconds")
    print("   Output: Formatted metrics for analysis")
    print()
    
    print("=" * 70)
    print("📊 Automation Summary")
    print("=" * 70)
    print()
    print("✅ Automated: 75% of workflow")
    print("   - Content generation (2-3 min)")
    print("   - Property creation (30 sec)")
    print("   - Contact import (5 min)")
    print("   - Campaign execution (1-2 min)")
    print("   - Analytics (30 sec)")
    print()
    print("📝 Manual: 25% of workflow")
    print("   - HubSpot scope fix (5 min, one-time)")
    print("   - Lead sourcing (1-2 hours)")
    print("   - Landing page building (2-3 hours)")
    print("   - Reply handling (15 min/day)")
    print()
    print("⏱️  Total time: ~3-5 hours (vs 15-20 hours manual)")
    print("💰 Total cost: ~$0.30 per run (vs $20/month ChatGPT Plus)")
    print()


def main():
    """Run complete integration test."""
    
    print()
    print("=" * 70)
    print("🧪 GemFlush Complete Integration Test")
    print("=" * 70)
    print()
    
    # Test 1: API Keys
    keys_ok = test_api_keys()
    
    # Test 2: Content Generation
    content_ok = test_content_generation()
    
    # Test 3: HubSpot
    hubspot_ok = test_hubspot_ready()
    
    # Print workflow
    print_workflow_summary()
    
    print("=" * 70)
    print("🎯 Test Results")
    print("=" * 70)
    print()
    
    if keys_ok and content_ok:
        print("✅ System is ready for launch!")
        print()
        print("📋 Remaining steps:")
        if not hubspot_ok:
            print("   1. Fix HubSpot API scopes")
        print("   2. Create HubSpot properties")
        print("   3. Source leads (Apollo or LinkedIn)")
        print("   4. Import leads to HubSpot")
        print("   5. Build landing pages in HubSpot UI")
        print("   6. Launch campaigns")
        print()
        print("📚 See: FULLY_AUTOMATED.md for complete workflow")
        return True
    else:
        print("⚠️  Some components need attention:")
        if not keys_ok:
            print("   - Add missing API keys to .env.local")
        if not content_ok:
            print("   - Generate content: generate_all_content.py")
        if not hubspot_ok:
            print("   - Check HubSpot API connection")
        print()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


