"""
Apollo Agent - Lead sourcing + enrichment service.

Searches for leads based on geography, specialty, and website presence.
Returns enriched lead data with clinic metadata.

API Pricing & Credits:
According to Apollo API documentation (https://docs.apollo.io/docs/api-pricing),
the following endpoints consume credits:

Search Endpoints (Credit-Consuming):
- Organization Search: v1/mixed_companies/search
- Organization Job Postings: /v1/organizations/{organization_id}/job_postings
- Complete Organization Info: /v1/organizations/{id}
- News Articles: /v1/news_articles/search

Enrichment Endpoints (Credit-Consuming):
- People Enrichment: v1/people/match
- Bulk People Enrichment: v1/people/bulk_match
- Organization Enrichment: v1/organizations/enrich
- Bulk Organization Enrichment: v1/organizations/bulk_enrich

Note: The mixed_people/search endpoint used in search_leads() may or may not
consume credits depending on your Apollo plan. Check your plan details.

To track credit usage, refer to the "Track API Usage" section in Apollo's
API documentation or your Apollo dashboard.
"""
import os
import requests
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

# Set up logging for this module
logger = logging.getLogger(__name__)

@dataclass
class Lead:
    """Lead data structure."""
    name: str
    email: str
    website: str
    company_name: str
    specialty: str
    location: str
    metadata: Dict


class ApolloAgent:
    """
    Apollo API wrapper for lead sourcing and enrichment.
    
    Critical design: Atomic service - can be edited independently.
    Single outcome: Return scored leads based on search criteria.
    
    Credit Awareness:
    - search_leads() uses mixed_people/search (credit consumption varies by plan)
    - enrich_person() uses v1/people/match (CONSUMES CREDITS)
    - enrich_organization() uses v1/organizations/enrich (CONSUMES CREDITS)
    - bulk_enrich_people() uses v1/people/bulk_match (CONSUMES CREDITS)
    - bulk_enrich_organizations() uses v1/organizations/bulk_enrich (CONSUMES CREDITS)
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Apollo Agent.
        
        Args:
            api_key: Apollo API key (defaults to APOLLO_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("APOLLO_API_KEY")
        if not self.api_key:
            raise ValueError("APOLLO_API_KEY not found in environment")
        
        # Support mock API URL override
        self.base_url = os.getenv("APOLLO_API_URL", "https://api.apollo.io/v1")
        if not self.base_url.endswith("/v1"):
            self.base_url = self.base_url.rstrip("/") + "/v1"
        self.headers = {
            "Cache-Control": "no-cache",
            "Content-Type": "application/json",
            "X-Api-Key": self.api_key,  # Apollo requires API key in header (not in body)
        }
    
    def search_leads(
        self,
        geography: str,
        specialty: str,
        min_employees: int = 1,
        max_employees: int = 50,
        has_website: bool = True,
        limit: int = 50
    ) -> List[Lead]:
        """
        Search for leads matching criteria.
        
        Uses: v1/mixed_people/search
        Credit Consumption: May consume credits depending on your Apollo plan.
        Check your plan details for credit usage.
        
        Args:
            geography: Location filter (e.g., "New York, NY")
            specialty: Medical specialty filter
            min_employees: Minimum employee count
            max_employees: Maximum employee count
            has_website: Require website presence
            limit: Maximum results to return (max 50 per request)
            
        Returns:
            List of Lead objects with enriched data
            
        Raises:
            requests.exceptions.RequestException: On API errors (401, 429, etc.)
        """
        search_params = {
            # Note: api_key now in X-Api-Key header (not in body)
            "q_keywords": specialty,
            "person_locations": [geography],
            "organization_num_employees_ranges": [
                f"{min_employees},{max_employees}"
            ],
            "person_titles": [
                "Owner", "CEO", "Medical Director", "Practice Manager", 
                "Partner", "Managing Partner", "Principal", "Broker"
            ],
            "page": 1,
            "per_page": min(limit, 50),
        }
        
        if has_website:
            search_params["organization_keywords"] = "website"
        
        try:
            logger.info(f"Apollo API: Searching for {specialty} in {geography}")
            response = requests.post(
                f"{self.base_url}/mixed_people/search",
                json=search_params,
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            
            leads = []
            people_found = data.get("people", [])
            logger.info(f"Apollo API: Found {len(people_found)} potential leads")
            
            for person in people_found[:limit]:
                org = person.get("organization", {})
                
                # Extract website
                website = org.get("website_url", "") or org.get("primary_phone", "")
                
                # Only include if has website (if required)
                if has_website and not website:
                    continue
                
                # Extract all available Apollo data (no additional API calls)
                lead = Lead(
                    name=f"{person.get('first_name', '')} {person.get('last_name', '')}".strip(),
                    email=person.get("email", ""),
                    website=website,
                    company_name=org.get("name", ""),
                    specialty=specialty,
                    location=geography,
                    metadata={
                        # Person identifiers
                        "apollo_person_id": person.get("id", ""),
                        "apollo_organization_id": org.get("id", ""),
                        # Person professional info
                        "title": person.get("title", ""),
                        "linkedin_url": person.get("linkedin_url", ""),
                        # Person contact info
                        "person_phone": person.get("phone_numbers", [None])[0] if person.get("phone_numbers") else None,
                        "person_city": person.get("city", ""),
                        "person_state": person.get("state", ""),
                        "person_country": person.get("country", ""),
                        "person_postal_code": person.get("postal_code", ""),
                        # Organization info
                        "organization_name": org.get("name", ""),
                        "organization_website": org.get("website_url", ""),
                        "organization_phone": org.get("primary_phone", ""),
                        "employee_count": org.get("estimated_num_employees", 0),
                        "organization_industry": org.get("industry", ""),
                        "organization_city": org.get("city", ""),
                        "organization_state": org.get("state", ""),
                        "organization_country": org.get("country", ""),
                        "organization_postal_code": org.get("postal_code", ""),
                        # Additional Apollo fields
                        "apollo_updated_at": person.get("updated_at", ""),
                        "organization_updated_at": org.get("updated_at", ""),
                    }
                )
                leads.append(lead)
            
            return leads
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Apollo API error: {e}")
            if e.response is not None:
                status_code = e.response.status_code
                logger.error(f"Status Code: {status_code} - Body: {e.response.text}")
                
                # Credit-related error handling
                if status_code == 402:
                    logger.error("Payment required - Check your Apollo plan and credit balance")
                elif status_code == 429:
                    logger.error("Rate limit exceeded - Wait a few minutes or check your Apollo plan")
                elif status_code == 401:
                    logger.error("Authentication error - Check if your APOLLO_API_KEY is correct")
            raise
    
    def score_leads(self, leads: List[Lead]) -> List[Lead]:
        """
        Score leads by specialty relevance and location.
        
        Args:
            leads: List of leads to score
            
        Returns:
            Sorted list of leads (highest score first)
        """
        scored_leads = []
        
        for lead in leads:
            score = 0
            
            # Website presence bonus
            if lead.website and lead.website.startswith("http"):
                score += 10
            
            # Title relevance
            title_lower = lead.metadata.get("title", "").lower()
            if any(keyword in title_lower for keyword in ["owner", "ceo", "director"]):
                score += 5
            
            # Employee count (sweet spot: 5-20)
            emp_count = lead.metadata.get("employee_count", 0)
            if 5 <= emp_count <= 20:
                score += 5
            elif emp_count > 20:
                score += 2
            
            # Add score to metadata
            lead.metadata["score"] = score
            scored_leads.append(lead)
        
        # Sort by score (descending)
        scored_leads.sort(key=lambda x: x.metadata.get("score", 0), reverse=True)
        
        return scored_leads
    
    def enrich_person(
        self,
        email: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        organization_name: Optional[str] = None,
        domain: Optional[str] = None
    ) -> Dict:
        """
        Enrich a person's data using Apollo's People Match API.
        
        Uses: v1/people/match
        Credit Consumption: CONSUMES CREDITS (1 credit per match)
        
        Args:
            email: Person's email address
            first_name: Person's first name
            last_name: Person's last name
            organization_name: Organization name
            domain: Organization domain
            
        Returns:
            Dictionary with enriched person data
            
        Raises:
            requests.exceptions.RequestException: On API errors
        """
        params = {
            # Note: api_key now in X-Api-Key header (not in body)
        }
        
        if email:
            params["email"] = email
        if first_name:
            params["first_name"] = first_name
        if last_name:
            params["last_name"] = last_name
        if organization_name:
            params["organization_name"] = organization_name
        if domain:
            params["domain"] = domain
        
        try:
            logger.info(f"Apollo API: Enriching person (CONSUMES CREDITS) - {email or f'{first_name} {last_name}'}")
            response = requests.post(
                f"{self.base_url}/people/match",
                json=params,
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            
            person = data.get("person", {})
            logger.info(f"Apollo API: Successfully enriched person - {person.get('email', 'N/A')}")
            return person
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Apollo API enrichment error: {e}")
            if e.response is not None:
                status_code = e.response.status_code
                logger.error(f"Status Code: {status_code} - Body: {e.response.text}")
                if status_code == 402:
                    logger.error("Payment required - Check your Apollo credit balance")
            raise
    
    def enrich_organization(
        self,
        domain: Optional[str] = None,
        name: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Dict:
        """
        Enrich an organization's data using Apollo's Organization Enrich API.
        
        Uses: v1/organizations/enrich
        Credit Consumption: CONSUMES CREDITS (1 credit per enrichment)
        
        Args:
            domain: Organization domain (e.g., "example.com")
            name: Organization name
            organization_id: Apollo organization ID
            
        Returns:
            Dictionary with enriched organization data
            
        Raises:
            requests.exceptions.RequestException: On API errors
        """
        params = {
            # Note: api_key now in X-Api-Key header (not in body)
        }
        
        if domain:
            params["domain"] = domain
        if name:
            params["name"] = name
        if organization_id:
            params["organization_id"] = organization_id
        
        try:
            logger.info(f"Apollo API: Enriching organization (CONSUMES CREDITS) - {domain or name or organization_id}")
            response = requests.post(
                f"{self.base_url}/organizations/enrich",
                json=params,
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            
            org = data.get("organization", {})
            logger.info(f"Apollo API: Successfully enriched organization - {org.get('name', 'N/A')}")
            return org
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Apollo API organization enrichment error: {e}")
            if e.response is not None:
                status_code = e.response.status_code
                logger.error(f"Status Code: {status_code} - Body: {e.response.text}")
                if status_code == 402:
                    logger.error("Payment required - Check your Apollo credit balance")
            raise
    
    def bulk_enrich_people(
        self,
        people: List[Dict[str, Optional[str]]]
    ) -> List[Dict]:
        """
        Bulk enrich multiple people using Apollo's Bulk People Match API.
        
        Uses: v1/people/bulk_match
        Credit Consumption: CONSUMES CREDITS (1 credit per person matched)
        
        Args:
            people: List of dictionaries, each containing person data:
                   [{"email": "...", "first_name": "...", "last_name": "...", ...}, ...]
                   
        Returns:
            List of enriched person dictionaries
            
        Raises:
            requests.exceptions.RequestException: On API errors
        """
        params = {
            # Note: api_key now in X-Api-Key header (not in body)
            "people": people
        }
        
        try:
            logger.info(f"Apollo API: Bulk enriching {len(people)} people (CONSUMES CREDITS)")
            response = requests.post(
                f"{self.base_url}/people/bulk_match",
                json=params,
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            
            enriched_people = data.get("people", [])
            logger.info(f"Apollo API: Successfully enriched {len(enriched_people)} people")
            return enriched_people
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Apollo API bulk enrichment error: {e}")
            if e.response is not None:
                status_code = e.response.status_code
                logger.error(f"Status Code: {status_code} - Body: {e.response.text}")
                if status_code == 402:
                    logger.error("Payment required - Check your Apollo credit balance")
            raise
    
    def bulk_enrich_organizations(
        self,
        organizations: List[Dict[str, Optional[str]]]
    ) -> List[Dict]:
        """
        Bulk enrich multiple organizations using Apollo's Bulk Organization Enrich API.
        
        Uses: v1/organizations/bulk_enrich
        Credit Consumption: CONSUMES CREDITS (1 credit per organization enriched)
        
        Args:
            organizations: List of dictionaries, each containing organization data:
                           [{"domain": "...", "name": "...", ...}, ...]
                           
        Returns:
            List of enriched organization dictionaries
            
        Raises:
            requests.exceptions.RequestException: On API errors
        """
        params = {
            # Note: api_key now in X-Api-Key header (not in body)
            "organizations": organizations
        }
        
        try:
            logger.info(f"Apollo API: Bulk enriching {len(organizations)} organizations (CONSUMES CREDITS)")
            response = requests.post(
                f"{self.base_url}/organizations/bulk_enrich",
                json=params,
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            
            enriched_orgs = data.get("organizations", [])
            logger.info(f"Apollo API: Successfully enriched {len(enriched_orgs)} organizations")
            return enriched_orgs
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Apollo API bulk organization enrichment error: {e}")
            if e.response is not None:
                status_code = e.response.status_code
                logger.error(f"Status Code: {status_code} - Body: {e.response.text}")
                if status_code == 402:
                    logger.error("Payment required - Check your Apollo credit balance")
            raise
    
    def enrich_lead(self, lead: Lead) -> Lead:
        """
        Enrich a single lead with additional data using Apollo's enrichment APIs.
        
        This is a convenience method that enriches both person and organization data.
        Credit Consumption: CONSUMES CREDITS (2 credits: 1 for person + 1 for organization)
        
        Args:
            lead: Lead to enrich
            
        Returns:
            Enriched lead with updated metadata
        """
        try:
            # Enrich person data if email is available
            if lead.email:
                person_data = self.enrich_person(
                    email=lead.email,
                    first_name=lead.name.split()[0] if lead.name else None,
                    last_name=" ".join(lead.name.split()[1:]) if lead.name and len(lead.name.split()) > 1 else None,
                    organization_name=lead.company_name
                )
                # Update lead metadata with enriched person data
                lead.metadata.update({
                    "enriched_person": person_data,
                    "enriched_at": person_data.get("updated_at", "")
                })
            
            # Enrich organization data if website/domain is available
            if lead.website:
                # Extract domain from website
                domain = lead.website.replace("http://", "").replace("https://", "").split("/")[0]
                org_data = self.enrich_organization(
                    domain=domain,
                    name=lead.company_name
                )
                # Update lead metadata with enriched organization data
                lead.metadata.update({
                    "enriched_organization": org_data,
                    "organization_enriched_at": org_data.get("updated_at", "")
                })
            
            return lead
            
        except Exception as e:
            logger.warning(f"Failed to enrich lead {lead.email}: {e}. Returning lead as-is.")
            return lead
