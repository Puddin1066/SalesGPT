"""
Unit tests for Apollo AB Manager.
"""
import pytest
from unittest.mock import MagicMock
from services.analytics.apollo_ab_manager import (
    ApolloABManager,
    ApolloSearchConfig,
    GeographyStrategy,
    EmployeeRangeStrategy,
    TitleStrategy
)


@pytest.fixture
def mock_state_manager():
    """Create mock state manager."""
    state = MagicMock()
    state.get_all_leads.return_value = []
    return state


@pytest.fixture
def apollo_ab_manager(mock_state_manager):
    """Create Apollo AB manager instance."""
    return ApolloABManager(mock_state_manager)


def test_apollo_config_to_code():
    """Test config code generation."""
    config = ApolloSearchConfig(
        geography_strategy=GeographyStrategy.CITY_SPECIFIC,
        geography_value="New York, NY",
        employee_range=EmployeeRangeStrategy.SMALL,
        title_strategy=TitleStrategy.DECISION_MAKERS,
        require_website=True,
        specialty="Dermatology"
    )
    
    code = config.to_code()
    assert code == "city-small-decision-web"


def test_apollo_config_to_params():
    """Test config to Apollo params conversion."""
    config = ApolloSearchConfig(
        geography_strategy=GeographyStrategy.CITY_SPECIFIC,
        geography_value="New York, NY",
        employee_range=EmployeeRangeStrategy.SMALL,
        title_strategy=TitleStrategy.DECISION_MAKERS,
        require_website=True,
        specialty="Dermatology"
    )
    
    params = config.to_apollo_params()
    
    assert params["min_employees"] == 5
    assert params["max_employees"] == 15
    assert params["has_website"] is True
    assert "CEO" in params["title_filters"] or "Owner" in params["title_filters"]


def test_get_next_config_to_test_undersampled(apollo_ab_manager, mock_state_manager):
    """Test that under-sampled configs get priority."""
    # Mock leads for one config
    mock_state_manager.get_all_leads.return_value = [
        {"apollo_config_code": "city-small-decision-web", "status": "sent"}
    ] * 3  # Only 3 leads
    
    config = apollo_ab_manager.get_next_config_to_test()
    
    # Should prefer under-sampled configs
    assert config is not None


def test_get_config_performance_report(apollo_ab_manager, mock_state_manager):
    """Test performance report generation."""
    # Mock leads with different configs
    mock_state_manager.get_all_leads.return_value = [
        {
            "apollo_config_code": "city-small-decision-web",
            "status": "closed",
            "score": 15,
            "email_sent_at": "2024-01-01T00:00:00",
            "reply_received_at": "2024-01-02T00:00:00",
            "booked_at": "2024-01-03T00:00:00"
        }
    ] * 10
    
    report = apollo_ab_manager.get_config_performance_report()
    
    assert len(report) > 0
    assert "config_code" in report[0]
    assert "roi" in report[0]

