"""
Pytest tests for Apollo API integration.

Tests include:
- Search functionality (with mocking to avoid credit consumption)
- Enrichment methods (with mocking to avoid credit consumption)
- Error handling for credit-related issues
- Integration test (optional, requires API key)
"""
import pytest
import os
from unittest.mock import patch, MagicMock
from services.apollo import ApolloAgent
from services.apollo.apollo_agent import Lead


@pytest.fixture
def mock_apollo_response():
    """Mock Apollo API response for search."""
    return {
        "people": [
            {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "title": "CEO",
                "linkedin_url": "https://linkedin.com/in/johndoe",
                "organization": {
                    "id": "org_123",
                    "name": "Example Clinic",
                    "website_url": "https://example.com",
                    "estimated_num_employees": 15
                }
            },
            {
                "first_name": "Jane",
                "last_name": "Smith",
                "email": "jane@example.com",
                "title": "Medical Director",
                "linkedin_url": "https://linkedin.com/in/janesmith",
                "organization": {
                    "id": "org_456",
                    "name": "Smith Medical",
                    "website_url": "https://smithmedical.com",
                    "estimated_num_employees": 25
                }
            }
        ]
    }


@pytest.fixture
def mock_person_enrichment_response():
    """Mock Apollo API response for person enrichment."""
    return {
        "person": {
            "id": "person_123",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "title": "CEO",
            "linkedin_url": "https://linkedin.com/in/johndoe",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    }


@pytest.fixture
def mock_organization_enrichment_response():
    """Mock Apollo API response for organization enrichment."""
    return {
        "organization": {
            "id": "org_123",
            "name": "Example Clinic",
            "website_url": "https://example.com",
            "estimated_num_employees": 15,
            "updated_at": "2024-01-01T00:00:00Z"
        }
    }


class TestApolloAgent:
    """Test suite for ApolloAgent class."""
    
    def test_initialization_with_api_key(self):
        """Test ApolloAgent initialization with API key."""
        with patch.dict(os.environ, {"APOLLO_API_KEY": "test_key_123"}):
            agent = ApolloAgent()
            assert agent.api_key == "test_key_123"
            assert agent.base_url == "https://api.apollo.io/v1"
    
    def test_initialization_without_api_key(self):
        """Test ApolloAgent initialization fails without API key."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="APOLLO_API_KEY not found"):
                ApolloAgent()
    
    @patch('services.apollo.apollo_agent.requests.post')
    def test_search_leads_success(self, mock_post, mock_apollo_response):
        """Test successful lead search."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = mock_apollo_response
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        # Initialize agent
        with patch.dict(os.environ, {"APOLLO_API_KEY": "test_key"}):
            agent = ApolloAgent()
            leads = agent.search_leads(
                geography="New York, NY",
                specialty="Dermatology",
                limit=2
            )
        
        # Assertions
        assert len(leads) == 2
        assert leads[0].name == "John Doe"
        assert leads[0].email == "john@example.com"
        assert leads[0].company_name == "Example Clinic"
        assert leads[0].website == "https://example.com"
        assert leads[1].name == "Jane Smith"
        
        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "mixed_people/search" in call_args[0][0]
    
    @patch('services.apollo.apollo_agent.requests.post')
    def test_search_leads_filters_website(self, mock_post, mock_apollo_response):
        """Test that search filters out leads without websites when required."""
        # Modify mock to include a lead without website
        mock_apollo_response["people"].append({
            "first_name": "No",
            "last_name": "Website",
            "email": "noweb@example.com",
            "organization": {
                "name": "No Website Co",
                "website_url": "",  # No website
            }
        })
        
        mock_response = MagicMock()
        mock_response.json.return_value = mock_apollo_response
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        with patch.dict(os.environ, {"APOLLO_API_KEY": "test_key"}):
            agent = ApolloAgent()
            leads = agent.search_leads(
                geography="New York, NY",
                specialty="Dermatology",
                has_website=True,
                limit=10
            )
        
        # Should filter out the lead without website
        assert len(leads) == 2
    
    @patch('services.apollo.apollo_agent.requests.post')
    def test_search_leads_api_error_handling(self, mock_post):
        """Test error handling for API errors."""
        import requests
        # Setup mock to raise 401 error
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.side_effect = requests.exceptions.HTTPError(response=mock_response)
        
        with patch.dict(os.environ, {"APOLLO_API_KEY": "test_key"}):
            agent = ApolloAgent()
            with pytest.raises(requests.exceptions.HTTPError):
                agent.search_leads("New York, NY", "Dermatology")
    
    @patch('services.apollo.apollo_agent.requests.post')
    def test_search_leads_credit_error_402(self, mock_post):
        """Test handling of 402 Payment Required error."""
        import requests
        mock_response = MagicMock()
        mock_response.status_code = 402
        mock_response.text = "Payment Required"
        mock_post.side_effect = requests.exceptions.HTTPError(response=mock_response)
        
        with patch.dict(os.environ, {"APOLLO_API_KEY": "test_key"}):
            agent = ApolloAgent()
            with pytest.raises(requests.exceptions.HTTPError):
                agent.search_leads("New York, NY", "Dermatology")
    
    def test_score_leads(self):
        """Test lead scoring functionality."""
        with patch.dict(os.environ, {"APOLLO_API_KEY": "test_key"}):
            agent = ApolloAgent()
            
            leads = [
                Lead(
                    name="John Doe",
                    email="john@example.com",
                    website="https://example.com",
                    company_name="Example Clinic",
                    specialty="Dermatology",
                    location="New York, NY",
                    metadata={"title": "CEO", "employee_count": 15}
                ),
                Lead(
                    name="Jane Smith",
                    email="jane@example.com",
                    website="",  # No website
                    company_name="Smith Medical",
                    specialty="Dermatology",
                    location="New York, NY",
                    metadata={"title": "Manager", "employee_count": 30}
                )
            ]
            
            scored = agent.score_leads(leads)
            
            # First lead should score higher (has website, CEO title, good employee count)
            assert scored[0].metadata["score"] >= scored[1].metadata["score"]
            assert scored[0].name == "John Doe"  # Should be first after sorting
    
    @patch('services.apollo.apollo_agent.requests.post')
    def test_enrich_person_success(self, mock_post, mock_person_enrichment_response):
        """Test successful person enrichment (MOCKED - no credits consumed)."""
        mock_response = MagicMock()
        mock_response.json.return_value = mock_person_enrichment_response
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        with patch.dict(os.environ, {"APOLLO_API_KEY": "test_key"}):
            agent = ApolloAgent()
            person_data = agent.enrich_person(
                email="john@example.com",
                first_name="John",
                last_name="Doe"
            )
        
        assert person_data["email"] == "john@example.com"
        assert person_data["first_name"] == "John"
        assert person_data["title"] == "CEO"
        
        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "people/match" in call_args[0][0]
    
    @patch('services.apollo.apollo_agent.requests.post')
    def test_enrich_organization_success(self, mock_post, mock_organization_enrichment_response):
        """Test successful organization enrichment (MOCKED - no credits consumed)."""
        mock_response = MagicMock()
        mock_response.json.return_value = mock_organization_enrichment_response
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        with patch.dict(os.environ, {"APOLLO_API_KEY": "test_key"}):
            agent = ApolloAgent()
            org_data = agent.enrich_organization(domain="example.com")
        
        assert org_data["name"] == "Example Clinic"
        assert org_data["website_url"] == "https://example.com"
        
        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "organizations/enrich" in call_args[0][0]
    
    @patch('services.apollo.apollo_agent.requests.post')
    def test_bulk_enrich_people(self, mock_post):
        """Test bulk people enrichment (MOCKED - no credits consumed)."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "people": [
                {"email": "john@example.com", "first_name": "John"},
                {"email": "jane@example.com", "first_name": "Jane"}
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        with patch.dict(os.environ, {"APOLLO_API_KEY": "test_key"}):
            agent = ApolloAgent()
            people_data = agent.bulk_enrich_people([
                {"email": "john@example.com"},
                {"email": "jane@example.com"}
            ])
        
        assert len(people_data) == 2
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "people/bulk_match" in call_args[0][0]
    
    @patch('services.apollo.apollo_agent.requests.post')
    def test_bulk_enrich_organizations(self, mock_post):
        """Test bulk organization enrichment (MOCKED - no credits consumed)."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "organizations": [
                {"domain": "example.com", "name": "Example Clinic"},
                {"domain": "smith.com", "name": "Smith Medical"}
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        with patch.dict(os.environ, {"APOLLO_API_KEY": "test_key"}):
            agent = ApolloAgent()
            orgs_data = agent.bulk_enrich_organizations([
                {"domain": "example.com"},
                {"domain": "smith.com"}
            ])
        
        assert len(orgs_data) == 2
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "organizations/bulk_enrich" in call_args[0][0]
    
    @patch('services.apollo.apollo_agent.ApolloAgent.enrich_person')
    @patch('services.apollo.apollo_agent.ApolloAgent.enrich_organization')
    def test_enrich_lead(self, mock_enrich_org, mock_enrich_person):
        """Test lead enrichment convenience method (MOCKED - no credits consumed)."""
        mock_enrich_person.return_value = {
            "email": "john@example.com",
            "updated_at": "2024-01-01T00:00:00Z"
        }
        mock_enrich_org.return_value = {
            "name": "Example Clinic",
            "updated_at": "2024-01-01T00:00:00Z"
        }
        
        with patch.dict(os.environ, {"APOLLO_API_KEY": "test_key"}):
            agent = ApolloAgent()
            lead = Lead(
                name="John Doe",
                email="john@example.com",
                website="https://example.com",
                company_name="Example Clinic",
                specialty="Dermatology",
                location="New York, NY",
                metadata={}
            )
            
            enriched = agent.enrich_lead(lead)
            
            assert "enriched_person" in enriched.metadata
            assert "enriched_organization" in enriched.metadata
            mock_enrich_person.assert_called_once()
            mock_enrich_org.assert_called_once()


@pytest.mark.integration
class TestApolloIntegration:
    """Integration tests that require a real API key (optional)."""
    
    @pytest.fixture(autouse=True)
    def check_api_key(self):
        """Skip integration tests if API key is not available."""
        api_key = os.getenv("APOLLO_API_KEY")
        if not api_key:
            pytest.skip("APOLLO_API_KEY not set - skipping integration test")
    
    def test_search_leads_integration(self):
        """Integration test for lead search (REQUIRES API KEY - may consume credits)."""
        agent = ApolloAgent()
        leads = agent.search_leads(
            geography="New York, NY",
            specialty="Dermatology",
            limit=2
        )
        
        # If API key is valid, we should get results or an empty list
        assert isinstance(leads, list)
        if leads:
            assert isinstance(leads[0], Lead)
            assert hasattr(leads[0], 'email')
            assert hasattr(leads[0], 'name')



