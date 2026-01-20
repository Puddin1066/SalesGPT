"""
Smartlead Outbound Delivery Agent.

Handles inbox warm-up, domain rotation, and email sequence management.
Evidence-insertion template fields supported.
"""
import os
import requests
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class EmailSequence:
    """Email sequence configuration."""
    name: str
    subject: str
    body: str
    delay_days: int
    template_fields: Dict[str, str]


class SmartleadAgent:
    """
    Smartlead API wrapper for email outbound sequences.
    
    Critical design: Atomic service - handles all email delivery.
    Single outcome: Queue emails and manage sequences.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Smartlead Agent.
        
        Args:
            api_key: Smartlead API key (defaults to SMARTLEAD_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("SMARTLEAD_API_KEY")
        if not self.api_key:
            raise ValueError("SMARTLEAD_API_KEY not found in environment")
        
        # Support mock API URL override
        self.base_url = os.getenv("SMARTLEAD_API_URL", "https://server.smartlead.ai/api/v1")
        if not self.base_url.endswith("/v1"):
            self.base_url = self.base_url.rstrip("/") + "/v1"
        # Smartlead API uses query parameter for authentication, not headers
        self.headers = {
            "Content-Type": "application/json",
        }
        self.api_key_param = {"api_key": self.api_key}
    
    def create_campaign(
        self,
        name: str,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
        mailbox_ids: Optional[List[int]] = None,
        client_id: Optional[int] = None
    ) -> Optional[int]:
        """
        Create a new email campaign.
        
        Per official Smartlead API docs: https://helpcenter.smartlead.ai/en/articles/125-full-api-documentation
        
        Args:
            name: Campaign name (required)
            from_email: Sender email address (optional - can be set later)
            from_name: Sender display name (optional - can be set later)
            reply_to: Reply-to email address (optional - can be set later)
            mailbox_ids: List of mailbox IDs for domain rotation (optional - can be set later)
            client_id: Client ID if campaign is attached to a client (optional)
            
        Returns:
            Campaign ID if successful, None otherwise
        """
        # Per official docs, only name and client_id are required for creation
        payload = {
            "name": name,
            "client_id": client_id  # null if no client
        }
        
        try:
            # Use correct endpoint: /campaigns/create (per official docs)
            response = requests.post(
                f"{self.base_url}/campaigns/create",
                json=payload,
                headers=self.headers,
                params=self.api_key_param
            )
            response.raise_for_status()
            data = response.json()
            
            # Response format: {"ok": true, "id": 3023, "name": "...", "created_at": "..."}
            if data.get("ok") and data.get("id"):
                campaign_id = data.get("id")
                
                # If additional settings provided, update campaign settings
                if from_email or from_name or reply_to or mailbox_ids:
                    # Note: These may need to be set via campaign settings endpoint
                    # For now, campaign is created with basic settings
                    pass
                
                return campaign_id
            else:
                return None
            
        except requests.exceptions.RequestException as e:
            print(f"Smartlead API error creating campaign: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    print(f"Error details: {error_data}")
                except:
                    print(f"Error response: {e.response.text[:200]}")
            return None
    
    def add_sequence(
        self,
        campaign_id: int,
        subject: str,
        body: str,
        delay_days: int = 0,
        seq_number: Optional[int] = None
    ) -> Optional[int]:
        """
        Add an email sequence to a campaign.
        
        Per official Smartlead API docs: https://helpcenter.smartlead.ai/en/articles/125-full-api-documentation
        
        Args:
            campaign_id: Campaign ID
            subject: Email subject line
            body: Email body (supports template fields)
            delay_days: Days to wait before sending
            seq_number: Sequence number (1, 2, 3, etc.). If None, will try to auto-increment.
            
        Returns:
            Sequence ID if successful, None otherwise
        """
        # Get existing sequences to determine next seq_number
        if seq_number is None:
            try:
                response = requests.get(
                    f"{self.base_url}/campaigns/{campaign_id}/sequences",
                    headers=self.headers,
                    params=self.api_key_param
                )
                if response.status_code == 200:
                    existing_sequences = response.json()
                    seq_number = len(existing_sequences) + 1
                else:
                    seq_number = 1  # Default to first sequence
            except:
                seq_number = 1  # Default to first sequence
        
        # Per API requirements, sequences must be wrapped in a "sequences" array
        # Required fields: subject, email_body (not "body"), seq_number, seq_delay_details.delay_in_days
        payload = {
            "sequences": [{
                "subject": subject,
                "email_body": body,  # Field name is "email_body" not "body"
                "seq_number": seq_number,
                "seq_delay_details": {
                    "delay_in_days": delay_days
                }
            }]
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/campaigns/{campaign_id}/sequences",
                json=payload,
                headers=self.headers,
                params=self.api_key_param
            )
            response.raise_for_status()
            data = response.json()
            # Response format: {"ok": true, "data": "success"}
            # Sequence ID might be in response or we need to fetch sequences to get it
            if data.get("ok"):
                # Fetch sequences to get the newly created sequence ID
                try:
                    seq_response = requests.get(
                        f"{self.base_url}/campaigns/{campaign_id}/sequences",
                        headers=self.headers,
                        params=self.api_key_param
                    )
                    if seq_response.status_code == 200:
                        sequences = seq_response.json()
                        # Return the last sequence (most recently added)
                        if sequences:
                            return sequences[-1].get("id")
                except:
                    pass
                # If we can't get the ID, return True to indicate success
                return True
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"Smartlead API error adding sequence: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    print(f"Error details: {error_data}")
                except:
                    print(f"Error response: {e.response.text[:300]}")
            return None
    
    def add_leads_to_campaign(
        self,
        campaign_id: int,
        leads: List[Dict[str, str]]
    ) -> bool:
        """
        Add leads to a campaign.
        
        Per official Smartlead API docs: https://helpcenter.smartlead.ai/en/articles/125-full-api-documentation
        
        Args:
            campaign_id: Campaign ID
            leads: List of lead dicts. Each lead should have:
                - first_name (optional)
                - last_name (optional)
                - email (required)
                - phone_number (optional)
                - company_name (optional)
                - website (optional)
                - location (optional)
                - custom_fields (optional, max 20 fields)
                - linkedin_profile (optional)
                - company_url (optional)
            
        Returns:
            True if successful, False otherwise
        """
        # Per official docs, leads are added one at a time or in batch
        # The endpoint expects the lead data directly, not wrapped in a "leads" array
        success_count = 0
        
        for lead in leads:
            try:
                # Each lead is added individually per the API docs
                response = requests.post(
                    f"{self.base_url}/campaigns/{campaign_id}/leads",
                    json=lead,  # Send lead data directly
                    headers=self.headers,
                    params=self.api_key_param
                )
                response.raise_for_status()
                data = response.json()
                if data.get("ok"):
                    success_count += 1
                else:
                    print(f"Warning: Failed to add lead {lead.get('email', 'unknown')}")
                    
            except requests.exceptions.RequestException as e:
                print(f"Smartlead API error adding lead {lead.get('email', 'unknown')}: {e}")
                continue
        
        # Return True if at least one lead was added successfully
        return success_count > 0
    
    def send_reply(
        self,
        thread_id: str,
        body: str,
        subject: Optional[str] = None
    ) -> bool:
        """
        Send a reply to an existing email thread.
        
        Args:
            thread_id: Email thread ID
            body: Reply body
            subject: Optional subject (uses original if not provided)
            
        Returns:
            True if successful, False otherwise
        """
        payload = {
            "thread_id": thread_id,
            "body": body,
        }
        
        if subject:
            payload["subject"] = subject
        
        try:
            response = requests.post(
                f"{self.base_url}/replies",
                json=payload,
                headers=self.headers,
                params=self.api_key_param
            )
            response.raise_for_status()
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"Smartlead API error sending reply: {e}")
            return False
    
    def get_mailboxes(self) -> List[Dict]:
        """
        Get list of available mailboxes for domain rotation.
        
        Returns:
            List of mailbox dictionaries
        """
        try:
            response = requests.get(
                f"{self.base_url}/mailboxes",
                headers=self.headers,
                params=self.api_key_param
            )
            response.raise_for_status()
            data = response.json()
            return data.get("mailboxes", [])
            
        except requests.exceptions.RequestException as e:
            print(f"Smartlead API error getting mailboxes: {e}")
            return []
    
    def check_warmup_status(self, mailbox_id: int) -> Dict:
        """
        Check inbox warm-up status for a mailbox.
        
        Args:
            mailbox_id: Mailbox ID
            
        Returns:
            Warm-up status dictionary
        """
        try:
            response = requests.get(
                f"{self.base_url}/mailboxes/{mailbox_id}/warmup",
                headers=self.headers,
                params=self.api_key_param
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Smartlead API error checking warmup: {e}")
            return {"status": "unknown", "error": str(e)}
