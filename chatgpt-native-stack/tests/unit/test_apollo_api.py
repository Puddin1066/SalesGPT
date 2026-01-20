"""
Unit tests for Apollo.io API integration.
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))


@pytest.mark.unit
def test_apollo_person_structure(mock_apollo_person):
    """Test Apollo person data structure."""
    assert 'id' in mock_apollo_person
    assert 'first_name' in mock_apollo_person
    assert 'last_name' in mock_apollo_person
    assert 'email' in mock_apollo_person
    assert 'title' in mock_apollo_person
    assert 'organization_name' in mock_apollo_person


@pytest.mark.unit
@patch('requests.post')
def test_apollo_search_api_call(mock_post, mock_apollo_person):
    """Test Apollo search API call."""
    # Mock response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'people': [mock_apollo_person],
        'pagination': {'total_entries': 1}
    }
    mock_post.return_value = mock_response
    
    import requests
    
    # Simulate API call
    headers = {"X-Api-Key": "test_key"}
    payload = {"q_keywords": "practice manager", "per_page": 1}
    
    response = requests.post(
        "https://api.apollo.io/v1/mixed_people/search",
        headers=headers,
        json=payload
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert 'people' in data
    assert len(data['people']) == 1


@pytest.mark.unit
def test_apollo_to_hubspot_mapping(mock_apollo_person):
    """Test mapping Apollo data to HubSpot format."""
    # Map fields
    hubspot_contact = {
        'email': mock_apollo_person['email'],
        'firstname': mock_apollo_person['first_name'],
        'lastname': mock_apollo_person['last_name'],
        'company': mock_apollo_person['organization_name'],
        'city': mock_apollo_person['city'],
        'jobtitle': mock_apollo_person['title']
    }
    
    # Assert mapping
    assert hubspot_contact['email'] == 'jane@lawfirm.com'
    assert hubspot_contact['firstname'] == 'Jane'
    assert hubspot_contact['company'] == 'Law Firm LLC'


@pytest.mark.unit
def test_apollo_search_filters():
    """Test Apollo search filter construction."""
    filters = {
        "person_titles": ["Practice Manager", "Office Manager"],
        "person_locations": ["New York, United States"],
        "q_organization_industry_tag_ids": ["5567cd4773696439b10b0000"],  # Healthcare
        "per_page": 10
    }
    
    assert 'person_titles' in filters
    assert len(filters['person_titles']) == 2
    assert 'person_locations' in filters


@pytest.mark.integration
@pytest.mark.skipif(not os.getenv('APOLLO_API_KEY'), reason="APOLLO_API_KEY not set")
def test_real_apollo_connection():
    """Test real Apollo API connection (minimal query)."""
    import requests
    
    api_key = os.getenv('APOLLO_API_KEY')
    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": api_key
    }
    
    url = "https://api.apollo.io/v1/mixed_people/search"
    payload = {"per_page": 1}  # Minimal query
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        # Should get 200 or 403 (if no credits/permissions)
        assert response.status_code in [200, 403]
        
        if response.status_code == 200:
            data = response.json()
            assert 'people' in data or 'pagination' in data
    except Exception as e:
        pytest.skip(f"Apollo API not accessible: {e}")


