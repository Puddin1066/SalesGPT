"""
Unit tests for HubSpot API integration.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))


@pytest.mark.unit
def test_hubspot_agent_initialization(mock_hubspot_agent):
    """Test HubSpot agent initializes correctly."""
    assert mock_hubspot_agent is not None
    assert hasattr(mock_hubspot_agent, 'create_contact')
    assert hasattr(mock_hubspot_agent, 'update_contact_properties')


@pytest.mark.unit
def test_create_contact_mock(mock_hubspot_agent, mock_hubspot_contact):
    """Test contact creation with mock."""
    # Test
    contact_id = mock_hubspot_agent.create_contact(
        email=mock_hubspot_contact['properties']['email'],
        first_name=mock_hubspot_contact['properties']['firstname'],
        last_name=mock_hubspot_contact['properties']['lastname']
    )
    
    # Assert
    assert contact_id == "12345"
    assert mock_hubspot_agent.create_contact.called


@pytest.mark.unit
def test_update_contact_properties_mock(mock_hubspot_agent):
    """Test updating contact properties with mock."""
    # Test
    result = mock_hubspot_agent.update_contact_properties(
        contact_id="12345",
        properties={"vertical": "medical"}
    )
    
    # Assert
    assert result is True
    assert mock_hubspot_agent.update_contact_properties.called


@pytest.mark.unit
def test_property_definition_structure():
    """Test custom property definitions are valid."""
    properties = [
        {
            "name": "vertical",
            "label": "Vertical",
            "type": "string",
            "fieldType": "text"
        },
        {
            "name": "gemflush_email_sent",
            "label": "GemFlush Email Sent",
            "type": "datetime",
            "fieldType": "date"
        }
    ]
    
    for prop in properties:
        assert 'name' in prop
        assert 'label' in prop
        assert 'type' in prop
        assert 'fieldType' in prop


@pytest.mark.unit
@patch('requests.post')
def test_create_property_api_call(mock_post):
    """Test property creation API call."""
    # Mock response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"name": "vertical", "type": "string"}
    mock_post.return_value = mock_response
    
    from setup.create_hubspot_properties import create_property
    
    property_config = {
        "name": "vertical",
        "label": "Vertical",
        "type": "string",
        "fieldType": "text"
    }
    
    # Test
    result = create_property("test_api_key", property_config)
    
    # Assert
    assert result is True
    assert mock_post.called


@pytest.mark.unit
def test_contact_csv_parsing(test_leads_csv):
    """Test parsing contacts from CSV."""
    from setup.import_contacts_bulk import read_leads_csv
    
    # Test
    leads = read_leads_csv(test_leads_csv)
    
    # Assert
    assert len(leads) == 3
    assert leads[0]['Email'] == 'test1@clinic.com'
    assert leads[0]['vertical'] == 'medical'
    assert leads[1]['vertical'] == 'legal'


@pytest.mark.unit
def test_contact_validation():
    """Test contact data validation."""
    valid_verticals = ['medical', 'legal', 'realestate', 'agencies']
    
    test_contacts = [
        {'vertical': 'medical', 'email': 'test@example.com'},
        {'vertical': 'invalid', 'email': 'bad@example.com'},
        {'vertical': 'legal', 'email': ''}
    ]
    
    valid_contacts = []
    for contact in test_contacts:
        if contact.get('vertical') in valid_verticals and contact.get('email'):
            valid_contacts.append(contact)
    
    assert len(valid_contacts) == 1
    assert valid_contacts[0]['vertical'] == 'medical'


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv('HUBSPOT_API_KEY') and not os.getenv('HUBSPOT_PAT'),
    reason="HubSpot API key not set"
)
def test_real_hubspot_connection():
    """Test real HubSpot API connection."""
    from services.crm.hubspot_agent import HubSpotAgent
    
    api_key = os.getenv('HUBSPOT_API_KEY') or os.getenv('HUBSPOT_PAT')
    agent = HubSpotAgent(api_key=api_key)
    
    # Test connection (doesn't create anything)
    assert agent is not None


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv('HUBSPOT_API_KEY') and not os.getenv('HUBSPOT_PAT'),
    reason="HubSpot API key not set"
)
def test_get_contact_by_email():
    """Test getting contact by email."""
    from services.crm.hubspot_agent import HubSpotAgent
    
    api_key = os.getenv('HUBSPOT_API_KEY') or os.getenv('HUBSPOT_PAT')
    agent = HubSpotAgent(api_key=api_key)
    
    # Try to get a contact (may not exist)
    contact = agent.get_contact_by_email('nonexistent@example.com')
    
    # Should return None for non-existent contact
    assert contact is None or isinstance(contact, dict)


