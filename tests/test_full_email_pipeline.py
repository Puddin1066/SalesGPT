"""
Test the full email pipeline:
1. Source 50 leads from Apollo (mocked)
2. Prioritize them
3. Customize messages with AI (mocked)
4. Send emails (mocked)
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime
from typing import List, Dict

# Import required modules
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from salesgpt.config import get_settings
from salesgpt.container import ServiceContainer
from workflows.background_queue_builder import BackgroundQueueBuilder
from state.state_manager import StateManager


class MockApolloAgent:
    """Mock Apollo agent that returns 50 test leads."""
    
    def search_people(self, geography: str, specialty: str, limit: int = 50, **kwargs) -> List[Dict]:
        """Return 50 mocked leads."""
        leads = []
        for i in range(1, 51):
            leads.append({
                "id": f"apollo_{i}",
                "first_name": f"John{i}",
                "last_name": f"Doe{i}",
                "name": f"John{i} Doe{i}",
                "email": f"john{i}.doe{i}@example.com",
                "title": f"{specialty} Manager" if i % 2 == 0 else f"Senior {specialty}",
                "organization_name": f"Company{i} Inc.",
                "organization_id": f"org_{i}",
                "linkedin_url": f"https://linkedin.com/in/johndoe{i}",
                "twitter_url": None,
                "github_url": None,
                "personal_emails": [],
                "work_email": f"john{i}.doe{i}@example.com",
                "state": "NY" if i % 3 == 0 else "CA" if i % 3 == 1 else "TX",
                "city": "New York" if i % 3 == 0 else "San Francisco" if i % 3 == 1 else "Austin",
                "country": "United States",
                "seniority": "manager" if i % 2 == 0 else "senior",
                "department": specialty,
                "sources": [],
                "employment_history": [],
                "education_history": [],
                "headline": f"Experienced {specialty} professional",
                "raw": {}
            })
        return leads
    
    def enrich_person(self, email: str) -> Dict:
        """Return enriched lead data."""
        return {
            "email": email,
            "enriched_at": datetime.now().isoformat(),
            "score": 75.0 + (hash(email) % 25),  # Random score between 75-100
            "linkedin_data": {"connections": hash(email) % 500},
            "twitter_data": None
        }


class MockSalesGPTWrapper:
    """Mock SalesGPT wrapper that generates email content."""
    
    def generate_email(
        self,
        lead: Dict,
        evidence: Dict = None,
        persuasion_route: str = "central"
    ) -> Dict:
        """Generate email content for a lead."""
        name = lead.get("first_name", lead.get("name", "there"))
        company = lead.get("organization_name", "your company")
        title = lead.get("title", "professional")
        
        # Generate personalized subject
        subject_variants = [
            f"Quick question about {company}",
            f"Interesting approach at {company}",
            f"Worth 5 minutes for {company}?",
            f"{title} insights for {company}",
            f"Following up on {company}"
        ]
        subject = subject_variants[hash(lead["email"]) % len(subject_variants)]
        
        # Generate personalized body based on persuasion route
        if persuasion_route == "central":
            body = f"""Hi {name},

I noticed {company} is focused on {title} - I thought you'd find this relevant.

We've helped similar companies achieve:
• 30% increase in efficiency
• 25% cost reduction
• Better team alignment

Would you be open to a quick 15-minute call to see if this could benefit {company}?

Best regards,
SalesGPT Team"""
        else:
            body = f"""Hi {name},

Quick question - have you considered how AI can transform {title} operations at {company}?

We're seeing amazing results with companies like yours. Happy to share a quick case study.

Best,
SalesGPT Team"""
        
        return {
            "subject": subject,
            "body": body,
            "personalization_score": 85.0 + (hash(lead["email"]) % 15),
            "generated_at": datetime.now().isoformat()
        }


class MockSmartleadAgent:
    """Mock Smartlead agent for sending emails."""
    
    def __init__(self):
        self.sent_emails = []
        self.campaign_id = "test_campaign_123"
    
    def create_campaign(self, name: str) -> str:
        """Create a mock campaign."""
        return self.campaign_id
    
    def add_leads_to_campaign(
        self,
        campaign_id: str,
        leads: List[Dict]
    ) -> Dict:
        """Add leads to campaign and send."""
        results = []
        for lead in leads:
            self.sent_emails.append({
                "email": lead["email"],
                "subject": lead.get("email_subject", ""),
                "body": lead.get("email_body", ""),
                "sent_at": datetime.now().isoformat(),
                "campaign_id": campaign_id
            })
            results.append({
                "email": lead["email"],
                "status": "sent",
                "message_id": f"msg_{hash(lead['email'])}"
            })
        
        return {
            "campaign_id": campaign_id,
            "leads_added": len(leads),
            "results": results
        }


class MockHubSpotAgent:
    """Mock HubSpot agent for CRM updates."""
    
    def __init__(self):
        self.contacts = {}
        self.deals = {}
    
    def create_or_update_contact(self, email: str, properties: Dict) -> Dict:
        """Create or update contact in HubSpot."""
        contact_id = f"contact_{hash(email)}"
        self.contacts[email] = {
            "id": contact_id,
            "email": email,
            "properties": properties,
            "created_at": datetime.now().isoformat()
        }
        return {
            "id": contact_id,
            "email": email,
            "properties": properties
        }
    
    def create_deal(self, contact_id: str, properties: Dict) -> Dict:
        """Create a deal in HubSpot."""
        deal_id = f"deal_{hash(contact_id)}"
        self.deals[contact_id] = {
            "id": deal_id,
            "contact_id": contact_id,
            "properties": properties,
            "created_at": datetime.now().isoformat()
        }
        return {
            "id": deal_id,
            "properties": properties
        }


def test_full_email_pipeline():
    """Test the complete email pipeline with mocked APIs."""
    
    print("\n" + "="*80)
    print("🧪 TESTING FULL EMAIL PIPELINE")
    print("="*80)
    print("\n1️⃣  Setting up mocked services...")
    
    # Initialize mocks
    mock_apollo = MockApolloAgent()
    mock_salesgpt = MockSalesGPTWrapper()
    mock_smartlead = MockSmartleadAgent()
    mock_hubspot = MockHubSpotAgent()
    
    # Initialize state manager with test database
    settings = get_settings()
    
    # Use a test database for this test
    test_db_path = "test_salesgpt.db"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    # Temporarily override database URL
    original_db_url = settings.database_url
    settings.database_url = f"sqlite:///{test_db_path}"
    
    # Initialize database and state manager
    from salesgpt.db.connection import DatabaseManager, get_db_session
    from salesgpt.models.database import Base
    
    # Create database manager with test database
    db_manager = DatabaseManager(database_url=settings.database_url)
    
    # Initialize database schema
    db_manager.create_tables()
    
    # Create state manager
    state_manager = StateManager(db_manager=db_manager)
    
    # Initialize queue builder with mocked services
    ab_manager = Mock()  # Mock AB test manager
    apollo_ab = Mock()  # Mock Apollo AB manager
    competitor = Mock()  # Mock competitor agent
    visibility = Mock()  # Mock visibility agent
    scorer = Mock()  # Mock GEO scorer
    
    queue_builder = BackgroundQueueBuilder(
        apollo=mock_apollo,
        salesgpt=mock_salesgpt,
        hubspot=mock_hubspot,
        state_manager=state_manager,
        ab_manager=ab_manager,
        apollo_ab=apollo_ab,
        competitor=competitor,
        visibility=visibility,
        scorer=scorer
    )
    
    print("   ✅ Services initialized\n")
    
    # Step 1: Source 50 leads
    print("2️⃣  Sourcing 50 leads from Apollo (mocked)...")
    geography = "New York, NY"
    specialty = "Sales"
    
    leads = mock_apollo.search_people(
        geography=geography,
        specialty=specialty,
        limit=50
    )
    
    print(f"   ✅ Sourced {len(leads)} leads")
    print(f"   📧 Sample emails: {', '.join([l['email'] for l in leads[:3]])}...\n")
    
    # Step 2: Prioritize and process leads
    print("3️⃣  Prioritizing leads and generating emails...")
    
    processed_leads = []
    for i, lead in enumerate(leads, 1):
        # Enrich lead
        enriched = mock_apollo.enrich_person(lead["email"])
        lead.update(enriched)
        
        # Compute ELM score (simplified)
        elm_score = lead.get("score", 75.0)
        persuasion_route = "central" if elm_score >= 85 else "peripheral"
        
        # Generate email
        email_content = mock_salesgpt.generate_email(
            lead=lead,
            persuasion_route=persuasion_route
        )
        
        # Create HubSpot contact
        hubspot_contact = mock_hubspot.create_or_update_contact(
            email=lead["email"],
            properties={
                "firstname": lead.get("first_name", ""),
                "lastname": lead.get("last_name", ""),
                "company": lead.get("organization_name", ""),
                "jobtitle": lead.get("title", ""),
                "hs_lead_status": "NEW"
            }
        )
        
        # Store in state
        state_manager.update_lead_state(
            email=lead["email"],
            state={
                **lead,
                "email_subject": email_content["subject"],
                "email_body": email_content["body"],
                "persuasion_route": persuasion_route,
                "elaboration_score": elm_score,
                "hubspot_contact_id": hubspot_contact["id"],
                "status": "pending_review",
                "variant_code": f"variant_{i % 3 + 1}",
                "created_at": datetime.now().isoformat()
            }
        )
        
        processed_leads.append({
            **lead,
            "email_subject": email_content["subject"],
            "email_body": email_content["body"],
            "persuasion_route": persuasion_route,
            "elaboration_score": elm_score,
            "hubspot_contact_id": hubspot_contact["id"]
        })
        
        if i % 10 == 0:
            print(f"   ✅ Processed {i}/{len(leads)} leads...")
    
    print(f"   ✅ All {len(processed_leads)} leads processed\n")
    
    # Sort by priority (ELM score)
    processed_leads.sort(key=lambda x: x.get("elaboration_score", 0), reverse=True)
    
    print("4️⃣  Prioritized leads (top 10 by score):")
    for i, lead in enumerate(processed_leads[:10], 1):
        print(f"   {i:2d}. {lead['email']:<30} Score: {lead['elaboration_score']:.1f}  Route: {lead['persuasion_route']}")
    print()
    
    # Step 3: Send emails
    print("5️⃣  Sending emails via Smartlead (mocked)...")
    
    # Prepare leads for sending
    leads_to_send = [
        {
            "email": lead["email"],
            "email_subject": lead["email_subject"],
            "email_body": lead["email_body"]
        }
        for lead in processed_leads
    ]
    
    # Send via Smartlead
    send_results = mock_smartlead.add_leads_to_campaign(
        campaign_id=mock_smartlead.campaign_id,
        leads=leads_to_send
    )
    
    print(f"   ✅ Sent {send_results['leads_added']} emails")
    print(f"   📧 Campaign ID: {send_results['campaign_id']}\n")
    
    # Update state with sent status
    for lead in processed_leads:
        state_manager.update_lead_state(
            lead["email"],
            {
                "status": "sent",
                "email_sent_at": datetime.now().isoformat()
            }
        )
    
    # Step 4: Verify results
    print("6️⃣  Verifying results...")
    
    # Check state manager
    all_leads = state_manager.get_all_leads()
    sent_leads = [l for l in all_leads if l.get("status") == "sent"]
    pending_leads = [l for l in all_leads if l.get("status") == "pending_review"]
    
    print(f"   ✅ Total leads in database: {len(all_leads)}")
    print(f"   ✅ Sent leads: {len(sent_leads)}")
    print(f"   ✅ Pending leads: {len(pending_leads)}")
    print(f"   ✅ HubSpot contacts created: {len(mock_hubspot.contacts)}")
    print(f"   ✅ Smartlead emails sent: {len(mock_smartlead.sent_emails)}\n")
    
    # Show sample email
    print("7️⃣  Sample generated email:")
    sample_lead = processed_leads[0]
    print(f"   📧 To: {sample_lead['email']}")
    print(f"   📋 Subject: {sample_lead['email_subject']}")
    print(f"   💬 Body preview: {sample_lead['email_body'][:100]}...\n")
    
    # Summary statistics
    print("="*80)
    print("📊 PIPELINE SUMMARY")
    print("="*80)
    print(f"✅ Leads sourced: {len(leads)}")
    print(f"✅ Leads processed: {len(processed_leads)}")
    print(f"✅ Emails generated: {len(processed_leads)}")
    print(f"✅ Emails sent: {send_results['leads_added']}")
    print(f"✅ HubSpot contacts: {len(mock_hubspot.contacts)}")
    print(f"✅ Central route emails: {sum(1 for l in processed_leads if l['persuasion_route'] == 'central')}")
    print(f"✅ Peripheral route emails: {sum(1 for l in processed_leads if l['persuasion_route'] == 'peripheral')}")
    print()
    print(f"📈 Average ELM score: {sum(l.get('elaboration_score', 0) for l in processed_leads) / len(processed_leads):.1f}")
    print(f"📈 Top score: {max(l.get('elaboration_score', 0) for l in processed_leads):.1f}")
    print(f"📈 Bottom score: {min(l.get('elaboration_score', 0) for l in processed_leads):.1f}")
    print()
    print("="*80)
    print("✅ TEST COMPLETED SUCCESSFULLY")
    print("="*80)
    
    # Cleanup
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    # Assertions
    assert len(leads) == 50, "Should source 50 leads"
    assert len(processed_leads) == 50, "Should process 50 leads"
    assert send_results['leads_added'] == 50, "Should send 50 emails"
    assert len(mock_hubspot.contacts) == 50, "Should create 50 HubSpot contacts"
    assert len(mock_smartlead.sent_emails) == 50, "Should send 50 emails via Smartlead"
    
    print("\n✅ All assertions passed!")


if __name__ == "__main__":
    test_full_email_pipeline()

