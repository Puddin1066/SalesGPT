import pytest
import asyncio
import os
from unittest.mock import MagicMock, patch, AsyncMock

# Import after conftest has set up mocks
from main_agent import ASSCHOrchestrator
from services.apollo.apollo_agent import Lead

# Mock data for testing
MOCK_LEADS = [
    Lead(
        name="John Doe",
        email="john@example.com",
        website="https://example.com",
        company_name="Example Clinic",
        specialty="Dermatology",
        location="New York, NY",
        metadata={"title": "Owner", "employee_count": 10}
    )
]

@pytest.fixture
def mock_orchestrator():
    """Fixture to provide a fully mocked ASSCHOrchestrator."""
    with patch("main_agent.load_dotenv"), \
         patch("main_agent.ApolloAgent") as mock_apollo_cls, \
         patch("main_agent.SmartleadAgent") as mock_smartlead_cls, \
         patch("main_agent.SalesGPTWrapper") as mock_salesgpt_cls, \
         patch("main_agent.CalScheduler") as mock_scheduler_cls, \
         patch("main_agent.HubSpotAgent") as mock_crm_cls, \
         patch("main_agent.GEMflushAgent") as mock_visibility_cls, \
         patch("main_agent.StateManager") as mock_state_cls:
        
        # Instantiate the orchestrator
        orchestrator = ASSCHOrchestrator()
        
        # Set up the mock instances that were created during __init__
        orchestrator.apollo = mock_apollo_cls.return_value
        orchestrator.smartlead = mock_smartlead_cls.return_value
        orchestrator.salesgpt = mock_salesgpt_cls.return_value
        orchestrator.scheduler = mock_scheduler_cls.return_value
        orchestrator.crm = mock_crm_cls.return_value
        orchestrator.visibility = mock_visibility_cls.return_value
        orchestrator.state = mock_state_cls.return_value
        
        yield orchestrator

@pytest.mark.asyncio
async def test_e2e_flow_interested(mock_orchestrator):
    """Test the full E2E flow when a lead expresses interest."""
    print("\n--- Starting E2E Test (Interested Lead) ---")
    
    # 1. Setup mocks for Lead Generation (Apollo)
    mock_orchestrator.apollo.search_leads.return_value = MOCK_LEADS
    mock_orchestrator.apollo.score_leads.side_effect = lambda x: x
    print("MOCK: Apollo generated 1 lead: john@example.com")
    
    # 2. Setup mocks for Outreach (Smartlead)
    mock_orchestrator.smartlead.get_mailboxes.return_value = [{"id": 123}]
    mock_orchestrator.smartlead.create_campaign.return_value = 456
    mock_orchestrator.smartlead.add_leads_to_campaign.return_value = True
    mock_orchestrator.smartlead.send_reply.return_value = True
    print("MOCK: Smartlead campaign 456 created and lead added")
    
    # 3. Setup mocks for CRM (HubSpot)
    mock_orchestrator.crm.create_contact.return_value = "contact_789"
    mock_orchestrator.crm.update_pipeline_stage.return_value = True
    print("MOCK: HubSpot contact contact_789 created")
    
    # 4. Setup mocks for Visibility Enrichment (GEMflush)
    mock_orchestrator.visibility.get_competitor_comparison.return_value = {
        "clinic_id": "Example Clinic",
        "delta_score": -15,
        "percentage_delta": 15,
        "competitor_name": "Local Competitor"
    }
    mock_orchestrator.visibility.format_evidence_message.return_value = "Wait, your visibility is 15% lower than Local Competitor!"
    print("MOCK: GEMflush generated visibility evidence")
    
    # 5. Setup mocks for AI facilitation (SalesGPT)
    mock_orchestrator.salesgpt.generate_reply.side_effect = lambda **kwargs: {
        "intent": "interested",
        "body": f"I'm glad you're interested in {kwargs.get('clinic_name')}! I noticed you have some visibility issues.",
        "action": "send_booking_link"
    }
    print("MOCK: SalesGPT facilitating conversation with context")
    
    # 6. Setup mocks for Scheduling (Cal.com)
    mock_orchestrator.scheduler.get_booking_link.return_value = "https://cal.com/ted/15min"
    mock_orchestrator.scheduler.generate_confirmation_message.return_value = "Book here: https://cal.com/ted/15min"
    print("MOCK: Cal.com booking link generated")
    
    # --- PHASE 1: Run Daily Pipeline (Lead Gen -> Outreach -> CRM) ---
    print("\nPHASE 1: Running daily pipeline...")
    await mock_orchestrator.run_daily_pipeline(
        geography="New York, NY", 
        specialty="Dermatology", 
        lead_limit=1
    )
    
    # Verify pipeline steps
    mock_orchestrator.apollo.search_leads.assert_called_once()
    mock_orchestrator.smartlead.add_leads_to_campaign.assert_called_once()
    mock_orchestrator.crm.create_contact.assert_called_once()
    print("✅ Phase 1 complete: Lead sourced, campaign started, CRM synced")
    
    # --- PHASE 2: Handle Lead Reply (AI Facilitation -> Visibility -> Booking) ---
    print("\nPHASE 2: Handling lead reply...")
    # Mock lead state from Step 1
    mock_orchestrator.state.get_lead_state.return_value = {
        "company_name": "Example Clinic",
        "hubspot_contact_id": "contact_789"
    }
    
    await mock_orchestrator.handle_reply(
        thread_id="thread_abc",
        sender_email="john@example.com",
        sender_name="John Doe",
        email_body="Yes, I'm interested in hearing more about my clinic's visibility."
    )
    
    # Verify reply steps
    mock_orchestrator.salesgpt.generate_reply.assert_called_once()
    mock_orchestrator.scheduler.get_booking_link.assert_called_once()
    mock_orchestrator.smartlead.send_reply.assert_called_once()
    mock_orchestrator.crm.update_pipeline_stage.assert_called_with("contact_789", "booked")
    print("✅ Phase 2 complete: Reply handled by AI, booking link sent, CRM updated to 'booked'")
    
    print("\n--- E2E Test Passed Successfully! ---")

@pytest.mark.asyncio
async def test_e2e_flow_objection(mock_orchestrator):
    """Test the flow when a lead has an objection and needs visibility evidence."""
    print("\n--- Starting E2E Test (Objection Flow) ---")
    
    # Setup for objection intent
    mock_orchestrator.salesgpt.generate_reply.return_value = {
        "intent": "objection",
        "body": "I understand your concern about the cost.",
        "action": "send_evidence"
    }
    
    # Mock lead state
    mock_orchestrator.state.get_lead_state.return_value = {
        "company_name": "Example Clinic",
        "hubspot_contact_id": "contact_789"
    }
    
    # Simulate objection reply
    await mock_orchestrator.handle_reply(
        thread_id="thread_xyz",
        sender_email="john@example.com",
        sender_name="John Doe",
        email_body="This sounds expensive. Why should I care?"
    )
    
    # Verify visibility evidence was injected
    mock_orchestrator.visibility.get_competitor_comparison.assert_called_once()
    mock_orchestrator.visibility.format_evidence_message.assert_called_once()
    mock_orchestrator.smartlead.send_reply.assert_called_once()
    print("✅ Objection handled: AI injected visibility evidence from GEMflush into the reply")
    
    print("\n--- E2E Test (Objection) Passed Successfully! ---")

if __name__ == "__main__":
    asyncio.run(test_e2e_flow_interested(None))

