"""
Integration flow tests for Apollo → HubSpot pipeline.
Tests the complete data flow from Apollo lead search to HubSpot contact creation.
"""
import pytest
import os
from unittest.mock import patch, MagicMock
from services.apollo import ApolloAgent
from services.crm import HubSpotAgent
from services.apollo.apollo_agent import Lead
from tests.fixtures.hubspot_responses import mock_contact_response
from tests.utils.mock_helpers import create_mock_response, build_apollo_search_params


class TestApolloHubSpotFlow:
    """Test suite for Apollo → HubSpot integration flow."""
    
    @pytest.fixture
    def mock_apollo_search_response(self):
        """Mock Apollo search response."""
        return {
            "people": [
                {
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john@example.com",
                    "title": "Owner",
                    "linkedin_url": "https://linkedin.com/in/johndoe",
                    "organization": {
                        "id": "org_123",
                        "name": "Example Clinic",
                        "website_url": "https://example.com",
                        "estimated_num_employees": 15,
                        "primary_phone": "555-1234",
                    },
                },
                {
                    "first_name": "Jane",
                    "last_name": "Smith",
                    "email": "jane@clinic.com",
                    "title": "Medical Director",
                    "linkedin_url": "https://linkedin.com/in/janesmith",
                    "organization": {
                        "id": "org_456",
                        "name": "Smith Medical Center",
                        "website_url": "https://smithmedical.com",
                        "estimated_num_employees": 25,
                        "primary_phone": "555-5678",
                    },
                },
            ]
        }
    
    @patch("services.crm.hubspot_agent.requests.request")
    @patch("services.apollo.apollo_agent.requests.post")
    def test_apollo_to_hubspot_flow_success(
        self, mock_apollo_post, mock_hubspot_request, mock_apollo_search_response
    ):
        """Test complete flow: Apollo search → HubSpot contact creation."""
        # Mock Apollo search response
        apollo_response = create_mock_response(
            status_code=200, json_data=mock_apollo_search_response
        )
        mock_apollo_post.return_value = apollo_response
        
        # Mock HubSpot contact creation responses
        hubspot_responses = [
            create_mock_response(
                status_code=201, json_data=mock_contact_response("contact_123")
            ),
            create_mock_response(
                status_code=201, json_data=mock_contact_response("contact_456")
            ),
        ]
        mock_hubspot_request.side_effect = hubspot_responses
        
        with patch.dict(
            os.environ,
            {
                "APOLLO_API_KEY": "test_apollo_key",
                "HUBSPOT_API_KEY": "test_hubspot_key",
            },
        ):
            # Step 1: Search leads in Apollo
            apollo = ApolloAgent()
            leads = apollo.search_leads(
                geography="New York, NY",
                specialty="Dermatology",
                limit=2,
            )
            
            assert len(leads) == 2
            assert leads[0].email == "john@example.com"
            assert leads[1].email == "jane@clinic.com"
            
            # Step 2: Score leads
            scored_leads = apollo.score_leads(leads)
            assert len(scored_leads) == 2
            
            # Step 3: Create contacts in HubSpot
            hubspot = HubSpotAgent()
            contact_ids = []
            for lead in scored_leads:
                contact_id = hubspot.create_contact(
                    email=lead.email,
                    first_name=lead.name.split()[0] if lead.name else "",
                    last_name=" ".join(lead.name.split()[1:])
                    if len(lead.name.split()) > 1
                    else "",
                    company=lead.company_name,
                    website=lead.website,
                )
                if contact_id:
                    contact_ids.append(contact_id)
            
            assert len(contact_ids) == 2
            assert "contact_123" in contact_ids
            assert "contact_456" in contact_ids
            
            # Verify API calls
            mock_apollo_post.assert_called_once()
            assert mock_hubspot_request.call_count == 2
    
    @patch("services.crm.hubspot_agent.requests.request")
    @patch("services.apollo.apollo_agent.requests.post")
    def test_apollo_to_hubspot_data_transformation(
        self, mock_apollo_post, mock_hubspot_request, mock_apollo_search_response
    ):
        """Test data transformation between Apollo and HubSpot."""
        apollo_response = create_mock_response(
            status_code=200, json_data=mock_apollo_search_response
        )
        mock_apollo_post.return_value = apollo_response
        
        hubspot_response = create_mock_response(
            status_code=201, json_data=mock_contact_response("contact_123")
        )
        mock_hubspot_request.return_value = hubspot_response
        
        with patch.dict(
            os.environ,
            {
                "APOLLO_API_KEY": "test_apollo_key",
                "HUBSPOT_API_KEY": "test_hubspot_key",
            },
        ):
            apollo = ApolloAgent()
            leads = apollo.search_leads(
                geography="New York, NY", specialty="Dermatology", limit=1
            )
            
            lead = leads[0]
            hubspot = HubSpotAgent()
            contact_id = hubspot.create_contact(
                email=lead.email,
                first_name=lead.name.split()[0],
                last_name=" ".join(lead.name.split()[1:]) if len(lead.name.split()) > 1 else "",
                company=lead.company_name,
                website=lead.website,
            )
            
            # Verify data transformation
            assert contact_id == "contact_123"
            hubspot_call = mock_hubspot_request.call_args
            payload = hubspot_call[1]["json"]
            assert payload["properties"]["email"] == lead.email
            assert payload["properties"]["company"] == lead.company_name
            assert payload["properties"]["website"] == lead.website
    
    @patch("services.crm.hubspot_agent.requests.request")
    @patch("services.apollo.apollo_agent.requests.post")
    def test_apollo_to_hubspot_error_propagation(
        self, mock_apollo_post, mock_hubspot_request
    ):
        """Test error handling when HubSpot fails after Apollo succeeds."""
        # Apollo succeeds
        apollo_response = create_mock_response(
            status_code=200,
            json_data={
                "people": [
                    {
                        "first_name": "John",
                        "last_name": "Doe",
                        "email": "john@example.com",
                        "organization": {
                            "name": "Example Clinic",
                            "website_url": "https://example.com",
                        },
                    }
                ]
            },
        )
        mock_apollo_post.return_value = apollo_response
        
        # HubSpot fails
        import requests
        error_response = MagicMock()
        error_response.status_code = 401
        error_response.text = "Unauthorized"
        error_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=error_response
        )
        mock_hubspot_request.return_value = error_response
        
        with patch.dict(
            os.environ,
            {
                "APOLLO_API_KEY": "test_apollo_key",
                "HUBSPOT_API_KEY": "invalid_key",
            },
        ):
            apollo = ApolloAgent()
            leads = apollo.search_leads(
                geography="New York, NY", specialty="Dermatology", limit=1
            )
            
            assert len(leads) == 1
            
            hubspot = HubSpotAgent()
            contact_id = hubspot.create_contact(
                email=leads[0].email,
                first_name="John",
                last_name="Doe",
                company=leads[0].company_name,
            )
            
            # HubSpot should return None on error
            assert contact_id is None
    
    @patch("services.crm.hubspot_agent.requests.request")
    @patch("services.apollo.apollo_agent.requests.post")
    def test_pipeline_stage_update_flow(
        self, mock_apollo_post, mock_hubspot_request, mock_apollo_search_response
    ):
        """Test updating HubSpot pipeline stage based on lead data."""
        # Apollo search
        apollo_response = create_mock_response(
            status_code=200, json_data=mock_apollo_search_response
        )
        mock_apollo_post.return_value = apollo_response
        
        # HubSpot contact creation
        contact_response = create_mock_response(
            status_code=201, json_data=mock_contact_response("contact_123")
        )
        # HubSpot stage update
        stage_response = create_mock_response(
            status_code=200,
            json_data={"id": "contact_123", "properties": {"dealstage": "engaged"}},
        )
        mock_hubspot_request.side_effect = [contact_response, stage_response]
        
        with patch.dict(
            os.environ,
            {
                "APOLLO_API_KEY": "test_apollo_key",
                "HUBSPOT_API_KEY": "test_hubspot_key",
            },
        ):
            apollo = ApolloAgent()
            leads = apollo.search_leads(
                geography="New York, NY", specialty="Dermatology", limit=1
            )
            
            hubspot = HubSpotAgent()
            contact_id = hubspot.create_contact(
                email=leads[0].email,
                first_name=leads[0].name.split()[0],
                last_name=" ".join(leads[0].name.split()[1:])
                if len(leads[0].name.split()) > 1
                else "",
                company=leads[0].company_name,
            )
            
            # Update pipeline stage
            if contact_id:
                success = hubspot.update_pipeline_stage(contact_id, "engaged")
                assert success is True
            
            # Verify both calls were made
            assert mock_hubspot_request.call_count == 2

