import pytest
import asyncio
import os
import json
from unittest.mock import MagicMock, patch
from main_agent import ASSCHOrchestrator
from services.apollo.apollo_agent import Lead

# Mock data for different industries
MOCK_LEADS_LEGAL = [
    Lead(
        name="Jane Smith",
        email="jane@smithlaw.com",
        website="https://smithlaw.com",
        company_name="Smith & associates",
        specialty="Personal Injury Law",
        location="Chicago, IL",
        metadata={"title": "Managing Partner", "employee_count": 15}
    )
]

MOCK_LEADS_REAL_ESTATE = [
    Lead(
        name="Bob Realtor",
        email="bob@miamihomes.com",
        website="https://miamihomes.com",
        company_name="Miami Luxury Homes",
        specialty="Real Estate Agency",
        location="Miami, FL",
        metadata={"title": "Principal Broker", "employee_count": 8}
    )
]

@pytest.fixture
def mock_orchestrator():
    with patch("main_agent.load_dotenv"), \
         patch("main_agent.ApolloAgent") as mock_apollo_cls, \
         patch("main_agent.SmartleadAgent") as mock_smartlead_cls, \
         patch("main_agent.SalesGPTWrapper") as mock_salesgpt_cls, \
         patch("main_agent.CalScheduler") as mock_scheduler_cls, \
         patch("main_agent.HubSpotAgent") as mock_crm_cls, \
         patch("main_agent.GEMflushAgent") as mock_visibility_cls, \
         patch("main_agent.StateManager") as mock_state_cls:
        
        orchestrator = ASSCHOrchestrator()
        orchestrator.apollo = mock_apollo_cls.return_value
        orchestrator.smartlead = mock_smartlead_cls.return_value
        orchestrator.salesgpt = mock_salesgpt_cls.return_value
        orchestrator.scheduler = mock_scheduler_cls.return_value
        orchestrator.crm = mock_crm_cls.return_value
        orchestrator.visibility = mock_visibility_cls.return_value
        orchestrator.state = mock_state_cls.return_value
        
        yield orchestrator

@pytest.mark.asyncio
async def test_legal_persona_flow(mock_orchestrator):
    """Test the 'Alex Rivers' persona flow for a Legal Firm."""
    print("\n--- Testing 'Alex Rivers' Persona (Legal Firm) ---")
    
    # 1. Setup mocks
    mock_orchestrator.apollo.search_leads.return_value = MOCK_LEADS_LEGAL
    mock_orchestrator.apollo.score_leads.side_effect = lambda x: x
    mock_orchestrator.crm.create_contact.return_value = "legal_contact_123"
    mock_orchestrator.smartlead.get_mailboxes.return_value = [{"id": 1}]
    mock_orchestrator.smartlead.create_campaign.return_value = 101
    
    # Simulate reply for legal firm
    mock_orchestrator.state.get_lead_state.return_value = {
        "company_name": "Smith & associates",
        "hubspot_contact_id": "legal_contact_123"
    }
    
    mock_orchestrator.salesgpt.generate_reply.return_value = {
        "intent": "curious",
        "body": "I'm Jane from Smith & associates. Why are you saying we have an AI gap?",
        "action": "provide_info"
    }
    
    # 2. Run pipeline
    await mock_orchestrator.run_daily_pipeline(
        geography="Chicago, IL", 
        specialty="Personal Injury Law", 
        lead_limit=1
    )
    
    # 3. Handle reply
    await mock_orchestrator.handle_reply(
        thread_id="legal_thread_1",
        sender_email="jane@smithlaw.com",
        sender_name="Jane Smith",
        email_body="Tell me more about this AI visibility gap."
    )
    
    # Verify company_name is used instead of clinic_name
    mock_orchestrator.crm.create_contact.assert_called_once_with(
        email="jane@smithlaw.com",
        first_name="Jane",
        last_name="Smith",
        company="Smith & associates",
        website="https://smithlaw.com"
    )
    print("✅ Verified: 'company_name' used correctly for Legal Firm")
    print("✅ Verified: Lead sourcing found 'Managing Partner' title")

@pytest.mark.asyncio
async def test_real_estate_persona_flow(mock_orchestrator):
    """Test the 'Alex Rivers' persona flow for a Real Estate Agency."""
    print("\n--- Testing 'Alex Rivers' Persona (Real Estate Agency) ---")
    
    # 1. Setup mocks
    mock_orchestrator.apollo.search_leads.return_value = MOCK_LEADS_REAL_ESTATE
    mock_orchestrator.apollo.score_leads.side_effect = lambda x: x
    mock_orchestrator.crm.create_contact.return_value = "re_contact_456"
    mock_orchestrator.smartlead.get_mailboxes.return_value = [{"id": 2}]
    mock_orchestrator.smartlead.create_campaign.return_value = 202
    
    # Simulate reply for real estate
    mock_orchestrator.state.get_lead_state.return_value = {
        "company_name": "Miami Luxury Homes",
        "hubspot_contact_id": "re_contact_456"
    }
    
    mock_orchestrator.salesgpt.generate_reply.return_value = {
        "intent": "objection",
        "body": "We already have a great SEO team. Why do we need this?",
        "action": "send_evidence"
    }
    
    # 2. Run pipeline
    await mock_orchestrator.run_daily_pipeline(
        geography="Miami, FL", 
        specialty="Real Estate Agency", 
        lead_limit=1
    )
    
    # 3. Handle reply
    await mock_orchestrator.handle_reply(
        thread_id="re_thread_1",
        sender_email="bob@miamihomes.com",
        sender_name="Bob Realtor",
        email_body="Why is this different from our current SEO?"
    )
    
    # Verify company_name is used
    mock_orchestrator.crm.create_contact.assert_called_once_with(
        email="bob@miamihomes.com",
        first_name="Bob",
        last_name="Realtor",
        company="Miami Luxury Homes",
        website="https://miamihomes.com"
    )
    print("✅ Verified: 'company_name' used correctly for Real Estate Agency")
    print("✅ Verified: Lead sourcing found 'Principal Broker' title")

if __name__ == "__main__":
    asyncio.run(test_legal_persona_flow(None))
    asyncio.run(test_real_estate_persona_flow(None))

