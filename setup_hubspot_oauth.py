#!/usr/bin/env python3
"""
HubSpot OAuth Setup Helper

Helps set up OAuth 2.0 authentication for HubSpot API.
Follows: https://developers.hubspot.com/docs/api-reference/auth-oauth-v1/guide
"""
import os
import sys
from dotenv import load_dotenv
from services.crm.hubspot_agent import HubSpotAgent

load_dotenv()

def setup_oauth():
    """Interactive OAuth setup for HubSpot."""
    print("="*60)
    print("HubSpot OAuth 2.0 Setup")
    print("="*60)
    print("\nThis script helps you set up OAuth authentication.")
    print("You'll need:")
    print("  1. A HubSpot app (create at: https://developers.hubspot.com/apps)")
    print("  2. Client ID and Client Secret from your app's Auth settings")
    print("  3. An authorization code from the OAuth flow")
    print()
    
    # Get credentials
    client_id = input("Enter your Client ID: ").strip()
    if not client_id:
        print("❌ Client ID is required")
        return False
    
    client_secret = input("Enter your Client Secret: ").strip()
    if not client_secret:
        print("❌ Client Secret is required")
        return False
    
    redirect_uri = input("Enter your Redirect URI (from app settings): ").strip()
    if not redirect_uri:
        print("❌ Redirect URI is required")
        return False
    
    print("\n" + "="*60)
    print("Step 1: Get Authorization Code")
    print("="*60)
    print("\n1. Build your authorization URL:")
    print(f"   https://app.hubspot.com/oauth/authorize?")
    print(f"   client_id={client_id}&")
    print(f"   scope=crm.objects.contacts.read%20crm.objects.contacts.write%20crm.objects.deals.read%20crm.objects.deals.write&")
    print(f"   redirect_uri={redirect_uri}")
    print("\n2. Open this URL in your browser")
    print("3. Authorize the app in your HubSpot account")
    print("4. You'll be redirected to your redirect_uri with a 'code' parameter")
    print("5. Copy the 'code' value from the URL")
    print()
    
    auth_code = input("Enter the authorization code from the redirect URL: ").strip()
    if not auth_code:
        print("❌ Authorization code is required")
        return False
    
    print("\n" + "="*60)
    print("Step 2: Generate Initial Tokens")
    print("="*60)
    print("\nGenerating access and refresh tokens...")
    
    tokens = HubSpotAgent.generate_initial_tokens(
        client_id=client_id,
        client_secret=client_secret,
        authorization_code=auth_code,
        redirect_uri=redirect_uri
    )
    
    if not tokens:
        print("❌ Failed to generate tokens. Check your credentials and try again.")
        return False
    
    print("✅ Tokens generated successfully!")
    print(f"\nAccess Token: {tokens.get('access_token', '')[:50]}...")
    print(f"Refresh Token: {tokens.get('refresh_token', '')[:50]}...")
    print(f"Expires in: {tokens.get('expires_in', 'N/A')} seconds")
    
    print("\n" + "="*60)
    print("Step 3: Update .env File")
    print("="*60)
    print("\nAdd these to your .env file:")
    print(f"HUBSPOT_CLIENT_ID={client_id}")
    print(f"HUBSPOT_CLIENT_SECRET={client_secret}")
    print(f"HUBSPOT_REFRESH_TOKEN={tokens.get('refresh_token', '')}")
    print("\nThe access token will be automatically refreshed when needed.")
    
    # Optionally write to .env
    write_env = input("\nWrite to .env file? (y/n): ").strip().lower()
    if write_env == 'y':
        env_path = '.env'
        try:
            # Read existing .env
            env_content = ""
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    env_content = f.read()
            
            # Remove old HubSpot OAuth vars if they exist
            lines = env_content.split('\n')
            filtered_lines = [
                line for line in lines
                if not line.startswith('HUBSPOT_CLIENT_ID=')
                and not line.startswith('HUBSPOT_CLIENT_SECRET=')
                and not line.startswith('HUBSPOT_REFRESH_TOKEN=')
            ]
            
            # Add new vars
            filtered_lines.append(f"HUBSPOT_CLIENT_ID={client_id}")
            filtered_lines.append(f"HUBSPOT_CLIENT_SECRET={client_secret}")
            filtered_lines.append(f"HUBSPOT_REFRESH_TOKEN={tokens.get('refresh_token', '')}")
            
            with open(env_path, 'w') as f:
                f.write('\n'.join(filtered_lines))
            
            print(f"✅ Updated {env_path}")
        except Exception as e:
            print(f"❌ Failed to write to .env: {e}")
            print("Please add the variables manually.")
    
    print("\n" + "="*60)
    print("Setup Complete!")
    print("="*60)
    print("\nYou can now test the connection with:")
    print("  python3 test_hubspot_connection.py")
    
    return True

if __name__ == "__main__":
    success = setup_oauth()
    sys.exit(0 if success else 1)



