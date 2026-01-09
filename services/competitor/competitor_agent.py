"""
Competitor Research Agent.

Generates mock local competitors and performs competitive analysis.
Uses GEMflush for visibility comparisons.

Critical design: Atomic service - handles all competitor research.
Single outcome: Return competitive analysis with competitor data.
"""
import hashlib
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class Competitor:
    """Competitor data structure."""
    name: str
    location: str
    specialty: str
    has_kg: bool
    wikidata_url: Optional[str] = None
    wikidata_qid: Optional[str] = None


@dataclass
class CompetitiveAnalysis:
    """Competitive analysis data structure."""
    lead_score: int
    competitor_score: int
    gap: float
    gap_percentage: float
    referral_multiplier: float
    competitor_name: str
    competitor_has_kg: bool
    competitor_kg_url: Optional[str] = None
    competitor_kg_qid: Optional[str] = None


class CompetitorAgent:
    """
    Competitor research agent for finding and analyzing local competitors.
    
    Critical design: Atomic service - can be edited independently.
    Single outcome: Return competitive analysis with mock competitor data.
    """
    
    def __init__(self, visibility_agent=None):
        """
        Initialize Competitor Agent.
        
        Args:
            visibility_agent: GEMflushAgent instance (injected for dependency)
        """
        self.visibility_agent = visibility_agent
    
    def generate_mock_competitors(
        self,
        company_name: str,
        location: str,
        specialty: str,
        count: int = 3
    ) -> List[Competitor]:
        """
        Generate mock local competitors based on location and specialty.
        Deterministic - same inputs always produce same competitors.
        No external API calls.
        
        Args:
            company_name: Company name (for hash seed)
            location: Location/geography
            specialty: Medical specialty
            count: Number of competitors to generate
            
        Returns:
            List of Competitor objects
        """
        # Deterministic competitor names based on hash
        lead_hash = hashlib.md5(f"{company_name}{location}".encode()).hexdigest()
        
        # Specialty-specific competitor name patterns
        specialty_patterns = {
            "Dental": ["SmileCare", "BrightSmile", "PerfectTeeth", "Elite Dental"],
            "Medical": ["HealthCare", "Wellness", "Prime Medical", "Advanced Care"],
            "Healthcare": ["CarePlus", "HealthFirst", "MedGroup", "Community Health"],
            "default": ["Competitor A", "Competitor B", "Competitor C"]
        }
        
        pattern = specialty_patterns.get(specialty, specialty_patterns["default"])
        location_suffix = location.split(",")[0] if "," in location else location
        
        competitors = []
        for i in range(count):
            comp_hash = int(lead_hash[i*2:(i+1)*2], 16)
            name_base = pattern[i % len(pattern)]
            has_kg = (comp_hash % 3) == 0  # 33% have KG (deterministic)
            
            competitors.append(Competitor(
                name=f"{name_base} {specialty} - {location_suffix}",
                location=location,
                specialty=specialty,
                has_kg=has_kg,
                wikidata_url=f"https://www.wikidata.org/wiki/Q{1000000 + comp_hash}" if has_kg else None,
                wikidata_qid=f"Q{1000000 + comp_hash}" if has_kg else None
            ))
        
        return competitors
    
    def get_competitive_analysis(
        self,
        clinic_id: str,
        competitor: Competitor
    ) -> CompetitiveAnalysis:
        """
        Get competitive analysis using GEMflush's deterministic scoring.
        No external API calls - uses existing mock system.
        
        Args:
            clinic_id: Clinic/business identifier
            competitor: Competitor object
            
        Returns:
            CompetitiveAnalysis object
        """
        if not self.visibility_agent:
            raise ValueError("Visibility agent not initialized")
        
        # Use existing GEMflush mock system
        audit = self.visibility_agent.get_audit(
            clinic_id=clinic_id,
            competitors=[competitor.name]
        )
        
        comparison = self.visibility_agent.get_competitor_comparison(
            clinic_id=clinic_id,
            competitor_name=competitor.name
        )
        
        # Calculate referral multiplier (mock estimate based on gap)
        gap = abs(comparison.get("delta_score", 0))
        referral_multiplier = max(1.2, round(1 + (gap / 50), 1))  # 1.2x to 3x more referrals
        
        # Estimate percentage gap
        gap_percentage = abs(comparison.get("percentage_delta", 0))
        
        return CompetitiveAnalysis(
            lead_score=audit.get("visibility_score", 0),
            competitor_score=comparison.get("competitor_score", 0),
            gap=comparison.get("delta_score", 0),
            gap_percentage=gap_percentage,
            referral_multiplier=referral_multiplier,
            competitor_name=competitor.name,
            competitor_has_kg=competitor.has_kg,
            competitor_kg_url=competitor.wikidata_url,
            competitor_kg_qid=competitor.wikidata_qid
        )
    
    def find_best_competitor(
        self,
        competitors: List[Competitor]
    ) -> Competitor:
        """
        Find best competitor to reference in email.
        Prefers: has KG > deterministic tie-breaker.
        
        Args:
            competitors: List of competitors
            
        Returns:
            Best competitor to reference
        """
        return max(
            competitors,
            key=lambda c: (
                c.has_kg,  # Prefer KG presence
                hash(c.name) % 100  # Deterministic tie-breaker
            )
        )

