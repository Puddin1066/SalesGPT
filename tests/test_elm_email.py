"""
Tests for ELM-driven cold email generation.

Tests:
1. Route selection (central vs peripheral)
2. Disclaimer injection when mock flags are enabled
3. Email output validity (non-empty, reasonable length)
"""
import pytest
import os
import json
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path

from main_agent import ASSCHOrchestrator
from services.apollo.apollo_agent import Lead
from services.salesgpt.salesgpt_wrapper import SalesGPTWrapper


@pytest.fixture
def sample_lead_high_elaboration():
    """Lead with high elaboration score (should route to central)."""
    return Lead(
        name="Jane Smith",
        email="jane@example.com",
        website="https://example.com",
        company_name="Smith Dental",
        specialty="Dental",
        location="San Francisco, CA",
        metadata={
            "title": "CEO",
            "employee_count": 25,
            "linkedin_url": "https://linkedin.com/in/jane",
            "organization_id": "12345"
        }
    )


@pytest.fixture
def sample_lead_low_elaboration():
    """Lead with low elaboration score (should route to peripheral)."""
    return Lead(
        name="Bob Johnson",
        email="bob@example.com",
        website="",  # No website
        company_name="Johnson Medical",
        specialty="Medical",
        location="Austin, TX",
        metadata={
            "title": "Assistant",  # Low authority
            "employee_count": 2,  # Very small
            "linkedin_url": "",
            "organization_id": "67890"
        }
    )


@pytest.fixture
def mock_orchestrator():
    """Fixture to provide a mocked ASSCHOrchestrator."""
    with patch("main_agent.load_dotenv"), \
         patch("main_agent.ApolloAgent") as mock_apollo_cls, \
         patch("main_agent.SmartleadAgent") as mock_smartlead_cls, \
         patch("main_agent.SalesGPTWrapper") as mock_salesgpt_cls, \
         patch("main_agent.CalScheduler") as mock_scheduler_cls, \
         patch("main_agent.HubSpotAgent") as mock_crm_cls, \
         patch("main_agent.GEMflushAgent") as mock_visibility_cls, \
         patch("main_agent.CompetitorAgent") as mock_competitor_cls, \
         patch("main_agent.GEOScorer") as mock_scorer_cls, \
         patch("main_agent.StateManager") as mock_state_cls:
        
        orchestrator = ASSCHOrchestrator()
        
        orchestrator.apollo = mock_apollo_cls.return_value
        orchestrator.smartlead = mock_smartlead_cls.return_value
        orchestrator.salesgpt = mock_salesgpt_cls.return_value
        orchestrator.scheduler = mock_scheduler_cls.return_value
        orchestrator.crm = mock_crm_cls.return_value
        orchestrator.visibility = mock_visibility_cls.return_value
        orchestrator.competitor = mock_competitor_cls.return_value
        orchestrator.scorer = mock_scorer_cls.return_value
        orchestrator.state = mock_state_cls.return_value
        
        yield orchestrator


def test_elaboration_score_high_route(mock_orchestrator, sample_lead_high_elaboration):
    """Test that high elaboration leads route to 'central'."""
    score, route = mock_orchestrator._compute_elaboration_score(sample_lead_high_elaboration)
    
    assert score >= 60.0, f"Expected score >= 60, got {score}"
    assert route == "central", f"Expected 'central' route, got '{route}'"


def test_elaboration_score_low_route(mock_orchestrator, sample_lead_low_elaboration):
    """Test that low elaboration leads route to 'peripheral'."""
    score, route = mock_orchestrator._compute_elaboration_score(sample_lead_low_elaboration)
    
    assert score < 60.0, f"Expected score < 60, got {score}"
    assert route == "peripheral", f"Expected 'peripheral' route, got '{route}'"


def test_elaboration_score_range(mock_orchestrator, sample_lead_high_elaboration):
    """Test that elaboration score is in valid range (0-100)."""
    score, route = mock_orchestrator._compute_elaboration_score(sample_lead_high_elaboration)
    
    assert 0.0 <= score <= 100.0, f"Score should be between 0 and 100"


@pytest.fixture
def mock_salesgpt_wrapper():
    """Fixture for SalesGPTWrapper with mocked API."""
    with patch("services.salesgpt.salesgpt_wrapper.SalesGPTAPI") as mock_api_cls:
        wrapper = SalesGPTWrapper(verbose=False)
        wrapper.sales_api = MagicMock()
        wrapper.sales_api.sales_agent = MagicMock()
        wrapper.sales_api.sales_agent.conversation_history = []
        wrapper.sales_api.sales_agent.seed_agent = MagicMock()
        wrapper.sales_api.do = AsyncMock(return_value={"response": "Test email body"})
        yield wrapper


def test_disclaimer_injection_central_route(mock_salesgpt_wrapper):
    """Test that disclaimers are injected for central route with mock flags."""
    playbook_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "examples",
        "elm_email_playbook.json"
    )
    
    # Load playbook
    with open(playbook_path, "r") as f:
        playbook = json.load(f)
    
    route_config = playbook["routes"]["central"]
    disclaimer_mode = {
        "simulated_competitor_data": True,
        "simulated_kg_presence": True,
        "simulated_audit_data": True
    }
    
    email_body = "This is a test email body."
    result = mock_salesgpt_wrapper._inject_disclaimer(
        email_body,
        route_config,
        disclaimer_mode
    )
    
    # Check that disclaimer was added
    assert len(result) > len(email_body), "Disclaimer should be added"
    assert "simulated" in result.lower() or "preview" in result.lower() or "estimate" in result.lower(), \
        "Disclaimer should contain simulated/preview/estimate language"


def test_disclaimer_injection_peripheral_route(mock_salesgpt_wrapper):
    """Test that disclaimers are injected for peripheral route with mock flags."""
    playbook_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "examples",
        "elm_email_playbook.json"
    )
    
    # Load playbook
    with open(playbook_path, "r") as f:
        playbook = json.load(f)
    
    route_config = playbook["routes"]["peripheral"]
    disclaimer_mode = {
        "simulated_competitor_data": True,
        "simulated_kg_presence": True,
        "simulated_audit_data": True
    }
    
    email_body = "This is a test email body."
    result = mock_salesgpt_wrapper._inject_disclaimer(
        email_body,
        route_config,
        disclaimer_mode
    )
    
    # Check that disclaimer was added
    assert len(result) > len(email_body), "Disclaimer should be added"
    assert "preview" in result.lower() or "estimate" in result.lower(), \
        "Disclaimer should contain preview/estimate language"


def test_disclaimer_no_injection_when_disabled(mock_salesgpt_wrapper):
    """Test that no disclaimer is injected when flags are disabled."""
    playbook_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "examples",
        "elm_email_playbook.json"
    )
    
    # Load playbook
    with open(playbook_path, "r") as f:
        playbook = json.load(f)
    
    route_config = playbook["routes"]["central"]
    disclaimer_mode = {
        "simulated_competitor_data": False,
        "simulated_kg_presence": False,
        "simulated_audit_data": False
    }
    
    email_body = "This is a test email body."
    result = mock_salesgpt_wrapper._inject_disclaimer(
        email_body,
        route_config,
        disclaimer_mode
    )
    
    # Check that no disclaimer was added
    assert result == email_body, "No disclaimer should be added when flags are disabled"


@pytest.mark.asyncio
async def test_email_generation_validity(mock_salesgpt_wrapper):
    """Test that generated emails are valid (non-empty, reasonable length)."""
    # Mock the API response
    mock_salesgpt_wrapper.sales_api.do = AsyncMock(return_value={
        "response": "Hi Jane,\n\nI noticed Smith Dental and wanted to share something about your AI visibility.\n\nBest,\nAlex"
    })
    
    competitive_analysis = {
        "lead_score": 45,
        "competitor_score": 75,
        "gap_percentage": 30,
        "referral_multiplier": 2.5,
        "competitor_name": "Competitor Dental",
        "competitor_has_kg": True
    }
    
    disclaimer_mode = {
        "simulated_competitor_data": True,
        "simulated_kg_presence": True,
        "simulated_audit_data": True
    }
    
    result = mock_salesgpt_wrapper.generate_initial_email(
        route="central",
        lead_name="Jane Smith",
        company_name="Smith Dental",
        location="San Francisco, CA",
        specialty="Dental",
        competitive_analysis=competitive_analysis,
        disclaimer_mode=disclaimer_mode
    )
    
    # Check structure
    assert "subject" in result, "Result should have 'subject' key"
    assert "body" in result, "Result should have 'body' key"
    assert "route" in result, "Result should have 'route' key"
    
    # Check non-empty
    assert result["subject"], "Subject should not be empty"
    assert result["body"], "Body should not be empty"
    
    # Check reasonable length (central route: 200-250 words, but allow some flexibility)
    word_count = len(result["body"].split())
    assert 50 <= word_count <= 400, f"Body should be 50-400 words, got {word_count}"
    
    # Check subject length (typically 50-70 chars)
    assert len(result["subject"]) <= 100, f"Subject should be <= 100 chars, got {len(result['subject'])}"


@pytest.mark.asyncio
async def test_email_generation_peripheral_route_length(mock_salesgpt_wrapper):
    """Test that peripheral route emails are shorter."""
    # Mock the API response
    mock_salesgpt_wrapper.sales_api.do = AsyncMock(return_value={
        "response": "Hi Bob,\n\nQuick question about your clinic's visibility. Would you be open to a 15-min chat?\n\nBest,\nAlex"
    })
    
    competitive_analysis = {
        "lead_score": 30,
        "competitor_score": 60,
        "gap_percentage": 30,
        "referral_multiplier": 2.0,
        "competitor_name": "Competitor Medical",
        "competitor_has_kg": False
    }
    
    disclaimer_mode = {
        "simulated_competitor_data": True,
        "simulated_kg_presence": False,
        "simulated_audit_data": True
    }
    
    result = mock_salesgpt_wrapper.generate_initial_email(
        route="peripheral",
        lead_name="Bob Johnson",
        company_name="Johnson Medical",
        location="Austin, TX",
        specialty="Medical",
        competitive_analysis=competitive_analysis,
        disclaimer_mode=disclaimer_mode
    )
    
    # Check that peripheral route emails are shorter (100-150 words)
    word_count = len(result["body"].split())
    assert word_count <= 200, f"Peripheral route should be <= 200 words, got {word_count}"


def test_playbook_loading(mock_salesgpt_wrapper):
    """Test that playbook loads correctly."""
    playbook = mock_salesgpt_wrapper._load_playbook()
    
    assert "routes" in playbook, "Playbook should have 'routes' key"
    assert "central" in playbook["routes"], "Playbook should have 'central' route"
    assert "peripheral" in playbook["routes"], "Playbook should have 'peripheral' route"
    assert "sequence_progression" in playbook, "Playbook should have 'sequence_progression' key"

