"""
HubSpot CRM Agent.

Manages pipeline stage updates: Idle → Engaged → Booked → Closed.

Supports both OAuth 2.0 and Private App access tokens.
For OAuth: Requires HUBSPOT_CLIENT_ID, HUBSPOT_CLIENT_SECRET, and HUBSPOT_REFRESH_TOKEN
For Private App: Requires HUBSPOT_API_KEY (Private App access token)
"""
import os
import requests
from typing import Dict, Optional, Literal


class HubSpotAgent:
    """
    HubSpot API wrapper for CRM pipeline management.
    
    Supports OAuth 2.0 (with token refresh) and Private App access tokens.
    
    Critical design: Atomic service - handles all CRM operations.
    Single outcome: Update pipeline stages based on lead status.
    """
    
    PIPELINE_STAGES = {
        "idle": "idle",
        "engaged": "engaged",
        "booked": "booked",
        "closed": "closed",
    }
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        refresh_token: Optional[str] = None
    ):
        """
        Initialize HubSpot Agent.
        
        Supports two authentication methods:
        1. Private App Access Token (simpler, single account)
        2. OAuth 2.0 (with refresh token support)
        
        Args:
            api_key: Private App access token (defaults to HUBSPOT_API_KEY env var)
            client_id: OAuth client ID (defaults to HUBSPOT_CLIENT_ID env var)
            client_secret: OAuth client secret (defaults to HUBSPOT_CLIENT_SECRET env var)
            refresh_token: OAuth refresh token (defaults to HUBSPOT_REFRESH_TOKEN env var)
        """
        # Support mock API URL override
        mock_base_url = os.getenv("HUBSPOT_API_URL", "https://api.hubapi.com")
        self.base_url = mock_base_url.rstrip("/")
        self.oauth_base_url = f"{self.base_url}/oauth/v1"
        
        # Try OAuth first if credentials are provided
        self.client_id = client_id or os.getenv("HUBSPOT_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("HUBSPOT_CLIENT_SECRET")
        self.refresh_token = refresh_token or os.getenv("HUBSPOT_REFRESH_TOKEN")
        self.access_token = None
        
        # Fall back to Private App token if OAuth not configured
        if self.client_id and self.client_secret and self.refresh_token:
            self.use_oauth = True
            self._refresh_access_token()
        else:
            self.use_oauth = False
            self.api_key = api_key or os.getenv("HUBSPOT_API_KEY")
            # Allow mock API mode without real credentials
            use_mock_apis = os.getenv("USE_MOCK_APIS", "false").lower() == "true"
            if not self.api_key:
                if use_mock_apis:
                    # Use a dummy token for mock mode
                    self.api_key = "mock_hubspot_token"
                    print("⚠️  HubSpot: Using mock mode (no real credentials needed)")
                else:
                    raise ValueError(
                        "HubSpot authentication not configured. "
                        "Either set HUBSPOT_API_KEY (Private App) or "
                        "HUBSPOT_CLIENT_ID, HUBSPOT_CLIENT_SECRET, and HUBSPOT_REFRESH_TOKEN (OAuth)"
                    )
        
        self._update_headers()
    
    @staticmethod
    def generate_initial_tokens(
        client_id: str,
        client_secret: str,
        authorization_code: str,
        redirect_uri: str
    ) -> Optional[Dict]:
        """
        Generate initial OAuth access and refresh tokens from authorization code.
        
        Per HubSpot OAuth guide: https://developers.hubspot.com/docs/api-reference/auth-oauth-v1/guide
        
        Args:
            client_id: OAuth client ID from app settings
            client_secret: OAuth client secret from app settings
            authorization_code: Code returned in redirect URL after user installs app
            redirect_uri: The app's redirect URL (must match app settings)
            
        Returns:
            Dictionary with access_token, refresh_token, expires_in, etc. or None if failed
        """
        try:
            response = requests.post(
                "https://api.hubapi.com/oauth/v1/token",
                data={
                    "grant_type": "authorization_code",
                    "code": authorization_code,
                    "redirect_uri": redirect_uri,
                    "client_id": client_id,
                    "client_secret": client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"HubSpot OAuth initial token generation failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    print(f"Error details: {error_data}")
                except:
                    print(f"Error response: {e.response.text}")
            return None
    
    def _refresh_access_token(self) -> bool:
        """
        Refresh OAuth access token using refresh token.
        
        Per HubSpot OAuth guide: https://developers.hubspot.com/docs/api-reference/auth-oauth-v1/guide
        
        Returns:
            True if successful, False otherwise
        """
        if not all([self.client_id, self.client_secret, self.refresh_token]):
            return False
        
        try:
            response = requests.post(
                f"{self.oauth_base_url}/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self.refresh_token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            self.access_token = data.get("access_token")
            # Update refresh token if a new one is provided
            if "refresh_token" in data:
                self.refresh_token = data.get("refresh_token")
            return True
        except requests.exceptions.RequestException as e:
            print(f"HubSpot OAuth token refresh failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    print(f"Error details: {error_data}")
                except:
                    print(f"Error response: {e.response.text}")
            return False
    
    def get_token_metadata(self) -> Optional[Dict]:
        """
        Retrieve OAuth access token metadata.
        
        Per HubSpot OAuth guide: https://developers.hubspot.com/docs/api-reference/auth-oauth-v1/guide
        
        Returns:
            Dictionary with token metadata (user, hub_id, scopes, etc.) or None if failed
        """
        if not self.use_oauth or not self.access_token:
            return None
        
        try:
            response = requests.get(
                f"{self.oauth_base_url}/access-tokens/{self.access_token}",
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"HubSpot OAuth token metadata retrieval failed: {e}")
            return None
    
    def _update_headers(self):
        """Update headers with current access token or API key."""
        token = self.access_token if self.use_oauth else self.api_key
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
    
    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Make API request with automatic OAuth token refresh on 401 errors.
        
        Args:
            method: HTTP method (get, post, patch, etc.)
            url: API endpoint URL
            **kwargs: Additional arguments for requests
            
        Returns:
            Response object
        """
        response = requests.request(method, url, headers=self.headers, **kwargs)
        
        # If OAuth and got 401, try refreshing token once
        if self.use_oauth and response.status_code == 401:
            if self._refresh_access_token():
                self._update_headers()
                # Retry the request with new token
                response = requests.request(method, url, headers=self.headers, **kwargs)
        
        return response
    
    def create_contact(
        self,
        email: str,
        first_name: str,
        last_name: str,
        company: Optional[str] = None,
        website: Optional[str] = None,
        phone: Optional[str] = None,
        title: Optional[str] = None,
        linkedin_url: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        country: Optional[str] = None,
        postal_code: Optional[str] = None,
        additional_properties: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Create a new contact in HubSpot with full Apollo data.
        
        Args:
            email: Contact email
            first_name: First name
            last_name: Last name
            company: Company name
            website: Website URL
            phone: Phone number
            title: Job title
            linkedin_url: LinkedIn profile URL
            city: City
            state: State/Province
            country: Country
            postal_code: Postal/ZIP code
            additional_properties: Additional HubSpot properties as dict
            
        Returns:
            Contact ID if successful, None otherwise
        """
        properties = {
            "email": email,
            "firstname": first_name,
            "lastname": last_name,
        }
        
        # Add optional standard properties
        if company:
            properties["company"] = company
        if website:
            properties["website"] = website
        if phone:
            properties["phone"] = phone
        if title:
            properties["jobtitle"] = title
        if linkedin_url:
            properties["linkedin"] = linkedin_url
        if city:
            properties["city"] = city
        if state:
            properties["state"] = state
        if country:
            properties["country"] = country
        if postal_code:
            properties["zip"] = postal_code
        
        # Add any additional custom properties
        if additional_properties:
            properties.update(additional_properties)
        
        payload = {"properties": properties}
        
        try:
            response = self._make_request(
                "POST",
                f"{self.base_url}/crm/v3/objects/contacts",
                json=payload
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
            response = self._make_request(
                "PATCH",
                f"{self.base_url}/crm/v3/objects/contacts/{contact_id}",
                json=payload
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
            response = self._make_request(
                "POST",
                f"{self.base_url}/crm/v3/objects/deals",
                json=payload
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
            response = self._make_request(
                "GET",
                f"{self.base_url}/crm/v3/objects/contacts/{email}",
                params={"idProperty": "email"}
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException:
            return None
    
    def update_contact_properties(
        self,
        contact_id: str,
        properties: Dict[str, str]
    ) -> bool:
        """
        Update contact properties (including custom properties).
        
        This is useful for adding email content, notes, or other custom fields
        that can be viewed in HubSpot UI.
        
        Args:
            contact_id: HubSpot contact ID
            properties: Dictionary of property names and values to update
            
        Returns:
            True if successful, False otherwise
        """
        payload = {"properties": properties}
        
        try:
            response = self._make_request(
                "PATCH",
                f"{self.base_url}/crm/v3/objects/contacts/{contact_id}",
                json=payload
            )
            response.raise_for_status()
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"HubSpot API error updating contact properties: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    print(f"Error details: {error_data}")
                except:
                    print(f"Error response: {e.response.text}")
            return False
    
    def create_or_update_contact(
        self,
        email: str,
        properties: Dict[str, str]
    ) -> Optional[str]:
        """
        Create or update contact using email as identifier.
        
        This method will create a new contact if it doesn't exist,
        or update existing contact if email matches.
        
        Args:
            email: Contact email (used as unique identifier)
            properties: Dictionary of properties to set
            
        Returns:
            Contact ID if successful, None otherwise
        """
        # Try to get existing contact
        existing = self.get_contact_by_email(email)
        
        if existing:
            # Update existing contact
            contact_id = existing.get("id")
            if self.update_contact_properties(contact_id, properties):
                return contact_id
        else:
            # Create new contact
            return self.create_contact(
                email=email,
                first_name=properties.get("firstname", ""),
                last_name=properties.get("lastname", ""),
                company=properties.get("company"),
                website=properties.get("website"),
                phone=properties.get("phone"),
                title=properties.get("jobtitle"),
                linkedin_url=properties.get("linkedin"),
                city=properties.get("city"),
                state=properties.get("state"),
                country=properties.get("country"),
                postal_code=properties.get("zip"),
                additional_properties={
                    k: v for k, v in properties.items()
                    if k not in ["email", "firstname", "lastname", "company", 
                                "website", "phone", "jobtitle", "linkedin",
                                "city", "state", "country", "zip"]
                }
            )
        
        return None
