"""
Mock HubSpot API responses for testing.
Reusable response data structures for all HubSpot endpoints.
"""
from typing import Dict, Any


def mock_contact_response(contact_id: str = "contact_123") -> Dict[str, Any]:
    """Mock successful contact creation response."""
    return {
        "id": contact_id,
        "properties": {
            "email": "john@example.com",
            "firstname": "John",
            "lastname": "Doe",
            "company": "Example Clinic",
            "website": "https://example.com",
        },
        "createdAt": "2024-01-01T00:00:00.000Z",
        "updatedAt": "2024-01-01T00:00:00.000Z",
    }


def mock_contact_list_response() -> Dict[str, Any]:
    """Mock contact list response."""
    return {
        "results": [
            {
                "id": "contact_123",
                "properties": {
                    "email": "john@example.com",
                    "firstname": "John",
                    "lastname": "Doe",
                },
            }
        ],
        "paging": {"next": None},
    }


def mock_deal_response(deal_id: str = "deal_123") -> Dict[str, Any]:
    """Mock successful deal creation response."""
    return {
        "id": deal_id,
        "properties": {
            "dealname": "Example Clinic Deal",
            "dealstage": "idle",
            "amount": "10000",
        },
        "associations": {
            "contacts": {
                "results": [{"id": "contact_123", "type": "deal_to_contact"}]
            }
        },
        "createdAt": "2024-01-01T00:00:00.000Z",
        "updatedAt": "2024-01-01T00:00:00.000Z",
    }


def mock_oauth_token_response() -> Dict[str, Any]:
    """Mock OAuth token refresh response."""
    return {
        "access_token": "new_access_token_123",
        "refresh_token": "new_refresh_token_123",
        "expires_in": 3600,
        "token_type": "Bearer",
    }


def mock_oauth_token_metadata() -> Dict[str, Any]:
    """Mock OAuth token metadata response."""
    return {
        "token": "access_token_123",
        "user": "user@example.com",
        "hub_id": 123456,
        "scopes": ["crm.objects.contacts.read", "crm.objects.contacts.write"],
        "hub_domain": "example.hubspot.com",
        "app_id": "app_123",
        "expires_in": 3600,
        "user_id": "user_123",
        "token_type": "Bearer",
    }


def mock_error_response(status_code: int, message: str) -> Dict[str, Any]:
    """Mock error response."""
    return {
        "status": "error",
        "message": message,
        "correlationId": "correlation_123",
        "statusCode": status_code,
    }


def mock_401_error() -> Dict[str, Any]:
    """Mock 401 Unauthorized error."""
    return mock_error_response(401, "Authentication credentials not found")


def mock_403_error() -> Dict[str, Any]:
    """Mock 403 Forbidden error."""
    return mock_error_response(403, "Insufficient permissions")


def mock_404_error() -> Dict[str, Any]:
    """Mock 404 Not Found error."""
    return mock_error_response(404, "Resource not found")


def mock_rate_limit_error() -> Dict[str, Any]:
    """Mock 429 Rate Limit error."""
    return {
        "status": "error",
        "message": "Rate limit exceeded",
        "correlationId": "correlation_123",
        "statusCode": 429,
    }



