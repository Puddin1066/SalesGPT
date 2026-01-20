"""
Deploy landing pages to HubSpot with proper API integration.

Handles:
- HubSpot CMS API integration
- Form embedding
- Tracking code setup
- A/B test configuration
"""

import os
import sys
import json
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
load_dotenv('.env.local')

try:
    import requests
except ImportError:
    print("❌ Error: requests library not found")
    print("   Install with: pip3 install requests")
    sys.exit(1)


class HubSpotDeployer:
    """Deploy landing pages to HubSpot via CMS API."""
    
    def __init__(self, access_token: str):
        """Initialize deployer with HubSpot credentials."""
        self.access_token = access_token
        self.base_url = "https://api.hubapi.com"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    def check_cms_access(self) -> bool:
        """Check if account has CMS API access."""
        try:
            url = f"{self.base_url}/cms/v3/pages/landing-pages"
            response = requests.get(url, headers=self.headers, params={"limit": 1})
            
            if response.status_code == 200:
                print("✅ CMS API access confirmed")
                return True
            elif response.status_code == 403:
                print("⚠️  CMS API requires HubSpot CMS Hub (paid tier)")
                print("   Current plan: Free or Marketing Hub")
                return False
            else:
                print(f"❌ API check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error checking CMS access: {e}")
            return False
    
    def create_hubspot_form(self, market: str) -> Optional[str]:
        """Create a HubSpot form for lead capture."""
        url = f"{self.base_url}/marketing/v3/forms"
        
        form_data = {
            "name": f"GemFlush {market.capitalize()} - Audit Request",
            "formFieldGroups": [
                {
                    "fields": [
                        {
                            "name": "firstname",
                            "label": "First Name",
                            "required": True,
                            "fieldType": "text"
                        }
                    ]
                },
                {
                    "fields": [
                        {
                            "name": "lastname",
                            "label": "Last Name",
                            "required": True,
                            "fieldType": "text"
                        }
                    ]
                },
                {
                    "fields": [
                        {
                            "name": "email",
                            "label": "Email Address",
                            "required": True,
                            "fieldType": "text"
                        }
                    ]
                },
                {
                    "fields": [
                        {
                            "name": "company",
                            "label": "Company Name",
                            "required": True,
                            "fieldType": "text"
                        }
                    ]
                },
                {
                    "fields": [
                        {
                            "name": "phone",
                            "label": "Phone Number",
                            "required": False,
                            "fieldType": "text"
                        }
                    ]
                }
            ],
            "submitText": "Get Your Free AI Audit",
            "notifyRecipients": "",
            "thankYouMessageHtml": "<p>Thank you! We'll analyze your AI visibility and send your personalized audit within 24 hours.</p>",
            "redirect": ""
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=form_data)
            
            if response.status_code in [200, 201]:
                form = response.json()
                form_id = form.get('id')
                print(f"   ✅ Form created: {form_id}")
                return form_id
            else:
                print(f"   ⚠️  Form creation failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"   ❌ Form creation error: {e}")
            return None
    
    def embed_hubspot_form(self, html: str, form_id: str, portal_id: str) -> str:
        """Embed HubSpot form into HTML."""
        
        # HubSpot form embed code
        form_embed = f"""
        <script charset="utf-8" type="text/javascript" src="//js.hsforms.net/forms/v2.js"></script>
        <script>
          hbspt.forms.create({{
            region: "na1",
            portalId: "{portal_id}",
            formId: "{form_id}"
          }});
        </script>
        """
        
        # Replace placeholder form with HubSpot form
        html = html.replace('<form id="audit-form" action="#" method="POST">', 
                          f'<div id="hubspot-form-{form_id}">')
        html = html.replace('</form>', f'</div>{form_embed}')
        
        return html
    
    def create_landing_page(self, html: str, name: str, slug: str) -> Optional[Dict]:
        """Create a landing page in HubSpot."""
        url = f"{self.base_url}/cms/v3/pages/landing-pages"
        
        page_data = {
            "name": name,
            "htmlTitle": name,
            "slug": slug,
            "state": "DRAFT",  # Start as draft for review
            "pageExpiryEnabled": False,
            "layoutSections": {
                "body": {
                    "html": html
                }
            }
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=page_data)
            
            if response.status_code in [200, 201]:
                page = response.json()
                print(f"   ✅ Page created: {page.get('url', 'N/A')}")
                return page
            else:
                print(f"   ❌ Page creation failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
        except Exception as e:
            print(f"   ❌ Page creation error: {e}")
            return None
    
    def publish_page(self, page_id: str) -> bool:
        """Publish a draft landing page."""
        url = f"{self.base_url}/cms/v3/pages/landing-pages/{page_id}/publish-action"
        
        try:
            response = requests.post(url, headers=self.headers, json={"action": "push-buffer-live"})
            
            if response.status_code == 200:
                print(f"   ✅ Page published")
                return True
            else:
                print(f"   ⚠️  Publishing failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Publishing error: {e}")
            return False


def deploy_all_pages():
    """Deploy all landing pages to HubSpot."""
    
    access_token = os.getenv('HUBSPOT_ACCESS_TOKEN')
    if not access_token:
        print("❌ Error: HUBSPOT_ACCESS_TOKEN not found in .env.local")
        print("\n💡 Alternative Deployment Options:")
        print("   1. Deploy to Netlify (instant, free):")
        print("      - Run: python3 landing-pages/deploy_netlify.py")
        print("   2. Deploy to Vercel (instant, free):")
        print("      - Run: python3 landing-pages/deploy_vercel.py")
        print("   3. Upload manually to HubSpot:")
        print("      - Marketing → Landing Pages → Upload HTML")
        return False
    
    deployer = HubSpotDeployer(access_token)
    
    print("🚀 Deploying Landing Pages to HubSpot\n")
    print("=" * 60)
    
    # Check CMS access
    print("\n1️⃣  Checking HubSpot CMS API access...")
    if not deployer.check_cms_access():
        print("\n❌ Cannot deploy via API - CMS Hub required")
        print("\n💡 Alternative: Use manual upload or Netlify/Vercel")
        return False
    
    # Get portal ID (from token or API)
    portal_id = os.getenv('HUBSPOT_PORTAL_ID', 'YOUR_PORTAL_ID')
    
    # Deploy pages
    html_dir = Path(__file__).parent / 'output' / 'html'
    markets = ['medical', 'legal', 'realestate', 'agencies']
    variants = ['a', 'b']
    
    deployed_count = 0
    
    for market in markets:
        print(f"\n2️⃣  Deploying {market.capitalize()} pages...")
        
        for variant in variants:
            html_file = html_dir / f"{market}_landing_page_{variant}.html"
            
            if not html_file.exists():
                print(f"   ⚠️  Variant {variant.upper()}: HTML not found")
                continue
            
            print(f"   Variant {variant.upper()}:", end=" ")
            
            try:
                # Read HTML
                with open(html_file, 'r', encoding='utf-8') as f:
                    html = f.read()
                
                # Create and embed form
                # form_id = deployer.create_hubspot_form(market)
                # if form_id:
                #     html = deployer.embed_hubspot_form(html, form_id, portal_id)
                
                # Create page
                page_name = f"GemFlush - {market.capitalize()} - Variant {variant.upper()}"
                slug = f"gemflush-{market}-{variant}"
                
                page = deployer.create_landing_page(html, page_name, slug)
                
                if page:
                    deployed_count += 1
                    
                    # Optionally publish immediately
                    # deployer.publish_page(page['id'])
                
            except Exception as e:
                print(f"❌ Error: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print(f"\n📊 Deployment Summary:")
    print(f"   • Pages deployed: {deployed_count}/8")
    
    if deployed_count > 0:
        print(f"\n✅ Landing pages created in HubSpot!")
        print(f"\n💡 Next Steps:")
        print(f"   1. Review pages in HubSpot → Marketing → Landing Pages")
        print(f"   2. Add HubSpot forms to pages")
        print(f"   3. Publish pages when ready")
        print(f"   4. Update email campaigns with page URLs")
        return True
    else:
        print(f"\n❌ No pages deployed")
        return False


if __name__ == "__main__":
    success = deploy_all_pages()
    sys.exit(0 if success else 1)


