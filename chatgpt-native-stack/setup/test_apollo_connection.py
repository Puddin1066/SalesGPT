"""
Test Apollo.io API connection and lead enrichment.

Verifies Apollo API key and tests basic enrichment functionality.
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

load_dotenv('.env.local')


def test_apollo_connection():
    """Test Apollo.io API connection."""
    
    api_key = os.getenv('APOLLO_API_KEY')
    if not api_key:
        print("❌ Error: APOLLO_API_KEY not found in .env.local")
        return False
    
    print("🚀 Testing Apollo.io API connection...\n")
    
    # Test 1: Verify API key
    print("1️⃣  Testing API Key Authentication...")
    
    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "X-Api-Key": api_key
    }
    
    # Use Apollo's people search endpoint with minimal query
    url = "https://api.apollo.io/v1/mixed_people/search"
    
    payload = {
        "q_keywords": "practice manager medical",
        "page": 1,
        "per_page": 1  # Just get 1 result to test
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            print("   ✅ API key valid")
            data = response.json()
            
            # Check credits
            if 'pagination' in data:
                print(f"   ℹ️  Available credits: Check your Apollo dashboard")
            
            return True
            
        elif response.status_code == 401:
            print("   ❌ API key invalid or expired")
            return False
            
        elif response.status_code == 403:
            print("   ❌ API key lacks required permissions")
            return False
            
        else:
            print(f"   ⚠️  Unexpected response: {response.status_code}")
            print(f"      {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_apollo_search():
    """Test Apollo.io lead search functionality."""
    
    api_key = os.getenv('APOLLO_API_KEY')
    if not api_key:
        return False
    
    print("\n2️⃣  Testing Lead Search...")
    
    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "X-Api-Key": api_key
    }
    
    url = "https://api.apollo.io/v1/mixed_people/search"
    
    # Search for medical practice managers in New York
    payload = {
        "q_organization_industry_tag_ids": ["5567cd4773696439b10b0000"],  # Healthcare
        "person_titles": ["Practice Manager", "Office Manager"],
        "person_locations": ["New York, United States"],
        "page": 1,
        "per_page": 5
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        data = response.json()
        people = data.get('people', [])
        
        print(f"   ✅ Search successful")
        print(f"   📊 Found: {len(people)} sample results")
        
        if people:
            print(f"\n   Sample lead:")
            person = people[0]
            print(f"      Name: {person.get('first_name', 'N/A')} {person.get('last_name', 'N/A')}")
            print(f"      Title: {person.get('title', 'N/A')}")
            print(f"      Company: {person.get('organization_name', 'N/A')}")
            print(f"      Email: {'✅ Available' if person.get('email') else '❌ Not available'}")
            print(f"      City: {person.get('city', 'N/A')}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Search failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                print(f"      Details: {json.dumps(error_data, indent=6)}")
            except:
                print(f"      Response: {e.response.text[:200]}")
        return False


def test_apollo_enrichment():
    """Test Apollo.io contact enrichment."""
    
    api_key = os.getenv('APOLLO_API_KEY')
    if not api_key:
        return False
    
    print("\n3️⃣  Testing Contact Enrichment...")
    
    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "X-Api-Key": api_key
    }
    
    url = "https://api.apollo.io/v1/people/match"
    
    # Try to enrich a generic contact
    payload = {
        "first_name": "John",
        "last_name": "Smith",
        "organization_name": "Example Medical Clinic",
        "domain": "example.com"
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            person = data.get('person', {})
            
            if person:
                print(f"   ✅ Enrichment working")
                print(f"   ℹ️  Can enrich contacts with additional data")
            else:
                print(f"   ℹ️  Enrichment available (no match for test data)")
            
            return True
        else:
            print(f"   ⚠️  Enrichment test: {response.status_code}")
            print(f"      Note: This is optional functionality")
            return True  # Don't fail on enrichment test
            
    except Exception as e:
        print(f"   ⚠️  Enrichment test error: {e}")
        print(f"      Note: Enrichment is optional")
        return True  # Don't fail on optional feature


def check_apollo_credits():
    """Check Apollo.io credit usage."""
    
    api_key = os.getenv('APOLLO_API_KEY')
    if not api_key:
        return False
    
    print("\n4️⃣  Checking Account Credits...")
    
    print("   ℹ️  Credit information:")
    print("      - Apollo.io credits are consumed on searches and exports")
    print("      - Check your dashboard: https://app.apollo.io")
    print("      - Free tier: Limited credits per month")
    print("      - Paid plans: More credits available")
    
    return True


def main():
    """Run all Apollo.io tests."""
    
    print("=" * 70)
    print("🔍 Apollo.io API Testing")
    print("=" * 70)
    print()
    
    # Check if API key exists
    api_key = os.getenv('APOLLO_API_KEY')
    if not api_key:
        print("❌ APOLLO_API_KEY not found in .env.local")
        print()
        print("💡 To use Apollo.io:")
        print("   1. Sign up at https://app.apollo.io")
        print("   2. Get your API key from Settings → Integrations")
        print("   3. Add to .env.local: APOLLO_API_KEY=your_key")
        print()
        print("⚠️  Note: Apollo.io is optional for lead sourcing")
        print("   Alternatives:")
        print("   - LinkedIn Sales Navigator (free trial)")
        print("   - Manual lead research")
        print("   - Buy lead lists from ZoomInfo, UpLead, etc.")
        return False
    
    results = []
    
    # Test 1: Connection
    results.append(test_apollo_connection())
    
    if results[0]:
        # Test 2: Search
        results.append(test_apollo_search())
        
        # Test 3: Enrichment (optional)
        results.append(test_apollo_enrichment())
        
        # Test 4: Credits info
        results.append(check_apollo_credits())
    
    print()
    print("=" * 70)
    print("📊 Apollo.io Test Summary")
    print("=" * 70)
    print()
    
    if all(results[:2]):  # Only require connection and search
        print("✅ Apollo.io API is working!")
        print()
        print("💡 Next steps:")
        print("   1. Use Apollo to search for leads by vertical")
        print("   2. Export leads to CSV")
        print("   3. Import to HubSpot: import_contacts_bulk.py")
        print()
        print("📚 See: REALISTIC_WORKFLOW.md for lead sourcing guide")
        return True
    else:
        print("⚠️  Apollo.io API has issues")
        print()
        print("💡 Troubleshooting:")
        print("   - Verify API key is correct")
        print("   - Check account status and credits")
        print("   - Try regenerating API key in Apollo dashboard")
        print()
        print("📚 Alternative: Use LinkedIn Sales Navigator for leads")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


