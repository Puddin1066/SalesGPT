"""
GEO Value Appreciation Scorer.

Scores leads by likelihood to appreciate GEO (Generative Engine Optimization) value.

Critical design: Atomic service - single responsibility.
Single outcome: Return GEO value appreciation score (0-100).
"""
from typing import Any


class GEOScorer:
    """
    Scores leads by likelihood to appreciate GEO value.
    
    Critical design: Atomic service - can be edited independently.
    Single outcome: Return GEO score (0-100).
    """
    
    @staticmethod
    def score_lead(
        lead: Any,
        visibility_score: int
    ) -> float:
        """
        Calculate GEO value appreciation score.
        
        Args:
            lead: Lead object (from ApolloAgent) with name, email, website, 
                  company_name, specialty, location, metadata attributes
            visibility_score: AI visibility score from audit
            
        Returns:
            Score 0-100 (higher = more likely to appreciate GEO)
        """
        score = 0.0
        
        # Has website = understands digital (20 points)
        if lead.website:
            score += 20.0
        
        # Low visibility = high pain (30 points)
        if visibility_score < 40:
            score += 30.0
        elif visibility_score < 60:
            score += 15.0
        
        # Decision maker title (20 points)
        title = lead.metadata.get("title", "").lower()
        if any(word in title for word in ["owner", "ceo", "founder", "director"]):
            score += 20.0
        
        # Business size sweet spot (15 points)
        emp_count = lead.metadata.get("employee_count", 0)
        if 5 <= emp_count <= 50:
            score += 15.0
        
        # Industry fit (15 points)
        if lead.specialty in ["Healthcare", "Medical", "Dental"]:
            score += 15.0
        
        return min(score, 100.0)

