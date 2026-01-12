"""
Bulk import contacts to HubSpot via API.

Reads CSV file and imports contacts using HubSpot API.
"""

import os
import sys
import csv
import requests
import time
from typing import List, Dict
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from services.crm.hubspot_agent import HubSpotAgent

load_dotenv('.env.local')


def read_leads_csv(csv_path: str) -> List[Dict]:
    """Read leads from CSV file."""
    
    if not os.path.exists(csv_path):
        print(f"❌ Error: CSV file not found: {csv_path}")
        return []
    
    leads = []
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Skip example rows
                if 'example@' in row.get('Email', '').lower():
                    continue
                leads.append(row)
        
        print(f"📄 Read {len(leads)} leads from CSV")
        return leads
        
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return []


def import_contacts(csv_path: str, batch_size: int = 10, dry_run: bool = False):
    """Import contacts from CSV to HubSpot."""
    
    api_key = os.getenv('HUBSPOT_API_KEY') or os.getenv('HUBSPOT_PAT')
    if not api_key:
        print("❌ Error: HUBSPOT_API_KEY or HUBSPOT_PAT not found")
        return False
    
    # Read CSV
    leads = read_leads_csv(csv_path)
    if not leads:
        return False
    
    print(f"\n🚀 {'[DRY RUN] ' if dry_run else ''}Importing {len(leads)} contacts to HubSpot...\n")
    
    # Initialize HubSpot agent
    hubspot = HubSpotAgent(api_key=api_key)
    
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for i, lead in enumerate(leads, 1):
        email = lead.get('Email', '').strip()
        if not email:
            print(f"   ⏭️  Row {i}: No email - skipping")
            skip_count += 1
            continue
        
        # Map CSV columns to HubSpot properties
        properties = {
            'email': email,
            'firstname': lead.get('First Name', '').strip(),
            'lastname': lead.get('Last Name', '').strip(),
            'company': lead.get('Company', '').strip(),
            'city': lead.get('City', '').strip(),
            'jobtitle': lead.get('Job Title', '').strip(),
            'vertical': lead.get('vertical', '').strip().lower()
        }
        
        # Remove empty properties
        properties = {k: v for k, v in properties.items() if v}
        
        # Validate vertical
        valid_verticals = ['medical', 'legal', 'realestate', 'agencies']
        if properties.get('vertical') and properties['vertical'] not in valid_verticals:
            print(f"   ⚠️  Row {i} ({email}): Invalid vertical '{properties['vertical']}' - skipping")
            skip_count += 1
            continue
        
        if dry_run:
            print(f"   [DRY RUN] Would import: {email} ({properties.get('vertical', 'no vertical')})")
            success_count += 1
        else:
            try:
                # Create or update contact
                contact_id = hubspot.create_or_update_contact(email, properties)
                
                if contact_id:
                    print(f"   ✅ {i}/{len(leads)}: {email} (ID: {contact_id})")
                    success_count += 1
                else:
                    print(f"   ❌ {i}/{len(leads)}: {email} - Failed")
                    error_count += 1
                
                # Rate limiting: Wait between batches
                if i % batch_size == 0:
                    time.sleep(0.5)
                    
            except Exception as e:
                print(f"   ❌ {i}/{len(leads)}: {email} - Error: {e}")
                error_count += 1
    
    # Summary
    print(f"\n📊 Import Summary:")
    print(f"   Total: {len(leads)}")
    print(f"   {'Would import' if dry_run else 'Imported'}: {success_count}")
    print(f"   Skipped: {skip_count}")
    if not dry_run:
        print(f"   Errors: {error_count}")
    
    if not dry_run and success_count > 0:
        print(f"\n✅ Imported {success_count} contacts successfully!")
        print(f"\n💡 Verify in HubSpot:")
        print(f"   1. Go to: Contacts → All Contacts")
        print(f"   2. Filter by 'vertical' property")
        print(f"   3. Check contacts appear correctly")
    
    return success_count > 0


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Import contacts from CSV to HubSpot')
    parser.add_argument('csv_file', help='Path to CSV file with leads')
    parser.add_argument('--batch-size', type=int, default=10, help='Batch size for rate limiting')
    parser.add_argument('--dry-run', action='store_true', help='Preview import without actually creating contacts')
    
    args = parser.parse_args()
    
    success = import_contacts(args.csv_file, args.batch_size, args.dry_run)
    sys.exit(0 if success else 1)

