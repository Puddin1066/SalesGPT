"""
Create HubSpot email templates from generated content.

Reads email content files and creates marketing email templates in HubSpot.
Note: HubSpot Free tier may have limited API access for email template creation.
This script will attempt to create templates, but may require manual creation via UI.
"""

import os
import sys
import requests
import json
from typing import Dict, Optional
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

load_dotenv('.env.local')


def parse_email_content(content: str) -> Dict[str, str]:
    """Parse email content file format."""
    
    lines = content.strip().split('\n')
    if len(lines) < 3:
        raise ValueError("Email content must have at least 3 lines (subject A, subject B, body)")
    
    return {
        'subject_a': lines[0].strip(),
        'subject_b': lines[1].strip(),
        'body': '\n'.join(lines[2:]).strip()
    }


def create_email_template(api_key: str, name: str, subject: str, body: str) -> Optional[str]:
    """Create a marketing email template in HubSpot."""
    
    base_url = "https://api.hubapi.com"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Note: This endpoint may require Marketing Hub (not available on Free tier)
    # If it fails, user will need to create templates manually
    url = f"{base_url}/marketing/v3/emails"
    
    payload = {
        "name": name,
        "subject": subject,
        "emailBody": body.replace('\n', '<br>'),
        "emailType": "BATCH_EMAIL"
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        data = response.json()
        template_id = data.get('id')
        print(f"   ✅ Created: {name}")
        return template_id
        
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response is not None:
            status = e.response.status_code
            
            # 403 = Permission denied (likely Free tier limitation)
            if status == 403:
                print(f"   ⚠️  {name} - API access denied (may require paid tier)")
                return None
            
            try:
                error_data = e.response.json()
                print(f"   ❌ {name} - Error: {error_data.get('message', str(e))}")
            except:
                print(f"   ❌ {name} - Error: {e}")
        else:
            print(f"   ❌ {name} - Error: {e}")
        
        return None


def create_all_templates():
    """Create email templates from email-content directory."""
    
    api_key = os.getenv('HUBSPOT_API_KEY') or os.getenv('HUBSPOT_PAT')
    if not api_key:
        print("❌ Error: HUBSPOT_API_KEY or HUBSPOT_PAT not found")
        return False
    
    email_content_dir = os.path.join(
        os.path.dirname(__file__),
        '..',
        'email-content'
    )
    
    if not os.path.exists(email_content_dir):
        print(f"❌ Error: Email content directory not found: {email_content_dir}")
        return False
    
    # Find all email content files
    email_files = [f for f in os.listdir(email_content_dir) if f.endswith('.txt')]
    
    if not email_files:
        print(f"⚠️  No email content files found in {email_content_dir}")
        print(f"💡 Generate email content first using prompts in content-prompts/email_prompts.md")
        return False
    
    print(f"🚀 Creating email templates from {len(email_files)} content files...\n")
    
    created_count = 0
    failed_count = 0
    permission_denied = False
    
    for filename in sorted(email_files):
        filepath = os.path.join(email_content_dir, filename)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            parsed = parse_email_content(content)
            
            # Create two variants (A and B)
            for variant in ['A', 'B']:
                subject = parsed[f'subject_{variant.lower()}']
                template_name = f"{filename.replace('.txt', '')}_{variant}"
                
                template_id = create_email_template(
                    api_key,
                    template_name,
                    subject,
                    parsed['body']
                )
                
                if template_id:
                    created_count += 1
                else:
                    failed_count += 1
                    if "API access denied" in str(template_id):
                        permission_denied = True
                        
        except Exception as e:
            print(f"   ❌ Error processing {filename}: {e}")
            failed_count += 1
    
    print(f"\n📊 Summary:")
    print(f"   Created: {created_count}")
    print(f"   Failed: {failed_count}")
    
    if permission_denied:
        print(f"\n⚠️  API Permission Issues Detected")
        print(f"\n💡 HubSpot Free tier may not support email template API creation.")
        print(f"   Alternative approach:")
        print(f"   1. Use email content files in {email_content_dir}")
        print(f"   2. Create templates manually in HubSpot UI:")
        print(f"      Marketing → Email → Create email")
        print(f"   3. Or send emails directly using gemflush_campaign.py")
        print(f"      (Script can embed content without templates)")
        return False
    
    if created_count > 0:
        print(f"\n✅ Email templates created!")
    
    return created_count > 0 or not permission_denied


if __name__ == "__main__":
    success = create_all_templates()
    
    if not success:
        print(f"\n📝 Note: Email templates are optional.")
        print(f"   Campaign script can send emails directly without templates.")
    
    sys.exit(0 if success else 1)

