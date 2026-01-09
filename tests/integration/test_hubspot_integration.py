"""
Integration tests for HubSpot API.
All API calls are mocked to avoid actual API usage.
"""
import pytest
import os
from unittest.mock import patch, MagicMock
import requests
from services.crm import HubSpotAgent
from tests.fixtures.hubspot_responses import (
    mock_contact_response,
    mock_deal_response,
    mock_oauth_token_response,
    mock_oauth_token_metadata,
    mock_401_error,
    mock_403_error,
    mock_404_error,
    mock_rate_limit_error,
)
from tests.utils.mock_helpers import (
    create_mock_response,
    create_hubspot_error_response,
    build_hubspot_contact_payload,
)


class TestHubSpotAgent:
    """Test suite for HubSpotAgent class."""
    
    def test_initialization_with_api_key(self):
        """Test HubSpotAgent initialization with Private App token."""
        with patch.dict(os.environ, {"HUBSPOT_API_KEY": "test_token_123"}):
            agent = HubSpotAgent()
            assert agent.api_key == "test_token_123"
            assert agent.base_url == "https://api.hubapi.com"
            assert agent.use_oauth is False
            assert "Bearer test_token_123" in agent.headers["Authorization"]
    
    def test_initialization_with_oauth(self):
        """Test HubSpotAgent initialization with OAuth credentials."""
        with patch.dict(
            os.environ,
            {
                "HUBSPOT_CLIENT_ID": "client_123",
                "HUBSPOT_CLIENT_SECRET": "secret_123",
                "HUBSPOT_REFRESH_TOKEN": "refresh_123",
            },
        ), patch.object(HubSpotAgent, "_refresh_access_token", return_value=True):
            agent = HubSpotAgent()
            assert agent.use_oauth is True
            assert agent.client_id == "client_123"
            assert agent.client_secret == "secret_123"
            assert agent.refresh_token == "refresh_123"
    
    def test_initialization_without_credentials(self):
        """Test HubSpotAgent initialization fails without credentials."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="HubSpot authentication not configured"):
                HubSpotAgent()
    
    @patch("services.crm.hubspot_agent.requests.request")
    def test_create_contact_success(self, mock_request):
        """Test successful contact creation."""
        mock_response = create_mock_response(
            status_code=201, json_data=mock_contact_response("contact_456")
        )
        mock_request.return_value = mock_response
        
        with patch.dict(os.environ, {"HUBSPOT_API_KEY": "test_token"}):
            agent = HubSpotAgent()
            contact_id = agent.create_contact(
                email="john@example.com",
                first_name="John",
                last_name="Doe",
                company="Example Clinic",
                website="https://example.com",
            )
        
        assert contact_id == "contact_456"
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][0] == "POST"
        assert "crm/v3/objects/contacts" in call_args[0][1]
        assert call_args[1]["json"]["properties"]["email"] == "john@example.com"
    
    @patch("services.crm.hubspot_agent.requests.request")
    def test_create_contact_minimal_data(self, mock_request):
        """Test contact creation with minimal required data."""
        mock_response = create_mock_response(
            status_code=201, json_data=mock_contact_response("contact_789")
        )
        mock_request.return_value = mock_response
        
        with patch.dict(os.environ, {"HUBSPOT_API_KEY": "test_token"}):
            agent = HubSpotAgent()
            contact_id = agent.create_contact(
                email="jane@example.com",
                first_name="Jane",
                last_name="Smith",
            )
        
        assert contact_id == "contact_789"
        payload = mock_request.call_args[1]["json"]
        assert "company" not in payload["properties"]
        assert "website" not in payload["properties"]
    
    @patch("services.crm.hubspot_agent.requests.request")
    def test_create_contact_api_error(self, mock_request):
        """Test contact creation with API error."""
        error = create_hubspot_error_response(400, "Invalid email format")
        mock_request.side_effect = error
        
        with patch.dict(os.environ, {"HUBSPOT_API_KEY": "test_token"}):
            agent = HubSpotAgent()
            contact_id = agent.create_contact(
                email="invalid-email",
                first_name="Test",
                last_name="User",
            )
        
        assert contact_id is None
    
    @patch("services.crm.hubspot_agent.requests.request")
    def test_update_pipeline_stage_idle(self, mock_request):
        """Test updating pipeline stage to idle."""
        mock_response = create_mock_response(
            status_code=200,
            json_data={"id": "contact_123", "properties": {"dealstage": "idle"}},
        )
        mock_request.return_value = mock_response
        
        with patch.dict(os.environ, {"HUBSPOT_API_KEY": "test_token"}):
            agent = HubSpotAgent()
            success = agent.update_pipeline_stage("contact_123", "idle")
        
        assert success is True
        call_args = mock_request.call_args
        assert call_args[0][0] == "PATCH"
        assert "crm/v3/objects/contacts/contact_123" in call_args[0][1]
        assert call_args[1]["json"]["properties"]["dealstage"] == "idle"
    
    @patch("services.crm.hubspot_agent.requests.request")
    def test_update_pipeline_stage_booked(self, mock_request):
        """Test updating pipeline stage to booked."""
        mock_response = create_mock_response(
            status_code=200,
            json_data={"id": "contact_123", "properties": {"dealstage": "booked"}},
        )
        mock_request.return_value = mock_response
        
        with patch.dict(os.environ, {"HUBSPOT_API_KEY": "test_token"}):
            agent = HubSpotAgent()
            success = agent.update_pipeline_stage("contact_123", "booked")
        
        assert success is True
        payload = mock_request.call_args[1]["json"]
        assert payload["properties"]["dealstage"] == "booked"
    
    def test_update_pipeline_stage_invalid(self):
        """Test updating pipeline stage with invalid stage."""
        with patch.dict(os.environ, {"HUBSPOT_API_KEY": "test_token"}):
            agent = HubSpotAgent()
            with pytest.raises(ValueError, match="Invalid stage"):
                agent.update_pipeline_stage("contact_123", "invalid_stage")
    
    @patch("services.crm.hubspot_agent.requests.request")
    def test_create_deal_success(self, mock_request):
        """Test successful deal creation."""
        mock_response = create_mock_response(
            status_code=201, json_data=mock_deal_response("deal_456")
        )
        mock_request.return_value = mock_response
        
        with patch.dict(os.environ, {"HUBSPOT_API_KEY": "test_token"}):
            agent = HubSpotAgent()
            deal_id = agent.create_deal(
                contact_id="contact_123",
                deal_name="Example Clinic Deal",
                amount=10000.0,
                stage="idle",
            )
        
        assert deal_id == "deal_456"
        call_args = mock_request.call_args
        assert call_args[0][0] == "POST"
        assert "crm/v3/objects/deals" in call_args[0][1]
        payload = call_args[1]["json"]
        assert payload["properties"]["dealname"] == "Example Clinic Deal"
        assert payload["properties"]["amount"] == "10000.0"
        assert len(payload["associations"]) > 0
    
    @patch("services.crm.hubspot_agent.requests.request")
    def test_get_contact_by_email_found(self, mock_request):
        """Test getting contact by email when contact exists."""
        mock_response = create_mock_response(
            status_code=200, json_data=mock_contact_response("contact_123")
        )
        mock_request.return_value = mock_response
        
        with patch.dict(os.environ, {"HUBSPOT_API_KEY": "test_token"}):
            agent = HubSpotAgent()
            contact = agent.get_contact_by_email("john@example.com")
        
        assert contact is not None
        assert contact["id"] == "contact_123"
        call_args = mock_request.call_args
        assert call_args[0][0] == "GET"
        assert "crm/v3/objects/contacts/john@example.com" in call_args[0][1]
        assert call_args[1]["params"]["idProperty"] == "email"
    
    @patch("services.crm.hubspot_agent.requests.request")
    def test_get_contact_by_email_not_found(self, mock_request):
        """Test getting contact by email when contact doesn't exist."""
        error = create_hubspot_error_response(404, "Resource not found")
        mock_request.side_effect = error
        
        with patch.dict(os.environ, {"HUBSPOT_API_KEY": "test_token"}):
            agent = HubSpotAgent()
            contact = agent.get_contact_by_email("nonexistent@example.com")
        
        assert contact is None
    
    @patch("services.crm.hubspot_agent.requests.post")
    def test_oauth_token_refresh_success(self, mock_post):
        """Test successful OAuth token refresh."""
        mock_response = create_mock_response(
            status_code=200, json_data=mock_oauth_token_response()
        )
        mock_post.return_value = mock_response
        
        with patch.dict(
            os.environ,
            {
                "HUBSPOT_CLIENT_ID": "client_123",
                "HUBSPOT_CLIENT_SECRET": "secret_123",
                "HUBSPOT_REFRESH_TOKEN": "refresh_123",
            },
        ):
            agent = HubSpotAgent()
            # Agent initialization calls _refresh_access_token() once
            # Now call it again manually
            success = agent._refresh_access_token()
        
        assert success is True
        assert agent.access_token == "new_access_token_123"
        # Should be called twice: once during init, once manually
        assert mock_post.call_count == 2
        # Check the last call (manual refresh)
        call_data = mock_post.call_args[1]["data"]
        assert call_data["grant_type"] == "refresh_token"
        assert call_data["refresh_token"] in ["refresh_123", "new_refresh_token_123"]
    
    @patch("services.crm.hubspot_agent.requests.post")
    def test_oauth_token_refresh_failure(self, mock_post):
        """Test OAuth token refresh failure."""
        error = create_hubspot_error_response(401, "Invalid refresh token")
        mock_post.side_effect = error
        
        with patch.dict(
            os.environ,
            {
                "HUBSPOT_CLIENT_ID": "client_123",
                "HUBSPOT_CLIENT_SECRET": "secret_123",
                "HUBSPOT_REFRESH_TOKEN": "invalid_refresh",
            },
        ):
            agent = HubSpotAgent()
            success = agent._refresh_access_token()
        
        assert success is False
    
    @patch("services.crm.hubspot_agent.requests.request")
    @patch("services.crm.hubspot_agent.requests.post")
    def test_oauth_token_refresh_on_401(self, mock_post, mock_request):
        """Test automatic token refresh on 401 error."""
        # Token refresh response (used during init and on 401)
        token_response = create_mock_response(
            status_code=200, json_data=mock_oauth_token_response()
        )
        # First request fails with 401
        error_response = create_mock_response(status_code=401)
        # Retry succeeds
        success_response = create_mock_response(
            status_code=200, json_data=mock_contact_response()
        )
        
        # Init calls refresh once, then 401 triggers another refresh
        mock_post.return_value = token_response
        mock_request.side_effect = [error_response, success_response]
        
        with patch.dict(
            os.environ,
            {
                "HUBSPOT_CLIENT_ID": "client_123",
                "HUBSPOT_CLIENT_SECRET": "secret_123",
                "HUBSPOT_REFRESH_TOKEN": "refresh_123",
            },
        ):
            agent = HubSpotAgent()
            # This should trigger token refresh and retry
            contact_id = agent.create_contact(
                email="test@example.com",
                first_name="Test",
                last_name="User",
            )
        
        assert contact_id == "contact_123"
        # Token refresh called twice: once during init, once on 401
        assert mock_post.call_count == 2
        assert mock_request.call_count == 2  # Initial + retry
    
    @patch("services.crm.hubspot_agent.requests.request")
    def test_401_unauthorized_error(self, mock_request):
        """Test handling of 401 Unauthorized error."""
        error = create_hubspot_error_response(401, "Authentication credentials not found")
        mock_request.side_effect = error
        
        with patch.dict(os.environ, {"HUBSPOT_API_KEY": "invalid_token"}):
            agent = HubSpotAgent()
            contact_id = agent.create_contact(
                email="test@example.com",
                first_name="Test",
                last_name="User",
            )
        
        assert contact_id is None
    
    @patch("services.crm.hubspot_agent.requests.request")
    def test_403_forbidden_error(self, mock_request):
        """Test handling of 403 Forbidden error."""
        error = create_hubspot_error_response(403, "Insufficient permissions")
        mock_request.side_effect = error
        
        with patch.dict(os.environ, {"HUBSPOT_API_KEY": "test_token"}):
            agent = HubSpotAgent()
            contact_id = agent.create_contact(
                email="test@example.com",
                first_name="Test",
                last_name="User",
            )
        
        assert contact_id is None
    
    @patch("services.crm.hubspot_agent.requests.request")
    def test_404_not_found_error(self, mock_request):
        """Test handling of 404 Not Found error."""
        error = create_hubspot_error_response(404, "Resource not found")
        mock_request.side_effect = error
        
        with patch.dict(os.environ, {"HUBSPOT_API_KEY": "test_token"}):
            agent = HubSpotAgent()
            success = agent.update_pipeline_stage("nonexistent_contact", "booked")
        
        assert success is False
    
    @patch("services.crm.hubspot_agent.requests.get")
    def test_get_token_metadata(self, mock_get):
        """Test retrieving OAuth token metadata."""
        mock_response = create_mock_response(
            status_code=200, json_data=mock_oauth_token_metadata()
        )
        mock_get.return_value = mock_response
        
        with patch.dict(
            os.environ,
            {
                "HUBSPOT_CLIENT_ID": "client_123",
                "HUBSPOT_CLIENT_SECRET": "secret_123",
                "HUBSPOT_REFRESH_TOKEN": "refresh_123",
            },
        ), patch.object(HubSpotAgent, "_refresh_access_token", return_value=True):
            agent = HubSpotAgent()
            agent.access_token = "access_token_123"
            metadata = agent.get_token_metadata()
        
        assert metadata is not None
        assert metadata["user"] == "user@example.com"
        assert metadata["hub_id"] == 123456
        assert "crm.objects.contacts.read" in metadata["scopes"]
    
    @patch("services.crm.hubspot_agent.requests.post")
    def test_generate_initial_tokens(self, mock_post):
        """Test generating initial OAuth tokens from authorization code."""
        mock_response = create_mock_response(
            status_code=200, json_data=mock_oauth_token_response()
        )
        mock_post.return_value = mock_response
        
        tokens = HubSpotAgent.generate_initial_tokens(
            client_id="client_123",
            client_secret="secret_123",
            authorization_code="auth_code_123",
            redirect_uri="https://example.com/callback",
        )
        
        assert tokens is not None
        assert tokens["access_token"] == "new_access_token_123"
        assert tokens["refresh_token"] == "new_refresh_token_123"
        mock_post.assert_called_once()
        call_data = mock_post.call_args[1]["data"]
        assert call_data["grant_type"] == "authorization_code"
        assert call_data["code"] == "auth_code_123"

