"""
Unit tests for Metrics Tracker.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock
from services.analytics.metrics_tracker import MetricsTracker


@pytest.fixture
def mock_state_manager():
    """Create mock state manager."""
    return MagicMock()


@pytest.fixture
def metrics_tracker(mock_state_manager):
    """Create metrics tracker instance."""
    return MetricsTracker(mock_state_manager)


def test_get_variant_performance(metrics_tracker, mock_state_manager):
    """Test variant performance calculation."""
    # Mock leads with variant data
    mock_state_manager.get_all_leads.return_value = [
        {
            "variant_code": "test-variant",
            "email_sent_at": (datetime.now() - timedelta(days=1)).isoformat(),
            "reply_received_at": (datetime.now() - timedelta(days=1) + timedelta(hours=2)).isoformat(),
            "reply_intent": "interested",
            "booked_at": (datetime.now() - timedelta(days=1) + timedelta(hours=3)).isoformat(),
            "status": "closed"
        }
    ] * 10
    
    perf = metrics_tracker.get_variant_performance("test-variant", days_back=30)
    
    assert "sent_count" in perf
    assert "reply_rate" in perf
    assert perf["sent_count"] == 10


def test_get_niche_performance(metrics_tracker, mock_state_manager):
    """Test niche performance analysis."""
    mock_state_manager.get_all_leads.return_value = [
        {
            "specialty": "Dermatology",
            "email_sent_at": (datetime.now() - timedelta(days=1)).isoformat(),
            "reply_received_at": (datetime.now() - timedelta(days=1) + timedelta(hours=1)).isoformat(),
            "booked_at": (datetime.now() - timedelta(days=1) + timedelta(hours=2)).isoformat(),
            "status": "closed"
        }
    ] * 5
    
    niches = metrics_tracker.get_niche_performance("specialty", days_back=30)
    
    assert len(niches) > 0
    assert niches[0]["niche"] == "Dermatology"
    assert "reply_rate" in niches[0]

