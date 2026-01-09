"""
Integration tests for Apollo.io API.
Extends existing tests with additional integration-focused test cases.
All API calls are mocked to avoid credit consumption.
"""
import pytest
import os
from unittest.mock import patch, MagicMock
import requests
from services.apollo import ApolloAgent
from services.apollo.apollo_agent import Lead
from tests.fixtures.api_responses import ApolloResponseFixtures
from tests.utils.mock_helpers import (
    create_mock_response,
    create_apollo_error_response,
    build_apollo_search_params,
)


class TestApolloIntegration:
    """Integration test suite for ApolloAgent class."""
    
    @pytest.fixture
    def apollo_agent(self):
        """Create ApolloAgent instance with mocked API key."""
        with patch.dict(os.environ, {"APOLLO_API_KEY": "test_api_key_123"}):
            return ApolloAgent()
    
    @patch("services.apollo.apollo_agent.requests.post")
    def test_search_leads_with_various_filters(self, mock_post, apollo_agent):
        """Test lead search with different filter combinations."""
        mock_response = create_mock_response(
            status_code=200,
            json_data=ApolloResponseFixtures.get_search_response(limit=3),
        )
        mock_post.return_value = mock_response
        
        # Test with different employee ranges
        leads = apollo_agent.search_leads(
            geography="Los Angeles, CA",
            specialty="Cardiology",
            min_employees=10,
            max_employees=30,
            limit=3,
        )
        
        assert len(leads) == 3
        call_args = mock_post.call_args
        params = call_args[1]["json"]
        assert params["organization_num_employees_ranges"] == ["10,30"]
        assert params["q_keywords"] == "Cardiology"
        assert params["person_locations"] == ["Los Angeles, CA"]
    
    @patch("services.apollo.apollo_agent.requests.post")
    def test_search_leads_without_website_requirement(self, mock_post, apollo_agent):
        """Test search when website is not required."""
        response_data = ApolloResponseFixtures.get_search_response(limit=2)
        # Add a lead without website
        response_data["people"].append(
            {
                "first_name": "No",
                "last_name": "Website",
                "email": "noweb@example.com",
                "organization": {"name": "No Website Co", "website_url": ""},
            }
        )
        
        mock_response = create_mock_response(status_code=200, json_data=response_data)
        mock_post.return_value = mock_response
        
        leads = apollo_agent.search_leads(
            geography="New York, NY",
            specialty="Dermatology",
            has_website=False,
            limit=10,
        )
        
        # Should include lead without website when has_website=False
        assert len(leads) >= 2
    
    @patch("services.apollo.apollo_agent.requests.post")
    def test_search_leads_rate_limit_429(self, mock_post, apollo_agent):
        """Test handling of 429 rate limit error."""
        error = create_apollo_error_response(429, "Rate limit exceeded")
        mock_post.side_effect = error
        
        with pytest.raises(requests.exceptions.HTTPError):
            apollo_agent.search_leads(
                geography="New York, NY", specialty="Dermatology"
            )
    
    @patch("services.apollo.apollo_agent.requests.post")
    def test_enrich_person_credit_consumption(self, mock_post, apollo_agent):
        """Test that person enrichment consumes 1 credit per call."""
        mock_response = create_mock_response(
            status_code=200,
            json_data=ApolloResponseFixtures.get_person_enrichment_response(
                "test@example.com"
            ),
        )
        mock_post.return_value = mock_response
        
        # Enrich 3 people (should consume 3 credits)
        for i in range(3):
            apollo_agent.enrich_person(email=f"person{i}@example.com")
        
        assert mock_post.call_count == 3
        # All calls should be to people/match endpoint
        for call in mock_post.call_args_list:
            assert "people/match" in call[0][0]
    
    @patch("services.apollo.apollo_agent.requests.post")
    def test_enrich_organization_credit_consumption(self, mock_post, apollo_agent):
        """Test that organization enrichment consumes 1 credit per call."""
        mock_response = create_mock_response(
            status_code=200,
            json_data=ApolloResponseFixtures.get_organization_enrichment_response(
                "example.com"
            ),
        )
        mock_post.return_value = mock_response
        
        # Enrich 2 organizations (should consume 2 credits)
        apollo_agent.enrich_organization(domain="example.com")
        apollo_agent.enrich_organization(domain="test.com")
        
        assert mock_post.call_count == 2
        # All calls should be to organizations/enrich endpoint
        for call in mock_post.call_args_list:
            assert "organizations/enrich" in call[0][0]
    
    @patch("services.apollo.apollo_agent.requests.post")
    def test_enrich_lead_full_credit_consumption(self, mock_post, apollo_agent):
        """Test that full lead enrichment consumes 2 credits (1 person + 1 org)."""
        person_response = create_mock_response(
            status_code=200,
            json_data=ApolloResponseFixtures.get_person_enrichment_response(
                "john@example.com"
            ),
        )
        org_response = create_mock_response(
            status_code=200,
            json_data=ApolloResponseFixtures.get_organization_enrichment_response(
                "example.com"
            ),
        )
        mock_post.side_effect = [person_response, org_response]
        
        lead = Lead(
            name="John Doe",
            email="john@example.com",
            website="https://example.com",
            company_name="Example Clinic",
            specialty="Dermatology",
            location="New York, NY",
            metadata={},
        )
        
        enriched = apollo_agent.enrich_lead(lead)
        
        assert "enriched_person" in enriched.metadata
        assert "enriched_organization" in enriched.metadata
        assert mock_post.call_count == 2  # 2 credits consumed
    
    @patch("services.apollo.apollo_agent.requests.post")
    def test_bulk_enrich_people_credit_tracking(self, mock_post, apollo_agent):
        """Test bulk people enrichment credit consumption (1 credit per person)."""
        mock_response = create_mock_response(
            status_code=200,
            json_data={
                "people": [
                    {"email": "person1@example.com"},
                    {"email": "person2@example.com"},
                    {"email": "person3@example.com"},
                ]
            },
        )
        mock_post.return_value = mock_response
        
        people_data = [
            {"email": "person1@example.com"},
            {"email": "person2@example.com"},
            {"email": "person3@example.com"},
        ]
        
        enriched = apollo_agent.bulk_enrich_people(people_data)
        
        assert len(enriched) == 3
        assert mock_post.call_count == 1  # Single bulk call
        # 3 people = 3 credits consumed in one API call
    
    @patch("services.apollo.apollo_agent.requests.post")
    def test_bulk_enrich_organizations_credit_tracking(self, mock_post, apollo_agent):
        """Test bulk organization enrichment credit consumption."""
        mock_response = create_mock_response(
            status_code=200,
            json_data={
                "organizations": [
                    {"domain": "org1.com"},
                    {"domain": "org2.com"},
                ]
            },
        )
        mock_post.return_value = mock_response
        
        orgs_data = [{"domain": "org1.com"}, {"domain": "org2.com"}]
        
        enriched = apollo_agent.bulk_enrich_organizations(orgs_data)
        
        assert len(enriched) == 2
        assert mock_post.call_count == 1  # Single bulk call
        # 2 organizations = 2 credits consumed
    
    def test_score_leads_comprehensive(self, apollo_agent):
        """Test lead scoring with various scenarios."""
        leads = [
            Lead(
                name="High Score",
                email="high@example.com",
                website="https://example.com",
                company_name="Example Clinic",
                specialty="Dermatology",
                location="New York, NY",
                metadata={"title": "Owner", "employee_count": 15},
            ),
            Lead(
                name="Medium Score",
                email="medium@example.com",
                website="https://medium.com",
                company_name="Medium Clinic",
                specialty="Dermatology",
                location="New York, NY",
                metadata={"title": "Manager", "employee_count": 30},
            ),
            Lead(
                name="Low Score",
                email="low@example.com",
                website="",  # No website
                company_name="Low Clinic",
                specialty="Dermatology",
                location="New York, NY",
                metadata={"title": "Staff", "employee_count": 50},
            ),
        ]
        
        scored = apollo_agent.score_leads(leads)
        
        # Verify sorting (highest score first)
        assert scored[0].metadata["score"] >= scored[1].metadata["score"]
        assert scored[1].metadata["score"] >= scored[2].metadata["score"]
        
        # Verify scores are calculated
        assert scored[0].metadata["score"] >= 15  # Website + Owner + Good employees
        assert scored[2].metadata["score"] <= 2  # Only employee count
    
    @patch("services.apollo.apollo_agent.requests.post")
    def test_data_transformation_api_to_lead(self, mock_post, apollo_agent):
        """Test transformation of Apollo API response to Lead objects."""
        api_response = {
            "people": [
                {
                    "id": "person_123",
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john@example.com",
                    "title": "CEO",
                    "linkedin_url": "https://linkedin.com/in/johndoe",
                    "organization": {
                        "id": "org_123",
                        "name": "Example Clinic",
                        "website_url": "https://example.com",
                        "estimated_num_employees": 15,
                    },
                }
            ]
        }
        
        mock_response = create_mock_response(status_code=200, json_data=api_response)
        mock_post.return_value = mock_response
        
        leads = apollo_agent.search_leads(
            geography="New York, NY", specialty="Dermatology", limit=1
        )
        
        assert len(leads) == 1
        lead = leads[0]
        assert lead.name == "John Doe"
        assert lead.email == "john@example.com"
        assert lead.company_name == "Example Clinic"
        assert lead.website == "https://example.com"
        assert lead.metadata["title"] == "CEO"
        assert lead.metadata["employee_count"] == 15
        assert lead.metadata["apollo_organization_id"] == "org_123"
        assert lead.specialty == "Dermatology"
        assert lead.location == "New York, NY"
    
    @patch("services.apollo.apollo_agent.requests.post")
    def test_search_leads_empty_response(self, mock_post, apollo_agent):
        """Test handling of empty search results."""
        mock_response = create_mock_response(
            status_code=200, json_data={"people": []}
        )
        mock_post.return_value = mock_response
        
        leads = apollo_agent.search_leads(
            geography="Nowhere, XX", specialty="NonExistent", limit=10
        )
        
        assert len(leads) == 0
        assert isinstance(leads, list)
    
    @patch("services.apollo.apollo_agent.requests.post")
    def test_enrich_person_partial_data(self, mock_post, apollo_agent):
        """Test person enrichment with partial input data."""
        mock_response = create_mock_response(
            status_code=200,
            json_data=ApolloResponseFixtures.get_person_enrichment_response(
                "test@example.com"
            ),
        )
        mock_post.return_value = mock_response
        
        # Enrich with only email
        person_data = apollo_agent.enrich_person(email="test@example.com")
        
        assert person_data["email"] == "test@example.com"
        call_args = mock_post.call_args
        params = call_args[1]["json"]
        assert params["email"] == "test@example.com"
    
    @patch("services.apollo.apollo_agent.requests.post")
    def test_enrich_organization_by_domain(self, mock_post, apollo_agent):
        """Test organization enrichment using domain."""
        mock_response = create_mock_response(
            status_code=200,
            json_data=ApolloResponseFixtures.get_organization_enrichment_response(
                "example.com"
            ),
        )
        mock_post.return_value = mock_response
        
        org_data = apollo_agent.enrich_organization(domain="example.com")
        
        assert org_data["website_url"] == "https://example.com"
        call_args = mock_post.call_args
        params = call_args[1]["json"]
        assert params["domain"] == "example.com"
    
    @patch("services.apollo.apollo_agent.requests.post")
    def test_enrich_organization_by_name(self, mock_post, apollo_agent):
        """Test organization enrichment using name."""
        mock_response = create_mock_response(
            status_code=200,
            json_data=ApolloResponseFixtures.get_organization_enrichment_response(
                "example.com"
            ),
        )
        mock_post.return_value = mock_response
        
        org_data = apollo_agent.enrich_organization(name="Example Clinic")
        
        assert org_data is not None
        call_args = mock_post.call_args
        params = call_args[1]["json"]
        assert params["name"] == "Example Clinic"

