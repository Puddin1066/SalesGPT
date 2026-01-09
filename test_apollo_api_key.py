"""
Test Apollo API Key - Verifies API key from .env.local or .env

Tests both endpoints:
1. /mixed_people/search (current implementation)
2. /mixed_people/api_search (new API-optimized endpoint - no credits, no emails/phones)
"""
import os
import json
import requests
from dotenv import load_dotenv

def test_apollo_api_key():
    """Test Apollo API key from environment variables."""
    print("="*60)
    print("APOLLO API KEY TEST")
    print("="*60)
    
    # Load environment variables - priority: .env.local then .env
    if os.path.exists(".env.local"):
        print("📁 Loading environment from .env.local")
        load_dotenv(".env.local", override=True)
    else:
        print("📁 Loading environment from .env")
        load_dotenv()
    
    api_key = os.getenv("APOLLO_API_KEY")
    
    if not api_key:
        print("❌ ERROR: APOLLO_API_KEY not found in environment variables")
        print("   Please set APOLLO_API_KEY in .env.local or .env")
        return False
    
    # Mask API key for display
    masked_key = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else f"{api_key[:4]}***"
    print(f"🔑 API Key found: {masked_key}")
    print()
    
    base_url = "https://api.apollo.io/v1"
    headers = {
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
        "X-Api-Key": api_key,  # Apollo requires API key in header
    }
    
    # Test 1: Current endpoint (/mixed_people/search)
    print("="*60)
    print("TEST 1: /mixed_people/search (Current Implementation)")
    print("="*60)
    
    search_params = {
        # Note: api_key removed from body - now in X-Api-Key header
        "q_keywords": "Dermatology",
        "person_locations": ["New York, NY"],
        "organization_num_employees_ranges": ["1,50"],
        "person_titles": ["Owner", "CEO", "Medical Director"],
        "page": 1,
        "per_page": 2,
    }
    
    try:
        print("📡 Making API request to /mixed_people/search...")
        response = requests.post(
            f"{base_url}/mixed_people/search",
            json=search_params,
            headers=headers,
            timeout=10
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            people = data.get("people", [])
            print(f"✅ SUCCESS! API key is valid")
            print(f"   Found {len(people)} people in results")
            
            if people:
                person = people[0]
                print(f"\n   Sample result:")
                print(f"   - Name: {person.get('first_name', '')} {person.get('last_name', '')}")
                print(f"   - Title: {person.get('title', 'N/A')}")
                print(f"   - Company: {person.get('organization', {}).get('name', 'N/A')}")
                print(f"   - Email: {person.get('email', 'N/A')}")
            
            return True
            
        elif response.status_code == 401:
            print("❌ ERROR: 401 Unauthorized")
            print("   Your API key is invalid or expired")
            print(f"   Response: {response.text}")
            return False
            
        elif response.status_code == 402:
            print("⚠️  WARNING: 402 Payment Required")
            print("   Your API key is valid but you may have insufficient credits")
            print(f"   Response: {response.text}")
            return True  # Key is valid, just no credits
            
        elif response.status_code == 403:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get("error", response.text)
            print("⚠️  WARNING: 403 Forbidden")
            print("   Your API key is VALID, but your plan doesn't have access to this endpoint")
            print(f"   Error: {error_msg}")
            if "free plan" in error_msg.lower():
                print("   💡 Suggestion: Upgrade your Apollo plan to access this endpoint")
                print("   Visit: https://app.apollo.io/ to upgrade")
            return True  # Key is valid, just plan limitation
            
        elif response.status_code == 429:
            print("⚠️  WARNING: 429 Rate Limit Exceeded")
            print("   Your API key is valid but rate limit was exceeded")
            print("   Wait a few minutes and try again")
            return True  # Key is valid
            
        else:
            print(f"❌ ERROR: Unexpected status code {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Request failed - {str(e)}")
        return False
    
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False


def test_apollo_api_search_endpoint():
    """Test the new API-optimized search endpoint (no credits, no emails/phones)."""
    print("\n" + "="*60)
    print("TEST 2: /mixed_people/api_search (API-Optimized Endpoint)")
    print("="*60)
    print("Note: This endpoint doesn't consume credits but also doesn't")
    print("      return email addresses or phone numbers.")
    print()
    
    api_key = os.getenv("APOLLO_API_KEY")
    if not api_key:
        print("❌ API key not found")
        return False
    
    base_url = "https://api.apollo.io/api/v1"
    headers = {
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
        "X-Api-Key": api_key,  # Apollo requires API key in header
    }
    
    # According to docs: https://docs.apollo.io/reference/people-api-search
    # This endpoint requires a master API key
    search_params = {
        # Note: api_key removed from body - now in X-Api-Key header
        "q_keywords": "Dermatology",
        "person_locations": ["New York, NY"],
        "organization_num_employees_ranges": ["1,50"],
        "person_titles": ["Owner", "CEO", "Medical Director"],
        "page": 1,
        "per_page": 2,
    }
    
    try:
        print("📡 Making API request to /mixed_people/api_search...")
        response = requests.post(
            f"{base_url}/mixed_people/api_search",
            json=search_params,
            headers=headers,
            timeout=10
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            people = data.get("people", [])
            print(f"✅ SUCCESS! API key is valid for API search endpoint")
            print(f"   Found {len(people)} people in results")
            
            if people:
                person = people[0]
                print(f"\n   Sample result:")
                print(f"   - Name: {person.get('first_name', '')} {person.get('last_name', '')}")
                print(f"   - Title: {person.get('title', 'N/A')}")
                print(f"   - Company: {person.get('organization', {}).get('name', 'N/A')}")
                print(f"   - Email: {person.get('email', 'Not returned by this endpoint')}")
                print(f"   - Phone: {person.get('phone_numbers', 'Not returned by this endpoint')}")
            
            return True
            
        elif response.status_code == 401:
            print("❌ ERROR: 401 Unauthorized")
            print("   This endpoint requires a Master API key")
            print("   Your current key may not have master permissions")
            print(f"   Response: {response.text}")
            return False
            
        else:
            print(f"⚠️  Status Code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Request failed - {str(e)}")
        return False
    
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False


if __name__ == "__main__":
    print("\n")
    
    # Test 1: Current endpoint
    test1_result = test_apollo_api_key()
    
    # Test 2: New API search endpoint
    test2_result = test_apollo_api_search_endpoint()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    if test1_result:
        print("✅ Current endpoint (/mixed_people/search): API key is VALID")
    else:
        print("❌ Current endpoint (/mixed_people/search): API key is INVALID")
    
    if test2_result:
        print("✅ API search endpoint (/mixed_people/api_search): API key is VALID")
    else:
        print("⚠️  API search endpoint (/mixed_people/api_search): Not tested or requires Master API key")
    
    print("\n" + "="*60)
    
    if test1_result:
        print("✅ Your Apollo API key is VALID and working!")
        if test1_result and not test2_result:
            print("   ⚠️  Note: Your plan may not have access to all endpoints.")
            print("   Consider upgrading if you need full API access.")
        else:
            print("   You can use it with the current implementation.")
    else:
        print("❌ Your Apollo API key needs to be fixed.")
        print("   Check your .env.local file and verify the key is correct.")
    print("="*60 + "\n")

