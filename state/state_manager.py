"""
State Manager - Conversation and lead state persistence.

Manages conversation history and lead states in JSON files.
"""
import json
import os
from typing import Dict, List, Optional
from pathlib import Path


class StateManager:
    """
    Manages conversation and lead state persistence.
    
    Stores:
    - conversation_states.json: Thread ID -> conversation history
    - lead_states.json: Email -> lead metadata and status
    """
    
    def __init__(self, state_dir: Optional[str] = None):
        """
        Initialize State Manager.
        
        Args:
            state_dir: Directory for state files (defaults to ./state/)
        """
        self.state_dir = Path(state_dir or "state")
        self.state_dir.mkdir(exist_ok=True)
        
        self.conversation_file = self.state_dir / "conversation_states.json"
        self.lead_file = self.state_dir / "lead_states.json"
        
        # Initialize files if they don't exist
        self._init_files()
    
    def _init_files(self):
        """Initialize state files if they don't exist."""
        if not self.conversation_file.exists():
            self._write_json(self.conversation_file, {})
        
        if not self.lead_file.exists():
            self._write_json(self.lead_file, {})
    
    def _read_json(self, filepath: Path) -> Dict:
        """Read JSON file."""
        try:
            with open(filepath, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _write_json(self, filepath: Path, data: Dict):
        """Write JSON file."""
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
    
    def get_conversation_history(self, thread_id: str) -> List[str]:
        """
        Get conversation history for a thread.
        
        Args:
            thread_id: Email thread ID
            
        Returns:
            List of conversation messages
        """
        conversations = self._read_json(self.conversation_file)
        return conversations.get(thread_id, [])
    
    def add_conversation_message(
        self,
        thread_id: str,
        message: str,
        sender: str = "user"
    ):
        """
        Add a message to conversation history.
        
        Args:
            thread_id: Email thread ID
            message: Message content
            sender: "user" or "agent"
        """
        conversations = self._read_json(self.conversation_file)
        
        if thread_id not in conversations:
            conversations[thread_id] = []
        
        formatted_message = f"{sender.upper()}: {message}"
        conversations[thread_id].append(formatted_message)
        
        self._write_json(self.conversation_file, conversations)
    
    def get_lead_state(self, email: str) -> Optional[Dict]:
        """
        Get lead state by email.
        
        Args:
            email: Lead email address
            
        Returns:
            Lead state dictionary or None
        """
        leads = self._read_json(self.lead_file)
        return leads.get(email)
    
    def update_lead_state(self, email: str, state: Dict):
        """
        Update lead state.
        
        Args:
            email: Lead email address
            state: State dictionary to update
        """
        leads = self._read_json(self.lead_file)
        
        if email not in leads:
            leads[email] = {}
        
        leads[email].update(state)
        self._write_json(self.lead_file, leads)
    
    def set_lead_status(
        self,
        email: str,
        status: str,
        metadata: Optional[Dict] = None
    ):
        """
        Set lead status and optional metadata.
        
        Args:
            email: Lead email address
            status: Status string (e.g., "idle", "engaged", "booked")
            metadata: Optional metadata dictionary
        """
        leads = self._read_json(self.lead_file)
        
        if email not in leads:
            leads[email] = {}
        
        leads[email]["status"] = status
        if metadata:
            leads[email].update(metadata)
        
        self._write_json(self.lead_file, leads)
    
    def get_all_leads_by_status(self, status: str) -> List[Dict]:
        """
        Get all leads with a specific status.
        
        Args:
            status: Status to filter by
            
        Returns:
            List of lead dictionaries
        """
        leads = self._read_json(self.lead_file)
        return [
            {"email": email, **data}
            for email, data in leads.items()
            if data.get("status") == status
        ]
