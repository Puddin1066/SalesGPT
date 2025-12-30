"""
HubSpot CRM Agent.

Manages pipeline stage updates: Idle → Engaged → Booked → Closed.
"""
import os
import requests
from typing import Dict, Optional, Literal


class HubSpotAgent:
    """
    HubSpot API wrapper for CRM pipeline management.
    
    Critical design: Atomic service - handles all CRM operations.
    Single outcome: Update pipeline stages based on lead status.
    """
    
    PIPELINE_STAGES = {
        "idle": "idle",
        "engaged": "engaged",
        "booked": "booked",
        "closed": "closed",
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize HubSpot Agent.
        
        Args:
            api_key: HubSpot API key (defaults to HUBSPOT_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("HUBSPOT_API_KEY")
        if not self.api_key:
            raise ValueError("HUBSPOT_API_KEY not found in environment")
        
        self.base_url = "https://api.hubapi.com"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
    
    def create_contact(
        self,
        email: str,
        first_name: str,
        last_name: str,
        company: Optional[str] = None,
        website: Optional[str] = None
    ) -> Optional[str]:
        """
        Create a new contact in HubSpot.
        
        Args:
            email: Contact email
            first_name: First name
            last_name: Last name
            company: Company name
            website: Website URL
            
        Returns:
            Contact ID if successful, None otherwise
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
        
        payload = {"properties": properties}
        
        try:
            response = requests.post(
                f"{self.base_url}/crm/v3/objects/contacts",
                json=payload,
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            return data.get("id")
            
        except requests.exceptions.RequestException as e:
            print(f"HubSpot API error creating contact: {e}")
            return None
    
    def update_pipeline_stage(
        self,
        contact_id: str,
        stage: Literal["idle", "engaged", "booked", "closed"]
    ) -> bool:
        """
        Update contact's pipeline stage.
        
        Args:
            contact_id: HubSpot contact ID
            stage: Target pipeline stage
            
        Returns:
            True if successful, False otherwise
        """
        if stage not in self.PIPELINE_STAGES:
            raise ValueError(f"Invalid stage: {stage}")
        
        # HubSpot uses deal pipeline stages
        # This is a simplified implementation
        # In production, you'd need to create/update deals
        
        properties = {
            "dealstage": self.PIPELINE_STAGES[stage],
        }
        
        payload = {"properties": properties}
        
        try:
            # Update contact properties (simplified)
            # In production, you'd update deal stages
            response = requests.patch(
                f"{self.base_url}/crm/v3/objects/contacts/{contact_id}",
                json=payload,
                headers=self.headers
            )
            response.raise_for_status()
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"HubSpot API error updating stage: {e}")
            return False
    
    def create_deal(
        self,
        contact_id: str,
        deal_name: str,
        amount: Optional[float] = None,
        stage: str = "idle"
    ) -> Optional[str]:
        """
        Create a deal for a contact.
        
        Args:
            contact_id: HubSpot contact ID
            deal_name: Deal name
            amount: Deal amount (optional)
            stage: Initial pipeline stage
            
        Returns:
            Deal ID if successful, None otherwise
        """
        properties = {
            "dealname": deal_name,
            "dealstage": self.PIPELINE_STAGES.get(stage, "idle"),
        }
        
        if amount:
            properties["amount"] = str(amount)
        
        associations = [{
            "to": {"id": contact_id},
            "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 3}]
        }]
        
        payload = {
            "properties": properties,
            "associations": associations,
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/crm/v3/objects/deals",
                json=payload,
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            return data.get("id")
            
        except requests.exceptions.RequestException as e:
            print(f"HubSpot API error creating deal: {e}")
            return None
    
    def get_contact_by_email(self, email: str) -> Optional[Dict]:
        """
        Get contact by email address.
        
        Args:
            email: Contact email
            
        Returns:
            Contact dictionary if found, None otherwise
        """
        try:
            response = requests.get(
                f"{self.base_url}/crm/v3/objects/contacts/{email}",
                params={"idProperty": "email"},
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException:
            return None
