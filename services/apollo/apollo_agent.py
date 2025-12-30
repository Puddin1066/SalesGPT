"""
Apollo Agent - Lead sourcing + enrichment service.

Searches for leads based on geography, specialty, and website presence.
Returns enriched lead data with clinic metadata.
"""
import os
import requests
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class Lead:
    """Lead data structure."""
    name: str
    email: str
    website: str
    clinic_name: str
    specialty: str
    location: str
    metadata: Dict


class ApolloAgent:
    """
    Apollo API wrapper for lead sourcing and enrichment.
    
    Critical design: Atomic service - can be edited independently.
    Single outcome: Return scored leads based on search criteria.
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
        
        self.base_url = "https://api.apollo.io/v1"
        self.headers = {
            "Cache-Control": "no-cache",
            "Content-Type": "application/json",
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
        
        Args:
            geography: Location filter (e.g., "New York, NY")
            specialty: Medical specialty filter
            min_employees: Minimum employee count
            max_employees: Maximum employee count
            has_website: Require website presence
            limit: Maximum results to return
            
        Returns:
            List of Lead objects with enriched data
        """
        search_params = {
            "api_key": self.api_key,
            "q_keywords": specialty,
            "person_locations": [geography],
            "organization_num_employees_ranges": [
                f"{min_employees},{max_employees}"
            ],
            "person_titles": [
                "Owner", "CEO", "Medical Director", "Practice Manager"
            ],
            "page": 1,
            "per_page": min(limit, 50),
        }
        
        if has_website:
            search_params["organization_keywords"] = "website"
        
        try:
            response = requests.post(
                f"{self.base_url}/mixed_people/search",
                json=search_params,
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            
            leads = []
            for person in data.get("people", [])[:limit]:
                org = person.get("organization", {})
                
                # Extract website
                website = org.get("website_url", "") or org.get("primary_phone", "")
                
                # Only include if has website (if required)
                if has_website and not website:
                    continue
                
                lead = Lead(
                    name=f"{person.get('first_name', '')} {person.get('last_name', '')}".strip(),
                    email=person.get("email", ""),
                    website=website,
                    clinic_name=org.get("name", ""),
                    specialty=specialty,
                    location=geography,
                    metadata={
                        "title": person.get("title", ""),
                        "linkedin_url": person.get("linkedin_url", ""),
                        "organization_id": org.get("id", ""),
                        "employee_count": org.get("estimated_num_employees", 0),
                    }
                )
                leads.append(lead)
            
            return leads
            
        except requests.exceptions.RequestException as e:
            print(f"Apollo API error: {e}")
            return []
    
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
    
    def enrich_lead(self, lead: Lead) -> Lead:
        """
        Enrich a single lead with additional data.
        
        Args:
            lead: Lead to enrich
            
        Returns:
            Enriched lead
        """
        # Additional enrichment can be added here
        # For now, return as-is
        return lead
