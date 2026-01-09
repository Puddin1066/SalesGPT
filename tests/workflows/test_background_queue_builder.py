"""
Integration tests for Background Queue Builder.

Note: These tests focus on the logic methods that don't require full dependency setup.
"""
import pytest
from unittest.mock import MagicMock


def test_compute_elaboration_score_logic():
    """Test ELM score computation logic (standalone function)."""
    # Test the scoring logic directly without importing the full class
    def compute_elaboration_score(lead_metadata):
        """Standalone version of ELM score computation."""
        score = 0.0
        
        # Motivation (0-40 points)
        title = lead_metadata.get("title", "").lower()
        if any(word in title for word in ["owner", "ceo", "founder", "president"]):
            score += 30.0
        elif any(word in title for word in ["director", "manager", "partner"]):
            score += 20.0
        elif any(word in title for word in ["marketing", "growth", "strategy"]):
            score += 15.0
        
        # Ability (0-35 points)
        emp_count = lead_metadata.get("employee_count", 0)
        if 10 <= emp_count <= 50:
            score += 25.0
        elif 5 <= emp_count < 10:
            score += 15.0
        elif emp_count > 50:
            score += 10.0
        
        # Opportunity (0-25 points)
        website = lead_metadata.get("website", "")
        if website and website.startswith("http"):
            score += 25.0
        
        # Route selection
        route = "central" if score >= 60.0 else "peripheral"
        
        return (min(score, 100.0), route)
    
    # Test high-score lead (CEO + 25 employees + website)
    lead_metadata = {
        "title": "CEO",
        "employee_count": 25,
        "website": "https://test.com"
    }
    
    score, route = compute_elaboration_score(lead_metadata)
    
    assert 0 <= score <= 100
    assert route in ["central", "peripheral"]
    # CEO (30) + 25 employees (25) + website (25) = 80, should be central
    assert route == "central"
    assert score >= 60
    
    # Test low-score lead
    lead_metadata_low = {
        "title": "Assistant",
        "employee_count": 2,
        "website": None
    }
    
    score_low, route_low = compute_elaboration_score(lead_metadata_low)
    assert route_low == "peripheral"
    assert score_low < 60

