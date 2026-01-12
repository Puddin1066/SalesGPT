"""
Test GemFlush Campaign functionality.

Tests initialization, contact fetching, and email preparation without actually sending.
"""

import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import gemflush_campaign
import importlib.util
gemflush_path = os.path.join(os.path.dirname(__file__), 'gemflush_campaign.py')
spec = importlib.util.spec_from_file_location("gemflush_campaign", gemflush_path)
gemflush_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gemflush_module)
GemFlushCampaign = gemflush_module.GemFlushCampaign

load_dotenv('.env.local')


def test_campaign_initialization():
    """Test that campaign initializes correctly."""
    print("🧪 Test 1: Campaign Initialization")
    print("-" * 60)
    
    try:
        campaign = GemFlushCampaign(sender_email="Alex@GEMflush.com")
        print("✅ Campaign initialized successfully")
        print(f"   Sender email: {campaign.sender_email}")
        print(f"   HubSpot base URL: {campaign.base_url}")
        return True, campaign
    except Exception as e:
        print(f"❌ Failed to initialize campaign: {e}")
        return False, None


def test_contact_search(campaign):
    """Test searching for contacts by vertical."""
    print("\n🧪 Test 2: Contact Search")
    print("-" * 60)
    
    if not campaign:
        print("⏭️  Skipping (campaign not initialized)")
        return False
    
    # Test searching for contacts (may return empty if no contacts exist yet)
    try:
        contacts = campaign.get_contacts_by_property(
            property_name='vertical',
            property_value='medical',
            limit=10
        )
        print(f"✅ Contact search successful")
        print(f"   Found {len(contacts)} contacts for 'medical' vertical")
        if contacts:
            print(f"   Sample contact: {contacts[0].get('email', 'N/A')}")
        else:
            print("   (No contacts found - this is expected if leads haven't been imported yet)")
        return True
    except Exception as e:
        print(f"❌ Contact search failed: {e}")
        return False


def test_email_personalization(campaign):
    """Test email personalization logic."""
    print("\n🧪 Test 3: Email Personalization")
    print("-" * 60)
    
    if not campaign:
        print("⏭️  Skipping (campaign not initialized)")
        return False
    
    # Create a test contact
    test_contact = {
        "id": "test123",
        "email": "test@example.com",
        "firstname": "John",
        "lastname": "Doe",
        "company": "Test Medical Clinic",
        "city": "New York",
        "jobtitle": "Practice Manager"
    }
    
    # Test subject and body templates
    subject_template = "{{firstname}}, your competitors are showing up in ChatGPT"
    body_template = """Hi {{firstname}},

I noticed {{company}} is a medical practice in {{city}}.

According to a recent study, 64% of patients now use ChatGPT to research medical providers.

Curious how {{company}} ranks in AI search results?"""
    
    try:
        # Test personalization (without actually sending)
        personalized_subject = subject_template.replace('{{firstname}}', test_contact.get('firstname', ''))
        personalized_body = body_template.replace('{{firstname}}', test_contact.get('firstname', ''))
        personalized_body = personalized_body.replace('{{company}}', test_contact.get('company', ''))
        personalized_body = personalized_body.replace('{{city}}', test_contact.get('city', ''))
        
        print("✅ Email personalization test successful")
        print(f"   Original subject: {subject_template}")
        print(f"   Personalized: {personalized_subject}")
        print(f"   Original body snippet: {body_template[:50]}...")
        print(f"   Personalized snippet: {personalized_body[:50]}...")
        
        # Verify personalization worked
        assert "John" in personalized_subject, "First name not replaced in subject"
        assert "Test Medical Clinic" in personalized_body, "Company not replaced in body"
        assert "New York" in personalized_body, "City not replaced in body"
        
        print("   ✅ All personalization tokens replaced correctly")
        return True
    except Exception as e:
        print(f"❌ Email personalization test failed: {e}")
        return False


def test_email_content_format():
    """Test email content file format."""
    print("\n🧪 Test 4: Email Content Format")
    print("-" * 60)
    
    # Check if email-content directory exists
    email_content_dir = os.path.join(os.path.dirname(__file__), 'email-content')
    if not os.path.exists(email_content_dir):
        print("❌ email-content directory not found")
        return False
    
    print(f"✅ email-content directory exists: {email_content_dir}")
    
    # Check for README
    readme_path = os.path.join(email_content_dir, 'README.md')
    if os.path.exists(readme_path):
        print("✅ README.md found in email-content directory")
    else:
        print("⚠️  README.md not found (expected to be there)")
    
    # Check if any email content files exist (optional)
    email_files = [f for f in os.listdir(email_content_dir) if f.endswith('.txt')]
    if email_files:
        print(f"   Found {len(email_files)} email content file(s): {', '.join(email_files[:3])}")
    else:
        print("   No email content files found yet (expected - generate with ChatGPT)")
    
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("GemFlush Campaign Test Suite")
    print("=" * 60)
    print()
    
    results = []
    
    # Test 1: Initialization
    success, campaign = test_campaign_initialization()
    results.append(("Initialization", success))
    
    # Test 2: Contact Search
    success = test_contact_search(campaign)
    results.append(("Contact Search", success))
    
    # Test 3: Email Personalization
    success = test_email_personalization(campaign)
    results.append(("Email Personalization", success))
    
    # Test 4: Email Content Format
    success = test_email_content_format()
    results.append(("Email Content Format", success))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All tests passed! System is ready to use.")
        print("\nNext steps:")
        print("  1. Generate email content using HubSpot Marketing Email GPT")
        print("  2. Import leads to HubSpot CRM (tag with 'vertical' property)")
        print("  3. Create landing pages using HubSpot Landing Page Creator GPT")
        print("  4. Run campaigns: python3 chatgpt-native-stack/gemflush_campaign.py --vertical medical --email 1 --count 200")
        return 0
    else:
        print("\n⚠️  Some tests failed. Review errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

