"""
Pytest fixtures for service mocking.

Provides fixtures for all services to enable easy testing with dependency injection.
"""
import pytest
from unittest.mock import MagicMock

from services.apollo.apollo_agent import ApolloAgent
from services.outbound.smartlead_agent import SmartleadAgent
from services.salesgpt.salesgpt_wrapper import SalesGPTWrapper
from services.scheduler.cal_scheduler import CalScheduler
from services.crm.hubspot_agent import HubSpotAgent
from services.visibility.gemflush_agent import GEMflushAgent
from services.competitor.competitor_agent import CompetitorAgent
from services.scoring.geo_scorer import GEOScorer
from state.state_manager import StateManager


@pytest.fixture
def mock_apollo_agent():
    """Mock Apollo agent."""
    return MagicMock(spec=ApolloAgent)


@pytest.fixture
def mock_smartlead_agent():
    """Mock Smartlead agent."""
    return MagicMock(spec=SmartleadAgent)


@pytest.fixture
def mock_salesgpt_wrapper():
    """Mock SalesGPT wrapper."""
    return MagicMock(spec=SalesGPTWrapper)


@pytest.fixture
def mock_scheduler():
    """Mock Cal scheduler."""
    return MagicMock(spec=CalScheduler)


@pytest.fixture
def mock_crm_agent():
    """Mock HubSpot CRM agent."""
    return MagicMock(spec=HubSpotAgent)


@pytest.fixture
def mock_visibility_agent():
    """Mock GEMflush visibility agent."""
    return MagicMock(spec=GEMflushAgent)


@pytest.fixture
def mock_competitor_agent():
    """Mock competitor agent."""
    return MagicMock(spec=CompetitorAgent)


@pytest.fixture
def mock_scorer():
    """Mock GEO scorer."""
    return MagicMock(spec=GEOScorer)


@pytest.fixture
def mock_state_manager():
    """Mock state manager."""
    return MagicMock(spec=StateManager)


@pytest.fixture
def test_orchestrator(
    mock_apollo_agent,
    mock_smartlead_agent,
    mock_salesgpt_wrapper,
    mock_scheduler,
    mock_crm_agent,
    mock_visibility_agent,
    mock_competitor_agent,
    mock_scorer,
    mock_state_manager
):
    """Create test orchestrator with all mocked services."""
    from main_agent import ASSCHOrchestrator
    
    return ASSCHOrchestrator(
        apollo=mock_apollo_agent,
        smartlead=mock_smartlead_agent,
        salesgpt=mock_salesgpt_wrapper,
        scheduler=mock_scheduler,
        crm=mock_crm_agent,
        visibility=mock_visibility_agent,
        competitor=mock_competitor_agent,
        scorer=mock_scorer,
        state=mock_state_manager
    )

