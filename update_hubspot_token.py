#!/usr/bin/env python3
"""
Update HubSpot API key in .env file.

Usage:
    python3 update_hubspot_token.py YOUR_NEW_TOKEN
    # or
    python3 update_hubspot_token.py  # will prompt for token
"""
import os
import sys
import re
from pathlib import Path

def update_env_file(token: str):
    """Update HUBSPOT_API_KEY in .env file."""
    env_path = Path('.env')
    
    if not env_path.exists():
        print("❌ .env file not found. Creating new file...")
        with open(env_path, 'w') as f:
            f.write(f"HUBSPOT_API_KEY={token}\n")
        print(f"✅ Created .env file with new token")
        return True
    
    # Read existing .env
    with open(env_path, 'r') as f:
        content = f.read()
    
    # Check if HUBSPOT_API_KEY already exists
    pattern = r'^HUBSPOT_API_KEY=.*$'
    
    if re.search(pattern, content, re.MULTILINE):
        # Replace existing key
        new_content = re.sub(
            pattern,
            f'HUBSPOT_API_KEY={token}',
            content,
            flags=re.MULTILINE
        )
        print("✅ Updated existing HUBSPOT_API_KEY in .env")
    else:
        # Add new key
        if content and not content.endswith('\n'):
            content += '\n'
        content += f'HUBSPOT_API_KEY={token}\n'
        new_content = content
        print("✅ Added HUBSPOT_API_KEY to .env")
    
    # Write back
    with open(env_path, 'w') as f:
        f.write(new_content)
    
    return True

def main():
    if len(sys.argv) > 1:
        token = sys.argv[1].strip()
    else:
        print("Enter your new HubSpot Personal Access Key:")
        print("(You can get it from: https://app.hubspot.com/settings/integrations/private-apps)")
        print()
        token = input("Token: ").strip()
    
    if not token:
        print("❌ Token cannot be empty")
        sys.exit(1)
    
    if len(token) < 50:
        print(f"⚠️  Warning: Token seems short ({len(token)} chars). HubSpot tokens are usually 100+ characters.")
        confirm = input("Continue anyway? (y/n): ").strip().lower()
        if confirm != 'y':
            sys.exit(1)
    
    if update_env_file(token):
        print(f"\n✅ Token updated successfully!")
        print(f"   Token length: {len(token)} characters")
        print(f"   First 15 chars: {token[:15]}...")
        print(f"\n🔍 Verifying token...")
        print()
        
        # Run verification
        import subprocess
        result = subprocess.run(
            ['python3', 'verify_hubspot_token.py'],
            capture_output=False
        )
        sys.exit(result.returncode)

if __name__ == "__main__":
    main()

