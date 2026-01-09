"""
Recommendation Engine.

Generates data-driven optimization recommendations based on
A/B test results and performance metrics.
"""
from typing import Dict, List


class RecommendationEngine:
    """Generates optimization recommendations."""
    
    def __init__(self, metrics_tracker):
        """
        Initialize Recommendation Engine.
        
        Args:
            metrics_tracker: MetricsTracker instance
        """
        self.metrics = metrics_tracker
    
    def get_recommendations(self) -> List[Dict]:
        """
        Generate all recommendations.
        
        Returns:
            List of recommendation dictionaries
        """
        recommendations = []
        
        # 1. Email variant recommendations
        recommendations.extend(self._get_variant_recommendations())
        
        # 2. Apollo config recommendations
        recommendations.extend(self._get_apollo_recommendations())
        
        # 3. Niche recommendations
        recommendations.extend(self._get_niche_recommendations())
        
        return recommendations
    
    def _get_variant_recommendations(self) -> List[Dict]:
        """Recommend best email variants."""
        try:
            # Get all unique variants
            all_leads = self.metrics.state.get_all_leads()
            variants = set(l.get("variant_code") for l in all_leads if l.get("variant_code"))
            
            if len(variants) < 2:
                return []
            
            # Get performance for each
            variant_perf = []
            for variant in variants:
                perf = self.metrics.get_variant_performance(variant)
                if "error" not in perf and perf["sent_count"] >= 10:
                    variant_perf.append(perf)
            
            if not variant_perf:
                return []
            
            # Sort by booking rate
            variant_perf.sort(key=lambda x: x["booking_rate"], reverse=True)
            
            best = variant_perf[0]
            worst = variant_perf[-1]
            
            return [{
                "type": "email_variant",
                "priority": "high",
                "title": f"Best Email Variant: {best['variant_code']}",
                "description": f"Booking rate: {best['booking_rate']}% (vs {worst['booking_rate']}% for worst)",
                "action": f"Increase usage of variant {best['variant_code']}",
                "confidence": 0.95 if best["sent_count"] >= 50 else 0.75
            }]
        except Exception as e:
            print(f"Error getting variant recommendations: {e}")
            return []
    
    def _get_apollo_recommendations(self) -> List[Dict]:
        """Recommend best Apollo configs."""
        try:
            # This would require ApolloABManager, but we'll keep it simple for now
            # In full implementation, would query ApolloABManager.get_config_performance_report()
            return []
        except Exception as e:
            print(f"Error getting Apollo recommendations: {e}")
            return []
    
    def _get_niche_recommendations(self) -> List[Dict]:
        """Recommend best niches to target."""
        try:
            niches = self.metrics.get_niche_performance("specialty")
            
            if not niches or len(niches) < 2:
                return []
            
            best = niches[0]
            
            return [{
                "type": "niche",
                "priority": "medium",
                "title": f"Best Specialty: {best['niche']}",
                "description": f"Close rate: {best['close_rate']}% (ROI: {best['roi_score']})",
                "action": f"Target more {best['niche']} leads",
                "confidence": 0.85 if best["sent_count"] >= 30 else 0.65
            }]
        except Exception as e:
            print(f"Error getting niche recommendations: {e}")
            return []

