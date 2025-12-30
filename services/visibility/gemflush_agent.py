"""
GEMflush Visibility Agent.

Fetches audit scores and competitor comparisons for evidence injection.
"""
import os
import requests
from typing import Dict, Optional, List


class GEMflushAgent:
    """
    GEMflush Visibility API wrapper.
    
    Critical design: Atomic service - handles all visibility data.
    Single outcome: Return audit scores and competitor comparisons.
    """
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize GEMflush Agent.
        
        Args:
            api_key: GEMflush API key (defaults to GEMFLUSH_API_KEY env var)
            base_url: API base URL (defaults to GEMFLUSH_API_URL env var)
        """
        self.api_key = api_key or os.getenv("GEMFLUSH_API_KEY")
        self.base_url = base_url or os.getenv(
            "GEMFLUSH_API_URL",
            "https://api.gemflush.com/v1"
        )
        
        if not self.api_key:
            raise ValueError("GEMFLUSH_API_KEY not found in environment")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
    
    def get_audit(
        self,
        clinic_id: str,
        competitors: Optional[List[str]] = None
    ) -> Dict:
        """
        Get audit score for a clinic with competitor comparison.
        
        Args:
            clinic_id: Clinic identifier (can be website, name, or ID)
            competitors: List of competitor names/websites to compare
            
        Returns:
            Dictionary with audit scores and comparisons
        """
        params = {
            "clinic_id": clinic_id,
        }
        
        if competitors:
            params["competitors"] = ",".join(competitors)
        
        try:
            response = requests.get(
                f"{self.base_url}/audit",
                params=params,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"GEMflush API error: {e}")
            return {
                "error": str(e),
                "clinic_id": clinic_id,
                "visibility_score": 0,
                "competitors": [],
            }
    
    def get_competitor_comparison(
        self,
        clinic_id: str,
        competitor_name: str
    ) -> Dict:
        """
        Get specific competitor comparison.
        
        Args:
            clinic_id: Clinic identifier
            competitor_name: Competitor name/website
            
        Returns:
            Comparison dictionary with delta score
        """
        audit_data = self.get_audit(clinic_id, competitors=[competitor_name])
        
        if "error" in audit_data:
            return audit_data
        
        # Extract comparison data
        clinic_score = audit_data.get("visibility_score", 0)
        competitor_score = audit_data.get("competitor_scores", {}).get(
            competitor_name, 0
        )
        
        delta = clinic_score - competitor_score
        
        return {
            "clinic_id": clinic_id,
            "clinic_score": clinic_score,
            "competitor_name": competitor_name,
            "competitor_score": competitor_score,
            "delta_score": delta,
            "percentage_delta": round((delta / competitor_score * 100) if competitor_score > 0 else 0, 1),
        }
    
    def format_evidence_message(
        self,
        comparison_data: Dict,
        include_full_audit: bool = False
    ) -> str:
        """
        Format evidence data into persuasive message.
        
        Args:
            comparison_data: Comparison dictionary from get_competitor_comparison
            include_full_audit: Whether to include full audit details
            
        Returns:
            Formatted evidence message
        """
        delta = comparison_data.get("delta_score", 0)
        competitor = comparison_data.get("competitor_name", "competitors")
        percentage = comparison_data.get("percentage_delta", 0)
        
        if delta < 0:
            message = (
                f"Quick insight: Your clinic shows {abs(percentage)}% "
                f"less visibility than {competitor} in AI-powered patient searches. "
                f"Our knowledge graph publishing feature can help you actively raise your AI visibility. "
            )
        else:
            message = (
                f"Great news: Your clinic shows {abs(percentage)}% "
                f"more visibility than {competitor}, but there's still room to grow. "
                f"Knowledge graph publishing can help you maintain and improve this advantage. "
            )
        
        if include_full_audit:
            message += (
                f"I can show you the full audit breakdown and how knowledge graph publishing "
                f"can help maximize your patient acquisition on a short call."
            )
        else:
            message += (
                f"I can show you how knowledge graph publishing works on a short call."
            )
        
        return message
