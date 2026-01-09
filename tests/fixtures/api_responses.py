"""
Automated API response fixtures for GEMflush and Apollo IO.

These fixtures provide consistent, predictable mock responses for testing
and automation without consuming API credits.
"""
from typing import Dict, List, Optional


class GEMflushResponseFixtures:
    """Automated GEMflush API response fixtures."""
    
    @staticmethod
    def get_audit_response(clinic_id: str, competitors: Optional[List[str]] = None) -> Dict:
        """
        Generate automated GEMflush audit response.
        
        Args:
            clinic_id: Clinic identifier
            competitors: Optional list of competitor names
            
        Returns:
            Mock audit response matching GEMflush API format
        """
        import hashlib
        
        # Deterministic scoring
        clinic_hash = int(hashlib.md5(clinic_id.encode()).hexdigest()[:8], 16)
        base_score = 30 + (clinic_hash % 50)
        
        competitor_scores = {}
        if competitors:
            for comp in competitors:
                comp_hash = int(hashlib.md5(comp.encode()).hexdigest()[:8], 16)
                comp_score = 40 + (comp_hash % 40)
                competitor_scores[comp] = comp_score
        else:
            competitor_scores["Local Competitor"] = 65
        
        return {
            "clinic_id": clinic_id,
            "visibility_score": base_score,
            "competitor_scores": competitor_scores,
            "top_keywords": ["urgent care", "walk-in clinic", "primary care"],
            "recommendation": f"Improve AI search visibility for '{clinic_id}' by optimizing for patient-focused keywords.",
            "source": "automated_fixture"
        }
    
    @staticmethod
    def get_competitor_comparison(clinic_id: str, competitor_name: str) -> Dict:
        """Generate automated competitor comparison response."""
        audit = GEMflushResponseFixtures.get_audit_response(clinic_id, [competitor_name])
        
        clinic_score = audit["visibility_score"]
        competitor_score = list(audit["competitor_scores"].values())[0]
        delta = clinic_score - competitor_score
        
        return {
            "clinic_id": clinic_id,
            "clinic_score": clinic_score,
            "competitor_name": competitor_name,
            "competitor_score": competitor_score,
            "delta_score": delta,
            "percentage_delta": round((delta / competitor_score * 100) if competitor_score > 0 else 0, 1),
            "source": "automated_fixture"
        }


class ApolloResponseFixtures:
    """Automated Apollo IO API response fixtures."""
    
    @staticmethod
    def get_search_response(limit: int = 2) -> Dict:
        """
        Generate automated Apollo search response.
        
        Args:
            limit: Number of people to return
            
        Returns:
            Mock Apollo search response
        """
        people = []
        for i in range(limit):
            people.append({
                "first_name": f"John{i}",
                "last_name": f"Doe{i}",
                "email": f"john{i}@example.com",
                "title": "CEO" if i == 0 else "Medical Director",
                "linkedin_url": f"https://linkedin.com/in/johndoe{i}",
                "organization": {
                    "id": f"org_{i}",
                    "name": f"Example Clinic {i+1}",
                    "website_url": f"https://example{i}.com",
                    "estimated_num_employees": 10 + (i * 5)
                }
            })
        
        return {
            "people": people,
            "pagination": {
                "page": 1,
                "per_page": limit,
                "total_entries": limit
            },
            "source": "automated_fixture"
        }
    
    @staticmethod
    def get_person_enrichment_response(email: str) -> Dict:
        """Generate automated person enrichment response."""
        return {
            "person": {
                "id": f"person_{hash(email) % 10000}",
                "first_name": email.split("@")[0].split(".")[0].capitalize(),
                "last_name": "Doe",
                "email": email,
                "title": "CEO",
                "linkedin_url": f"https://linkedin.com/in/{email.split('@')[0]}",
                "updated_at": "2024-01-01T00:00:00Z",
                "source": "automated_fixture"
            }
        }
    
    @staticmethod
    def get_organization_enrichment_response(domain: str) -> Dict:
        """Generate automated organization enrichment response."""
        return {
            "organization": {
                "id": f"org_{hash(domain) % 10000}",
                "name": domain.split(".")[0].capitalize() + " Clinic",
                "website_url": f"https://{domain}",
                "estimated_num_employees": 15,
                "updated_at": "2024-01-01T00:00:00Z",
                "source": "automated_fixture"
            }
        }


# Convenience functions for easy import
def gemflush_audit(clinic_id: str, competitors: Optional[List[str]] = None) -> Dict:
    """Quick access to GEMflush audit fixture."""
    return GEMflushResponseFixtures.get_audit_response(clinic_id, competitors)


def gemflush_comparison(clinic_id: str, competitor_name: str) -> Dict:
    """Quick access to GEMflush comparison fixture."""
    return GEMflushResponseFixtures.get_competitor_comparison(clinic_id, competitor_name)


def apollo_search(limit: int = 2) -> Dict:
    """Quick access to Apollo search fixture."""
    return ApolloResponseFixtures.get_search_response(limit)


def apollo_enrich_person(email: str) -> Dict:
    """Quick access to Apollo person enrichment fixture."""
    return ApolloResponseFixtures.get_person_enrichment_response(email)


def apollo_enrich_org(domain: str) -> Dict:
    """Quick access to Apollo organization enrichment fixture."""
    return ApolloResponseFixtures.get_organization_enrichment_response(domain)

