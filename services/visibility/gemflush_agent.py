"""
GEMflush Visibility Agent.

Supports both real API calls (alex@gemflush.com) and LLM-based simulation.
Automated responses for testing and development.
"""
import os
import json
import requests
import logging
from typing import Dict, Optional, List

# Optional import for LLM simulation
try:
    from litellm import completion
    HAS_LITELLM = True
except ImportError:
    HAS_LITELLM = False

logger = logging.getLogger(__name__)


class GEMflushAgent:
    """
    GEMflush Visibility Audit Agent.
    
    Supports:
    - Real API calls to GEMflush API (if API key/endpoint configured)
    - LLM-based simulation (fallback)
    - Automated mock responses for testing
    
    Critical design: Zero-dependency emulation with optional real API support.
    Single outcome: Return realistic audit scores for sales persuasion.
    """
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        api_base_url: Optional[str] = None,
        use_real_api: bool = False
    ):
        """
        Initialize GEMflush Agent.
        
        Args:
            model_name: LLM model for simulation (default: gpt-3.5-turbo)
            api_key: GEMflush API key (from GEMFLUSH_API_KEY env var)
            api_base_url: GEMflush API base URL (from GEMFLUSH_API_URL env var)
            use_real_api: Force use of real API (default: auto-detect from env)
        """
        self.model_name = model_name or os.getenv("GPT_MODEL", "gpt-3.5-turbo")
        self.api_key = api_key or os.getenv("GEMFLUSH_API_KEY")
        self.api_base_url = api_base_url or os.getenv("GEMFLUSH_API_URL", "https://api.gemflush.com/v1")
        
        # Auto-detect if we should use real API
        if use_real_api or (self.api_key and os.getenv("GEMFLUSH_USE_REAL_API", "false").lower() == "true"):
            self.use_real_api = True
            logger.info("GEMflush Agent: Using REAL API mode")
        else:
            self.use_real_api = False
            logger.info("GEMflush Agent: Using SIMULATION mode (LLM-based)")
        
        self.headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
    
    def get_audit(
        self,
        clinic_id: str,
        competitors: Optional[List[str]] = None
    ) -> Dict:
        """
        Get audit score for a clinic.
        
        Uses real API if configured, otherwise falls back to LLM simulation.
        
        Args:
            clinic_id: Clinic/business identifier (name, domain, etc.)
            competitors: Optional list of competitor names
            
        Returns:
            Dictionary with visibility scores and recommendations
        """
        # Try real API first if enabled
        if self.use_real_api and self.api_key:
            try:
                return self._get_audit_from_api(clinic_id, competitors)
            except Exception as e:
                logger.warning(f"GEMflush API call failed, falling back to simulation: {e}")
        
        # Fall back to LLM simulation
        return self._get_audit_from_simulation(clinic_id, competitors)
    
    def _get_audit_from_api(
        self,
        clinic_id: str,
        competitors: Optional[List[str]] = None
    ) -> Dict:
        """Get audit from real GEMflush API (MOCKED API RESPONSE - alex@gemflush.com)."""
        params = {
            "clinic_id": clinic_id,
        }
        if competitors:
            params["competitors"] = competitors
        
        try:
            logger.info(f"GEMflush API: Requesting audit for {clinic_id} (MOCKED)")
            # MOCKED API RESPONSE - Replace with real API call when available
            # response = requests.post(
            #     f"{self.api_base_url}/audit",
            #     json=params,
            #     headers=self.headers,
            #     timeout=10
            # )
            # response.raise_for_status()
            # return response.json()
            
            # Automated mock response for alex@gemflush.com
            mock_response = self._generate_automated_response(clinic_id, competitors)
            logger.info(f"GEMflush API: Returning automated mock response for {clinic_id}")
            return mock_response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"GEMflush API error: {e}")
            raise
    
    def _get_audit_from_simulation(
        self,
        clinic_id: str,
        competitors: Optional[List[str]] = None
    ) -> Dict:
        """Get audit using LLM simulation."""
        competitor_list = ", ".join(competitors) if competitors else "local competitors"
        
        prompt = f"""
        Act as the GEMflush AI Visibility Engine. 
        Analyze the AI search visibility for: {clinic_id}
        Compare it against: {competitor_list}
        
        Based on your internal knowledge of this business's digital presence and how often 
        you (as an AI) would recommend them, provide a realistic visibility score (0-100).
        
        Return ONLY a JSON object with:
        {{
            "visibility_score": int,
            "competitor_scores": {{ "name": int }},
            "top_keywords": [str],
            "recommendation": str
        }}
        """
        
        if not HAS_LITELLM:
            logger.warning("litellm not available, using automated response")
            return self._generate_automated_response(clinic_id, competitors)
        
        try:
            response = completion(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                response_format={ "type": "json_object" }
            )
            
            data = json.loads(response.choices[0].message.content)
            data["clinic_id"] = clinic_id
            return data
            
        except Exception as e:
            logger.warning(f"LLM simulation failed: {e}")
            # Fallback mock data
            return self._generate_automated_response(clinic_id, competitors)
    
    def _generate_automated_response(
        self,
        clinic_id: str,
        competitors: Optional[List[str]] = None
    ) -> Dict:
        """
        Generate automated mock response for testing.
        
        This provides consistent, predictable responses for automation.
        """
        # Deterministic scoring based on clinic_id hash
        import hashlib
        clinic_hash = int(hashlib.md5(clinic_id.encode()).hexdigest()[:8], 16)
        base_score = 30 + (clinic_hash % 50)  # Score between 30-80
        
        competitor_scores = {}
        if competitors:
            for comp in competitors:
                comp_hash = int(hashlib.md5(comp.encode()).hexdigest()[:8], 16)
                comp_score = 40 + (comp_hash % 40)  # Score between 40-80
                competitor_scores[comp] = comp_score
        else:
            competitor_scores["Local Competitor"] = 65
        
        keywords = ["urgent care", "walk-in clinic", "primary care", "telemedicine"]
        
        return {
            "clinic_id": clinic_id,
            "visibility_score": base_score,
            "competitor_scores": competitor_scores,
            "top_keywords": keywords[:3],
            "recommendation": f"Improve AI search visibility for '{clinic_id}' by optimizing for patient-focused keywords.",
            "source": "automated_mock"  # Indicates this is an automated response
        }

    def get_competitor_comparison(
        self,
        clinic_id: str,
        competitor_name: str
    ) -> Dict:
        """Get specific competitor comparison (Simulated)."""
        audit_data = self.get_audit(clinic_id, competitors=[competitor_name])
        
        clinic_score = audit_data.get("visibility_score", 0)
        competitor_score = list(audit_data.get("competitor_scores", {}).values())[0]
        
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
        """Format simulated data into a persuasive sales message."""
        delta = comparison_data.get("delta_score", 0)
        competitor = comparison_data.get("competitor_name", "competitors")
        percentage = abs(comparison_data.get("percentage_delta", 0))
        
        if delta < 0:
            message = (
                f"Quick insight: Based on our AI visibility audit, your clinic currently shows {percentage}% "
                f"less visibility than {competitor} in GPT-based patient searches. "
            )
        else:
            message = (
                f"I ran an AI visibility audit and you're actually doing well compared to {competitor}, "
                f"beating them by about {percentage}%. However, there's a specific gap in your 'urgent care' visibility. "
            )
        
        if include_full_audit:
            message += "I can show you the full breakdown of these AI search metrics on a short call."
        else:
            message += "Would you be open to seeing the full data report?"
            
        return message
