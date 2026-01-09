"""
Helper functions for creating mocks in tests.
Response builders and error simulators.
"""
from unittest.mock import MagicMock
import requests
from typing import Dict, Any, Optional


def create_mock_response(
    status_code: int = 200,
    json_data: Optional[Dict[str, Any]] = None,
    text: str = "",
    headers: Optional[Dict[str, str]] = None,
) -> MagicMock:
    """
    Create a mock HTTP response object.
    
    Args:
        status_code: HTTP status code
        json_data: JSON response data
        text: Response text
        headers: Response headers
        
    Returns:
        Mock response object
    """
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.text = text
    mock_response.headers = headers or {}
    
    if json_data:
        mock_response.json.return_value = json_data
    else:
        mock_response.json.return_value = {}
    
    mock_response.raise_for_status = MagicMock()
    if status_code >= 400:
        error = requests.exceptions.HTTPError(response=mock_response)
        mock_response.raise_for_status.side_effect = error
    
    return mock_response


def create_apollo_error_response(
    status_code: int, error_message: str
) -> requests.exceptions.HTTPError:
    """
    Create an Apollo API error response.
    
    Args:
        status_code: HTTP status code (401, 402, 429, etc.)
        error_message: Error message
        
    Returns:
        HTTPError exception
    """
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.text = error_message
    mock_response.json.return_value = {"message": error_message}
    return requests.exceptions.HTTPError(response=mock_response)


def create_hubspot_error_response(
    status_code: int, error_message: str
) -> requests.exceptions.HTTPError:
    """
    Create a HubSpot API error response.
    
    Args:
        status_code: HTTP status code (401, 403, 404, etc.)
        error_message: Error message
        
    Returns:
        HTTPError exception
    """
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.text = error_message
    mock_response.json.return_value = {
        "status": "error",
        "message": error_message,
        "statusCode": status_code,
    }
    return requests.exceptions.HTTPError(response=mock_response)


def build_apollo_search_params(
    geography: str = "New York, NY",
    specialty: str = "Dermatology",
    limit: int = 50,
    has_website: bool = True,
) -> Dict[str, Any]:
    """
    Build Apollo search parameters for testing.
    
    Args:
        geography: Location filter
        specialty: Medical specialty
        limit: Maximum results
        has_website: Require website
        
    Returns:
        Search parameters dictionary
    """
    params = {
        "api_key": "test_api_key",
        "q_keywords": specialty,
        "person_locations": [geography],
        "organization_num_employees_ranges": ["1,50"],
        "person_titles": [
            "Owner",
            "CEO",
            "Medical Director",
            "Practice Manager",
            "Partner",
            "Managing Partner",
            "Principal",
            "Broker",
        ],
        "page": 1,
        "per_page": min(limit, 50),
    }
    
    if has_website:
        params["organization_keywords"] = "website"
    
    return params


def build_hubspot_contact_payload(
    email: str = "test@example.com",
    first_name: str = "Test",
    last_name: str = "User",
    company: Optional[str] = None,
    website: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build HubSpot contact payload for testing.
    
    Args:
        email: Contact email
        first_name: First name
        last_name: Last name
        company: Company name
        website: Website URL
        
    Returns:
        Contact payload dictionary
    """
    properties = {
        "email": email,
        "firstname": first_name,
        "lastname": last_name,
    }
    
    if company:
        properties["company"] = company
    if website:
        properties["website"] = website
    
    return {"properties": properties}

