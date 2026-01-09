"""
Tests for database migration and StateManager functionality.

Tests JSON to SQLite migration and StateManager database operations.
"""
import pytest
import json
from pathlib import Path
from datetime import datetime

from salesgpt.models.database import Lead, Conversation, ConversationMessage
from tests.fixtures.database import test_db_manager, test_state_manager


def test_state_manager_get_lead_state_nonexistent(test_state_manager):
    """Test getting lead state for non-existent lead."""
    result = test_state_manager.get_lead_state("nonexistent@example.com")
    assert result is None


def test_state_manager_set_lead_status(test_state_manager):
    """Test setting lead status."""
    email = "test@example.com"
    status = "engaged"
    metadata = {"test_key": "test_value"}
    
    test_state_manager.set_lead_status(email, status, metadata)
    
    lead_state = test_state_manager.get_lead_state(email)
    assert lead_state is not None
    assert lead_state["email"] == email
    assert lead_state["status"] == status
    assert lead_state["test_key"] == "test_value"


def test_state_manager_update_lead_state(test_state_manager):
    """Test updating lead state."""
    email = "test@example.com"
    
    # Set initial state
    test_state_manager.set_lead_status(email, "idle", {"key1": "value1"})
    
    # Update state
    test_state_manager.update_lead_state(email, {"key2": "value2", "status": "engaged"})
    
    lead_state = test_state_manager.get_lead_state(email)
    assert lead_state["key1"] == "value1"
    assert lead_state["key2"] == "value2"
    assert lead_state["status"] == "engaged"


def test_state_manager_get_conversation_history_empty(test_state_manager):
    """Test getting conversation history for non-existent thread."""
    history = test_state_manager.get_conversation_history("nonexistent_thread")
    assert history == []


def test_state_manager_add_conversation_message(test_state_manager):
    """Test adding conversation message."""
    thread_id = "test_thread_123"
    message = "Hello, this is a test message"
    sender = "user"
    
    test_state_manager.add_conversation_message(thread_id, message, sender)
    
    history = test_state_manager.get_conversation_history(thread_id)
    assert len(history) == 1
    assert "USER: Hello, this is a test message" in history[0]


def test_state_manager_conversation_multiple_messages(test_state_manager):
    """Test conversation with multiple messages."""
    thread_id = "test_thread_456"
    
    test_state_manager.add_conversation_message(thread_id, "Message 1", "user")
    test_state_manager.add_conversation_message(thread_id, "Message 2", "agent")
    test_state_manager.add_conversation_message(thread_id, "Message 3", "user")
    
    history = test_state_manager.get_conversation_history(thread_id)
    assert len(history) == 3
    assert "USER: Message 1" in history[0]
    assert "AGENT: Message 2" in history[1]
    assert "USER: Message 3" in history[2]


def test_state_manager_get_all_leads_by_status(test_state_manager):
    """Test getting all leads by status."""
    # Create leads with different statuses
    test_state_manager.set_lead_status("lead1@example.com", "idle")
    test_state_manager.set_lead_status("lead2@example.com", "engaged")
    test_state_manager.set_lead_status("lead3@example.com", "idle")
    
    idle_leads = test_state_manager.get_all_leads_by_status("idle")
    assert len(idle_leads) == 2
    
    engaged_leads = test_state_manager.get_all_leads_by_status("engaged")
    assert len(engaged_leads) == 1
    
    booked_leads = test_state_manager.get_all_leads_by_status("booked")
    assert len(booked_leads) == 0


def test_state_manager_lead_with_metadata(test_state_manager):
    """Test lead with complex metadata."""
    email = "complex@example.com"
    metadata = {
        "apollo_person_id": "12345",
        "hubspot_contact_id": "67890",
        "campaign_id": "campaign_123",
        "score": 85,
        "nested": {"key": "value"}
    }
    
    test_state_manager.set_lead_status(email, "idle", metadata)
    
    lead_state = test_state_manager.get_lead_state(email)
    assert lead_state["apollo_person_id"] == "12345"
    assert lead_state["hubspot_contact_id"] == "67890"
    assert lead_state["campaign_id"] == "campaign_123"
    assert lead_state["score"] == 85
    assert lead_state["nested"]["key"] == "value"

