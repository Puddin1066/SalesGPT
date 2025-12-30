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
        
        self.base_url = "https://api.smartlead.ai/v1"
        self.headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json",
        }
    
    def create_campaign(
        self,
        name: str,
        from_email: str,
        from_name: str,
        reply_to: str,
        mailbox_ids: List[int]
    ) -> Optional[int]:
        """
        Create a new email campaign.
        
        Args:
            name: Campaign name
            from_email: Sender email address
            from_name: Sender display name
            reply_to: Reply-to email address
            mailbox_ids: List of mailbox IDs for domain rotation
            
        Returns:
            Campaign ID if successful, None otherwise
        """
        payload = {
            "campaign_name": name,
            "from_email": from_email,
            "from_name": from_name,
            "reply_to": reply_to,
            "mailbox_ids": mailbox_ids,
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/campaigns",
                json=payload,
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            return data.get("campaign_id")
            
        except requests.exceptions.RequestException as e:
            print(f"Smartlead API error creating campaign: {e}")
            return None
    
    def add_sequence(
        self,
        campaign_id: int,
        subject: str,
        body: str,
        delay_days: int = 0
    ) -> Optional[int]:
        """
        Add an email sequence to a campaign.
        
        Args:
            campaign_id: Campaign ID
            subject: Email subject line
            body: Email body (supports template fields)
            delay_days: Days to wait before sending
            
        Returns:
            Sequence ID if successful, None otherwise
        """
        payload = {
            "campaign_id": campaign_id,
            "subject": subject,
            "body": body,
            "delay_days": delay_days,
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/campaigns/{campaign_id}/sequences",
                json=payload,
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            return data.get("sequence_id")
            
        except requests.exceptions.RequestException as e:
            print(f"Smartlead API error adding sequence: {e}")
            return None
    
    def add_leads_to_campaign(
        self,
        campaign_id: int,
        leads: List[Dict[str, str]]
    ) -> bool:
        """
        Add leads to a campaign.
        
        Args:
            campaign_id: Campaign ID
            leads: List of lead dicts with 'email', 'first_name', 'last_name', etc.
            
        Returns:
            True if successful, False otherwise
        """
        payload = {
            "campaign_id": campaign_id,
            "leads": leads,
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/campaigns/{campaign_id}/leads",
                json=payload,
                headers=self.headers
            )
            response.raise_for_status()
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"Smartlead API error adding leads: {e}")
            return False
    
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
                headers=self.headers
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
                headers=self.headers
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
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Smartlead API error checking warmup: {e}")
            return {"status": "unknown", "error": str(e)}
