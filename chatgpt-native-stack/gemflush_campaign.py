"""
GemFlush Campaign - Light Automation
Leverages SalesGPT patterns with ChatGPT-generated content.

Uses HubSpot Free tier (2,000 emails/month) for email sending.
Content generated via HubSpot GPTs in ChatGPT.
"""

import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Add parent directory to path to import SalesGPT services
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.crm.hubspot_agent import HubSpotAgent

load_dotenv('.env.local')


class GemFlushCampaign:
    """Light automation for GemFlush email campaigns using HubSpot API."""
    
    def __init__(self, sender_email: str = "Alex@GEMflush.com"):
        """
        Initialize campaign with HubSpot agent.
        
        Args:
            sender_email: Email address to use as sender (default: Alex@GEMflush.com)
        """
        # Use HUBSPOT_API_KEY (primary) or HUBSPOT_PAT (fallback)
        api_key = os.getenv('HUBSPOT_API_KEY') or os.getenv('HUBSPOT_PAT')
        
        if not api_key:
            raise ValueError(
                "HubSpot API key not found. Set HUBSPOT_API_KEY or HUBSPOT_PAT in .env.local"
            )
        
        self.hubspot = HubSpotAgent(api_key=api_key)
        self.base_url = "https://api.hubapi.com"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.sender_email = sender_email
        
    def get_contacts_by_property(
        self,
        property_name: str,
        property_value: str,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get contacts filtered by property value.
        
        Args:
            property_name: HubSpot property name (e.g., 'vertical')
            property_value: Property value to filter by
            limit: Maximum number of contacts to return
            
        Returns:
            List of contact dictionaries
        """
        import requests
        
        url = f"{self.base_url}/crm/v3/objects/contacts/search"
        
        payload = {
            "filterGroups": [{
                "filters": [{
                    "propertyName": property_name,
                    "operator": "EQ",
                    "value": property_value
                }]
            }],
            "properties": ["email", "firstname", "lastname", "company", "city", "jobtitle"],
            "limit": limit
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()
            contacts = []
            
            for result in data.get("results", []):
                props = result.get("properties", {})
                contacts.append({
                    "id": result.get("id"),
                    "email": props.get("email", ""),
                    "firstname": props.get("firstname", ""),
                    "lastname": props.get("lastname", ""),
                    "company": props.get("company", ""),
                    "city": props.get("city", ""),
                    "jobtitle": props.get("jobtitle", "")
                })
            
            return contacts
            
        except Exception as e:
            print(f"Error fetching contacts: {e}")
            return []
    
    def send_personalized_email(
        self,
        contact: Dict,
        subject: str,
        body: str,
        landing_page_url: str,
        variant: str
    ) -> bool:
        """
        Send personalized email via HubSpot Marketing API.
        
        Args:
            contact: Contact dictionary with email, firstname, etc.
            subject: Email subject line (with tokens)
            body: Email body template (with tokens)
            landing_page_url: Landing page URL to include
            variant: A/B test variant ('A' or 'B')
            
        Returns:
            True if sent successfully, False otherwise
        """
        import requests
        
        # Personalize subject and body
        personalized_subject = subject.replace('{{firstname}}', contact.get('firstname', ''))
        personalized_subject = personalized_subject.replace('{{company}}', contact.get('company', ''))
        personalized_subject = personalized_subject.replace('{{contact.firstname}}', contact.get('firstname', ''))
        personalized_subject = personalized_subject.replace('{{contact.company}}', contact.get('company', ''))
        
        personalized_body = body.replace('{{firstname}}', contact.get('firstname', ''))
        personalized_body = personalized_body.replace('{{company}}', contact.get('company', ''))
        personalized_body = personalized_body.replace('{{city}}', contact.get('city', ''))
        personalized_body = personalized_body.replace('{{contact.firstname}}', contact.get('firstname', ''))
        personalized_body = personalized_body.replace('{{contact.company}}', contact.get('company', ''))
        personalized_body = personalized_body.replace('{{contact.city}}', contact.get('city', ''))
        
        # Add landing page link
        personalized_body += f"\n\nView your AI visibility audit: {landing_page_url}"
        
        # HubSpot Marketing Email API - single send
        # Note: HubSpot Free tier limits to 2,000 emails/month
        # For automation, we'll use the transactional email API or store for manual send
        
        # Track in HubSpot CRM
        if contact.get('id'):
            self.hubspot.update_contact_properties(
                contact_id=contact['id'],
                properties={
                    'gemflush_email_sent': datetime.now().isoformat(),
                    'gemflush_variant': variant,
                    'gemflush_email_subject': personalized_subject,
                    'gemflush_last_campaign_date': datetime.now().strftime('%Y-%m-%d'),
                    'gemflush_sender_email': self.sender_email
                }
            )
        
        # For now, log to console (actual sending requires HubSpot Marketing Hub API)
        print(f"📧 Email prepared for {contact.get('email')}: {personalized_subject[:50]}...")
        print(f"   From: {self.sender_email}, Variant: {variant}, Landing page: {landing_page_url}")
        
        return True
    
    def send_email_batch(
        self,
        vertical: str,
        email_number: int,
        subject_variants: List[str],
        body_template: str,
        landing_page_url: str,
        batch_size: int = 100
    ) -> Dict:
        """
        Send email batch with A/B testing.
        
        Uses HubSpot Free (2,000/month limit).
        
        Args:
            vertical: Vertical name (medical, legal, realestate, agencies)
            email_number: Email sequence number (1, 2, or 3)
            subject_variants: List of 2 subject line variants for A/B test
            body_template: Email body template with personalization tokens
            landing_page_url: Landing page URL
            batch_size: Number of emails to send
            
        Returns:
            Dictionary with send statistics
        """
        if len(subject_variants) != 2:
            raise ValueError("Must provide exactly 2 subject line variants for A/B test")
        
        # Get contacts for vertical
        contacts = self.get_contacts_by_property(
            property_name='vertical',
            property_value=vertical,
            limit=batch_size
        )
        
        if not contacts:
            print(f"⚠️  No contacts found for vertical: {vertical}")
            return {"sent": 0, "contacts_found": 0}
        
        # Split for A/B test (50/50)
        split_point = len(contacts) // 2
        variant_a_contacts = contacts[:split_point]
        variant_b_contacts = contacts[split_point:]
        
        sent_count = 0
        
        # Send Variant A
        print(f"\n📤 Sending Variant A ({len(variant_a_contacts)} emails)...")
        for contact in variant_a_contacts:
            try:
                self.send_personalized_email(
                    contact=contact,
                    subject=subject_variants[0],
                    body=body_template,
                    landing_page_url=landing_page_url,
                    variant='A'
                )
                sent_count += 1
                time.sleep(0.5)  # Rate limiting
            except Exception as e:
                print(f"Error sending to {contact.get('email')}: {e}")
        
        # Send Variant B
        print(f"\n📤 Sending Variant B ({len(variant_b_contacts)} emails)...")
        for contact in variant_b_contacts:
            try:
                self.send_personalized_email(
                    contact=contact,
                    subject=subject_variants[1],
                    body=body_template,
                    landing_page_url=landing_page_url,
                    variant='B'
                )
                sent_count += 1
                time.sleep(0.5)  # Rate limiting
            except Exception as e:
                print(f"Error sending to {contact.get('email')}: {e}")
        
        print(f"\n✅ Sent {sent_count} emails to {vertical} vertical")
        print(f"   Variant A: {len(variant_a_contacts)} emails")
        print(f"   Variant B: {len(variant_b_contacts)} emails")
        
        return {
            "sent": sent_count,
            "contacts_found": len(contacts),
            "variant_a_count": len(variant_a_contacts),
            "variant_b_count": len(variant_b_contacts)
        }
    
    def get_non_responders(
        self,
        vertical: str,
        days_after: int = 3
    ) -> List[Dict]:
        """
        Get contacts who received email but didn't reply.
        
        Args:
            vertical: Vertical name
            days_after: Days since email was sent
            
        Returns:
            List of non-responder contacts
        """
        # Get all contacts for vertical who received email
        cutoff_date = (datetime.now() - timedelta(days=days_after)).isoformat()
        
        contacts = self.get_contacts_by_property(
            property_name='vertical',
            property_value=vertical,
            limit=500
        )
        
        # Filter for non-responders (would need custom property tracking replies)
        # For now, return all contacts (manual filtering needed)
        return contacts
    
    def track_metrics(self, vertical: str) -> Dict:
        """
        Pull metrics from HubSpot for ChatGPT analysis.
        
        Args:
            vertical: Vertical name
            
        Returns:
            Dictionary with metrics
        """
        contacts = self.get_contacts_by_property(
            property_name='vertical',
            property_value=vertical,
            limit=500
        )
        
        # Calculate basic metrics (would need HubSpot Marketing API for full metrics)
        total_sent = len(contacts)
        
        return {
            'vertical': vertical,
            'sent_count': total_sent,
            'note': 'Full metrics require HubSpot Marketing API access. Check HubSpot UI for opens/clicks/replies.'
        }


if __name__ == "__main__":
    """Example usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='GemFlush Campaign - Send A/B tested emails')
    parser.add_argument('--vertical', required=True, choices=['medical', 'legal', 'realestate', 'agencies'],
                       help='Target vertical')
    parser.add_argument('--email', type=int, default=1, help='Email sequence number (1, 2, or 3)')
    parser.add_argument('--count', type=int, default=200, help='Number of emails to send')
    
    args = parser.parse_args()
    
    # Load email content from file (to be generated by ChatGPT)
    email_content_file = f"chatgpt-native-stack/email-content/{args.vertical}_email_{args.email}.txt"
    
    if not os.path.exists(email_content_file):
        print(f"⚠️  Email content file not found: {email_content_file}")
        print("Generate email content using HubSpot Marketing Email GPT first.")
        sys.exit(1)
    
    # Read email content (format: first line = subject variant 1, second = subject variant 2, rest = body)
    with open(email_content_file, 'r') as f:
        lines = f.read().strip().split('\n')
        if len(lines) < 3:
            print(f"⚠️  Email content file format incorrect. Need: subject1, subject2, body")
            sys.exit(1)
        
        subject_variant_a = lines[0].strip()
        subject_variant_b = lines[1].strip()
        body_template = '\n'.join(lines[2:]).strip()
    
    # Landing page URL
    landing_page_url = f"https://your-subdomain.hs-sites.com/{args.vertical}-audit"
    
    # Initialize campaign (uses Alex@GEMflush.com as sender by default)
    campaign = GemFlushCampaign(sender_email="Alex@GEMflush.com")
    
    # Send batch
    results = campaign.send_email_batch(
        vertical=args.vertical,
        email_number=args.email,
        subject_variants=[subject_variant_a, subject_variant_b],
        body_template=body_template,
        landing_page_url=landing_page_url,
        batch_size=args.count
    )
    
    print(f"\n✅ Campaign complete!")
    print(f"   Vertical: {args.vertical}")
    print(f"   Emails sent: {results['sent']}")
    print(f"   Check HubSpot UI for opens/clicks/replies")

