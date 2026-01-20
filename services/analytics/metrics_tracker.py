"""
Metrics Tracker.

Tracks performance metrics for A/B tests:
- Email variant performance
- Apollo config performance
- Niche performance
- Time-based trends
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict


class MetricsTracker:
    """Tracks and analyzes performance metrics."""
    
    def __init__(self, state_manager):
        """
        Initialize Metrics Tracker.
        
        Args:
            state_manager: StateManager instance for querying leads
        """
        self.state = state_manager
    
    def get_variant_performance(
        self,
        variant_code: str,
        days_back: int = 30
    ) -> Dict:
        """
        Get performance metrics for email variant.
        
        Args:
            variant_code: Email variant code
            days_back: Number of days to look back
            
        Returns:
            Dictionary with performance metrics
        """
        cutoff = datetime.now() - timedelta(days=days_back)
        
        try:
            all_leads = self.state.get_all_leads()
            variant_leads = [
                data for data in all_leads
                if data.get("variant_code") == variant_code
                and self._parse_datetime(data.get("email_sent_at")) > cutoff
            ]
            
            if not variant_leads:
                return {"error": "No data"}
            
            sent = len(variant_leads)
            replied = sum(1 for l in variant_leads if l.get("reply_received_at"))
            positive = sum(
                1 for l in variant_leads
                if l.get("reply_intent") in ["interested", "curious"]
            )
            booked = sum(1 for l in variant_leads if l.get("booked_at"))
            closed = sum(1 for l in variant_leads if l.get("status") == "closed")
            
            # Calculate time to reply
            reply_times = []
            for lead in variant_leads:
                if lead.get("reply_received_at") and lead.get("email_sent_at"):
                    sent_time = self._parse_datetime(lead["email_sent_at"])
                    replied_time = self._parse_datetime(lead["reply_received_at"])
                    if sent_time and replied_time:
                        hours = (replied_time - sent_time).total_seconds() / 3600
                        reply_times.append(hours)
            
            avg_time_to_reply = sum(reply_times) / len(reply_times) if reply_times else 0
            
            # Calculate avg deal value
            deal_values = [l.get("deal_value", 0) for l in variant_leads if l.get("deal_value")]
            avg_deal_value = sum(deal_values) / len(deal_values) if deal_values else 0
            
            return {
                "variant_code": variant_code,
                "sent_count": sent,
                "reply_rate": round(replied / sent * 100, 2) if sent > 0 else 0,
                "positive_reply_rate": round(positive / replied * 100, 2) if replied > 0 else 0,
                "booking_rate": round(booked / sent * 100, 2) if sent > 0 else 0,
                "close_rate": round(closed / sent * 100, 2) if sent > 0 else 0,
                "avg_time_to_reply_hours": round(avg_time_to_reply, 1),
                "avg_deal_value": round(avg_deal_value, 2)
            }
        except Exception as e:
            print(f"Error getting variant performance: {e}")
            return {"error": str(e)}
    
    def get_apollo_config_performance(
        self,
        config_code: str,
        days_back: int = 30
    ) -> Dict:
        """
        Get performance metrics for Apollo config.
        
        Args:
            config_code: Apollo config code
            days_back: Number of days to look back
            
        Returns:
            Dictionary with performance metrics
        """
        cutoff = datetime.now() - timedelta(days=days_back)
        
        try:
            all_leads = self.state.get_all_leads()
            config_leads = [
                data for data in all_leads
                if data.get("apollo_config_code") == config_code
                and self._parse_datetime(data.get("email_sent_at")) > cutoff
            ]
            
            if not config_leads:
                return {"error": "No data"}
            
            sent = len(config_leads)
            scores = [l.get("score", 0) for l in config_leads if l.get("score")]
            avg_score = sum(scores) / len(scores) if scores else 0
            replied = sum(1 for l in config_leads if l.get("reply_received_at"))
            booked = sum(1 for l in config_leads if l.get("booked_at"))
            closed = sum(1 for l in config_leads if l.get("status") == "closed")
            
            return {
                "config_code": config_code,
                "leads_sourced": sent,
                "avg_lead_score": round(avg_score, 1),
                "reply_rate": round(replied / sent * 100, 2) if sent > 0 else 0,
                "booking_rate": round(booked / sent * 100, 2) if sent > 0 else 0,
                "close_rate": round(closed / sent * 100, 2) if sent > 0 else 0
            }
        except Exception as e:
            print(f"Error getting Apollo config performance: {e}")
            return {"error": str(e)}
    
    def get_niche_performance(
        self,
        dimension: str,  # "specialty", "location", "score_tier", "elm_route"
        days_back: int = 30
    ) -> List[Dict]:
        """
        Analyze performance by niche/segment.
        
        Args:
            dimension: Dimension to analyze by
            days_back: Number of days to look back
            
        Returns:
            List of niches with performance metrics
        """
        cutoff = datetime.now() - timedelta(days=days_back)
        
        try:
            all_leads = self.state.get_all_leads()
            recent_leads = [
                data for data in all_leads
                if data.get("email_sent_at")
                and self._parse_datetime(data.get("email_sent_at")) > cutoff
            ]
            
            # Group by dimension
            niches = defaultdict(list)
            for data in recent_leads:
                if dimension == "specialty":
                    key = data.get("specialty", "Unknown")
                elif dimension == "market":
                    key = data.get("market", "Unknown")
                elif dimension == "persona":
                    key = data.get("persona", "Unknown")
                elif dimension == "location":
                    key = data.get("location", "Unknown")
                elif dimension == "score_tier":
                    score = data.get("score", 0)
                    key = "A (15+)" if score >= 15 else "B (10-14)" if score >= 10 else "C (<10)"
                elif dimension == "elm_route":
                    key = data.get("persuasion_route", "Unknown")
                else:
                    key = "Unknown"
                
                niches[key].append(data)
            
            # Calculate metrics
            results = []
            for niche_name, leads in niches.items():
                sent = len(leads)
                replied = sum(1 for l in leads if l.get("reply_received_at"))
                booked = sum(1 for l in leads if l.get("booked_at"))
                closed = sum(1 for l in leads if l.get("status") == "closed")
                free_signed_up = sum(1 for l in leads if l.get("free_signup_at"))
                paid_pro = sum(1 for l in leads if l.get("paid_pro_at"))
                
                results.append({
                    "niche": niche_name,
                    "sent_count": sent,
                    "reply_rate": round(replied / sent * 100, 2) if sent > 0 else 0,
                    "booking_rate": round(booked / sent * 100, 2) if sent > 0 else 0,
                    "close_rate": round(closed / sent * 100, 2) if sent > 0 else 0,
                    "free_signup_rate": round(free_signed_up / sent * 100, 2) if sent > 0 else 0,
                    "paid_pro_rate": round(paid_pro / sent * 100, 2) if sent > 0 else 0,
                    # ROI proxy: weight paid_pro highest, then free signup, then close
                    "roi_score": round(
                        ((paid_pro / sent) * 100) * 10
                        + ((free_signed_up / sent) * 100) * 2
                        + ((closed / sent) * 100) * 5,
                        2
                    ) if sent > 0 else 0
                })
            
            results.sort(key=lambda x: x["roi_score"], reverse=True)
            return results
        except Exception as e:
            print(f"Error getting niche performance: {e}")
            return []
    
    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string to datetime object."""
        if not dt_str:
            return None
        try:
            if isinstance(dt_str, str):
                # Try ISO format first
                try:
                    return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                except ValueError:
                    # Try other formats
                    for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S']:
                        try:
                            return datetime.strptime(dt_str, fmt)
                        except ValueError:
                            continue
            return None
        except Exception:
            return None

