"""
Test Smartlead API Key and Authentication

Diagnoses API key issues and provides setup guidance.
"""
import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

def test_smartlead_api_key():
    """Test Smartlead API key authentication."""
    print("="*60)
    print("🔑 Testing Smartlead API Key")
    print("="*60)
    
    api_key = os.getenv("SMARTLEAD_API_KEY")
    if not api_key:
        print("\n❌ Error: SMARTLEAD_API_KEY not found in .env file")
        print("\nTo get your API key:")
        print("  1. Go to https://app.smartlead.ai")
        print("  2. Log in to your account")
        print("  3. Navigate to Settings → API")
        print("  4. Copy your API key")
        print("  5. Add to .env: SMARTLEAD_API_KEY=your_key_here")
        return False
    
    print(f"\n✅ API Key Found: {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else '***'}")
    
    # Test different endpoints
    base_url = "https://server.smartlead.ai/api/v1"
    
    # Try different authentication methods
    auth_methods = [
        {"api-key": api_key, "Content-Type": "application/json"},  # Current method
        {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},  # Bearer token
        {"Authorization": api_key, "Content-Type": "application/json"},  # Direct auth
        {"X-API-Key": api_key, "Content-Type": "application/json"},  # X-API-Key header
    ]
    
    # Also try query parameter method
    query_param_url = f"{base_url}/mailboxes?api_key={api_key}"
    
    headers = auth_methods[0]  # Start with current method
    
    # Test 1: Get mailboxes with different auth methods
    print("\n📬 Testing Mailboxes Endpoint...")
    
    # First try query parameter method
    print("\n   Trying method: Query parameter (api_key=...)")
    try:
        response = requests.get(
            query_param_url,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"      Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            mailboxes = data.get("mailboxes", [])
            print(f"      ✅ SUCCESS with query parameter method!")
            print(f"      Found {len(mailboxes)} mailboxes")
            if mailboxes:
                print("\n      Mailboxes:")
                for mb in mailboxes[:5]:
                    print(f"        - ID: {mb.get('id')}, Email: {mb.get('email')}, Status: {mb.get('status')}")
            print(f"\n   ✅ Correct authentication method: Query parameter")
            return True
        elif response.status_code == 401:
            try:
                error_data = response.json()
                print(f"      ❌ 401: {error_data.get('message', 'Unauthorized')}")
            except:
                print(f"      ❌ 401: Unauthorized")
    except requests.exceptions.RequestException as e:
        print(f"      ❌ Request failed: {e}")
    
    # Then try header methods
    for i, test_headers in enumerate(auth_methods, 1):
        method_name = list(test_headers.keys())[0] if test_headers else "unknown"
        print(f"\n   Trying method {i+1}: {method_name} header")
        
        try:
            response = requests.get(
                f"{base_url}/mailboxes",
                headers=test_headers,
                timeout=10
            )
        
            print(f"      Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                mailboxes = data.get("mailboxes", [])
                print(f"      ✅ SUCCESS with {method_name} header!")
                print(f"      Found {len(mailboxes)} mailboxes")
                if mailboxes:
                    print("\n      Mailboxes:")
                    for mb in mailboxes[:5]:
                        print(f"        - ID: {mb.get('id')}, Email: {mb.get('email')}, Status: {mb.get('status')}")
                print(f"\n   ✅ Correct authentication method: {method_name}")
                return True
            elif response.status_code == 401:
                try:
                    error_data = response.json()
                    print(f"      ❌ 401: {error_data.get('message', 'Unauthorized')}")
                except:
                    print(f"      ❌ 401: Unauthorized")
            elif response.status_code == 403:
                print(f"      ❌ 403: Forbidden")
            else:
                print(f"      ⚠️  Status {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"      ❌ Request failed: {e}")
            continue
    
    # If we get here, all methods failed
    print("\n   ❌ All authentication methods failed")
    print("\n   Possible issues:")
    print("     1. API key is incorrect or expired")
    print("     2. API key format is wrong")
    print("     3. Account doesn't have API access enabled")
    print("     4. Smartlead API endpoint or authentication method has changed")
    print("\n   Solution:")
    print("     1. Verify API key in Smartlead dashboard: https://app.smartlead.ai/settings/api")
    print("     2. Regenerate API key if needed")
    print("     3. Check your Smartlead plan includes API access")
    print("     4. Check Smartlead API documentation for current authentication method")
    return False
    
    # Test 2: Try account info endpoint (if available)
    print("\n📊 Testing Account Info...")
    try:
        response = requests.get(
            f"{base_url}/account",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            print("   ✅ Account endpoint accessible")
            data = response.json()
            print(f"   Account data: {data}")
        else:
            print(f"   ⚠️  Account endpoint returned {response.status_code} (may not exist)")
    except:
        print("   ⚠️  Account endpoint not available (this is normal)")

if __name__ == "__main__":
    success = test_smartlead_api_key()
    
    if success:
        print("\n" + "="*60)
        print("✅ API Key is Valid!")
        print("="*60)
        print("\nNext steps:")
        print("  1. Run: python3 setup_smartlead_account.py")
        print("  2. If no mailboxes found, add them in Smartlead dashboard")
        print("  3. Then run setup script again to create campaign")
    else:
        print("\n" + "="*60)
        print("❌ API Key Test Failed")
        print("="*60)
        print("\nPlease fix the issues above before proceeding.")

