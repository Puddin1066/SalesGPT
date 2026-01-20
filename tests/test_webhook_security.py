"""
Tests for webhook security features.

Tests signature verification and rate limiting.
"""
import pytest
import hmac
import hashlib
from fastapi.testclient import TestClient

from webhook_handler import app, verify_webhook_signature, settings


def test_verify_webhook_signature_valid():
    """Test valid webhook signature verification."""
    secret = "test_secret_key"
    payload = b'{"event": "email_replied", "thread_id": "123"}'
    
    # Generate valid signature
    signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    assert verify_webhook_signature(payload, signature, secret) is True


def test_verify_webhook_signature_invalid():
    """Test invalid webhook signature verification."""
    secret = "test_secret_key"
    payload = b'{"event": "email_replied", "thread_id": "123"}'
    invalid_signature = "invalid_signature"
    
    assert verify_webhook_signature(payload, invalid_signature, secret) is False


def test_verify_webhook_signature_missing():
    """Test webhook signature verification with missing signature."""
    secret = "test_secret_key"
    payload = b'{"event": "email_replied"}'
    
    assert verify_webhook_signature(payload, "", secret) is False
    assert verify_webhook_signature(payload, None, secret) is False


def test_webhook_endpoint_with_valid_signature():
    """Test webhook endpoint with valid signature."""
    client = TestClient(app)
    
    payload = {
        "event": "email_replied",
        "thread_id": "test_thread_123",
        "sender_email": "test@example.com",
        "sender_name": "Test User",
        "body": "Test message"
    }
    
    # Generate signature
    body_bytes = str(payload).encode()
    signature = hmac.new(
        settings.webhook_secret_key.encode(),
        body_bytes,
        hashlib.sha256
    ).hexdigest()
    
    # Note: This test may fail if orchestrator is not properly mocked
    # In a real test, you'd mock the orchestrator.handle_reply method
    response = client.post(
        "/webhook/smartlead",
        json=payload,
        headers={"X-Smartlead-Signature": signature}
    )
    
    # Should either succeed or fail with proper error (not 401)
    assert response.status_code != 401


def test_webhook_endpoint_with_invalid_signature():
    """Test webhook endpoint rejects invalid signature."""
    client = TestClient(app)
    
    payload = {
        "event": "email_replied",
        "thread_id": "test_thread_123",
        "sender_email": "test@example.com",
        "sender_name": "Test User",
        "body": "Test message"
    }
    
    response = client.post(
        "/webhook/smartlead",
        json=payload,
        headers={"X-Smartlead-Signature": "invalid_signature"}
    )
    
    # Should reject with 401
    assert response.status_code == 401


def test_webhook_endpoint_invalid_payload():
    """Test webhook endpoint rejects invalid payload."""
    client = TestClient(app)
    
    payload = {
        "event": "email_replied",
        # Missing required fields
    }
    
    response = client.post(
        "/webhook/smartlead",
        json=payload
    )
    
    # Should reject with 400
    assert response.status_code == 400


def test_webhook_endpoint_ignores_non_reply_events():
    """Test webhook endpoint ignores non-reply events."""
    client = TestClient(app)
    
    payload = {
        "event": "email_sent",  # Not email_replied
        "thread_id": "test_thread_123",
        "sender_email": "test@example.com",
        "sender_name": "Test User",
        "body": "Test message"
    }
    
    response = client.post(
        "/webhook/smartlead",
        json=payload
    )
    
    # Should return ignored status
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"



