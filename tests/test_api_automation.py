"""
Automated API response tests for GEMflush and Apollo IO.

Tests both services with automated mock responses to avoid consuming credits.
"""
import pytest
from unittest.mock import patch, MagicMock
from services.apollo import ApolloAgent
from services.visibility import GEMflushAgent
from tests.fixtures.api_responses import (
    GEMflushResponseFixtures,
    ApolloResponseFixtures,
    gemflush_audit,
    gemflush_comparison,
    apollo_search,
    apollo_enrich_person,
    apollo_enrich_org
)


class TestGEMflushAutomation:
    """Automated tests for GEMflush API responses."""
    
    def test_automated_audit_response(self):
        """Test automated GEMflush audit response generation."""
        response = gemflush_audit("Example Clinic", ["Competitor A", "Competitor B"])
        
        assert "visibility_score" in response
        assert "competitor_scores" in response
        assert "top_keywords" in response
        assert response["clinic_id"] == "Example Clinic"
        assert "Competitor A" in response["competitor_scores"]
        assert response["source"] == "automated_fixture"
    
    def test_automated_comparison_response(self):
        """Test automated competitor comparison response."""
        response = gemflush_comparison("Example Clinic", "Competitor A")
        
        assert "clinic_score" in response
        assert "competitor_score" in response
        assert "delta_score" in response
        assert "percentage_delta" in response
        assert response["competitor_name"] == "Competitor A"
    
    @patch('services.visibility.gemflush_agent.requests.post')
    def test_gemflush_agent_with_automated_response(self, mock_post):
        """Test GEMflush agent using automated API response."""
        # Setup automated mock response
        mock_response = MagicMock()
        mock_response.json.return_value = gemflush_audit("Test Clinic", ["Competitor"])
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        # Initialize agent with real API mode
        agent = GEMflushAgent(use_real_api=True, api_key="test_key")
        audit = agent.get_audit("Test Clinic", ["Competitor"])
        
        assert audit["clinic_id"] == "Test Clinic"
        assert "visibility_score" in audit
    
    def test_gemflush_agent_automated_fallback(self):
        """Test GEMflush agent automated response fallback."""
        agent = GEMflushAgent(use_real_api=False)
        audit = agent.get_audit("Test Clinic", ["Competitor"])
        
        assert audit["clinic_id"] == "Test Clinic"
        assert "visibility_score" in audit
        assert "source" in audit


class TestApolloAutomation:
    """Automated tests for Apollo IO API responses."""
    
    def test_automated_search_response(self):
        """Test automated Apollo search response generation."""
        response = apollo_search(limit=3)
        
        assert "people" in response
        assert len(response["people"]) == 3
        assert "pagination" in response
        assert response["source"] == "automated_fixture"
    
    def test_automated_person_enrichment(self):
        """Test automated person enrichment response."""
        response = apollo_enrich_person("john@example.com")
        
        assert "person" in response
        assert response["person"]["email"] == "john@example.com"
        assert "source" in response["person"]
    
    def test_automated_org_enrichment(self):
        """Test automated organization enrichment response."""
        response = apollo_enrich_org("example.com")
        
        assert "organization" in response
        assert "example.com" in response["organization"]["website_url"]
        assert "source" in response["organization"]
    
    @patch('services.apollo.apollo_agent.requests.post')
    def test_apollo_agent_with_automated_response(self, mock_post):
        """Test Apollo agent using automated API response."""
        mock_response = MagicMock()
        mock_response.json.return_value = apollo_search(limit=2)
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        import os
        with patch.dict(os.environ, {"APOLLO_API_KEY": "test_key"}):
            agent = ApolloAgent()
            leads = agent.search_leads("New York, NY", "Dermatology", limit=2)
        
        assert len(leads) == 2
        assert leads[0].email.startswith("john")


class TestCombinedAutomation:
    """Test combined automation of both GEMflush and Apollo."""
    
    @patch('services.apollo.apollo_agent.requests.post')
    @patch('services.visibility.gemflush_agent.requests.post')
    def test_full_pipeline_with_automated_responses(self, mock_gemflush, mock_apollo):
        """Test full pipeline using automated responses for both services."""
        # Setup Apollo automated response
        apollo_mock = MagicMock()
        apollo_mock.json.return_value = apollo_search(limit=2)
        apollo_mock.raise_for_status = MagicMock()
        mock_apollo.return_value = apollo_mock
        
        # Setup GEMflush automated response
        gemflush_mock = MagicMock()
        gemflush_mock.json.return_value = gemflush_audit("Example Clinic", ["Competitor"])
        gemflush_mock.raise_for_status = MagicMock()
        mock_gemflush.return_value = gemflush_mock
        
        import os
        with patch.dict(os.environ, {"APOLLO_API_KEY": "test_key"}):
            # Test Apollo
            apollo_agent = ApolloAgent()
            leads = apollo_agent.search_leads("New York, NY", "Dermatology", limit=2)
            assert len(leads) == 2
            
            # Test GEMflush
            gemflush_agent = GEMflushAgent(use_real_api=True, api_key="test_key")
            audit = gemflush_agent.get_audit("Example Clinic", ["Competitor"])
            assert "visibility_score" in audit
            
            # Test competitor comparison
            comparison = gemflush_agent.get_competitor_comparison("Example Clinic", "Competitor")
            assert "delta_score" in comparison
        
        print("✅ Full pipeline automation test passed!")


@pytest.mark.integration
class TestRealAPIWithAutomation:
    """Integration tests that can use real APIs with automated fallbacks."""
    
    def test_apollo_with_automated_fallback(self):
        """Test Apollo with automated response if API key not available."""
        import os
        api_key = os.getenv("APOLLO_API_KEY")
        
        if not api_key:
            # Use automated response
            response = apollo_search(limit=2)
            assert len(response["people"]) == 2
            print("✅ Using automated Apollo response (no API key)")
        else:
            # Would use real API here
            print("✅ Real API key available (would use real API)")
    
    def test_gemflush_with_automated_fallback(self):
        """Test GEMflush with automated response if API key not available."""
        import os
        api_key = os.getenv("GEMFLUSH_API_KEY")
        
        if not api_key:
            # Use automated response
            response = gemflush_audit("Test Clinic")
            assert "visibility_score" in response
            print("✅ Using automated GEMflush response (no API key)")
        else:
            # Would use real API here
            print("✅ Real API key available (would use real API)")

