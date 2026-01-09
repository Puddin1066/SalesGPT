"""
Apollo A/B Test Manager.

Manages Apollo search configuration testing.
Tests: geography strategy, employee ranges, title filters, website requirements.
"""
import math
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional


class GeographyStrategy(Enum):
    CITY_SPECIFIC = "city"
    METRO_AREA = "metro"
    STATE_WIDE = "state"
    MULTI_CITY = "multi"


class EmployeeRangeStrategy(Enum):
    MICRO = "micro"          # 1-5
    SMALL = "small"          # 5-15
    MEDIUM = "medium"        # 15-50
    LARGE = "large"          # 50-200
    MIXED_SMALL = "mixed_sm" # 1-20
    MIXED_MEDIUM = "mixed_md"# 10-50


class TitleStrategy(Enum):
    C_LEVEL_ONLY = "c_level"
    OWNERS_ONLY = "owners"
    DECISION_MAKERS = "decision"
    BROAD = "broad"
    MEDICAL_SPECIFIC = "medical"


@dataclass
class ApolloSearchConfig:
    """Apollo search configuration for A/B testing."""
    geography_strategy: GeographyStrategy
    geography_value: str
    employee_range: EmployeeRangeStrategy
    title_strategy: TitleStrategy
    require_website: bool
    specialty: str
    
    def to_code(self) -> str:
        """Generate config code."""
        website_code = "web" if self.require_website else "noweb"
        return f"{self.geography_strategy.value}-{self.employee_range.value}-{self.title_strategy.value}-{website_code}"
    
    def to_apollo_params(self) -> Dict:
        """Convert to Apollo API search parameters."""
        # Define employee ranges
        employee_ranges = {
            EmployeeRangeStrategy.MICRO: (1, 5),
            EmployeeRangeStrategy.SMALL: (5, 15),
            EmployeeRangeStrategy.MEDIUM: (15, 50),
            EmployeeRangeStrategy.LARGE: (50, 200),
            EmployeeRangeStrategy.MIXED_SMALL: (1, 20),
            EmployeeRangeStrategy.MIXED_MEDIUM: (10, 50)
        }
        
        min_emp, max_emp = employee_ranges[self.employee_range]
        
        # Define title lists
        title_lists = {
            TitleStrategy.C_LEVEL_ONLY: ["CEO", "CFO", "COO", "President"],
            TitleStrategy.OWNERS_ONLY: ["Owner", "Managing Partner", "Principal"],
            TitleStrategy.DECISION_MAKERS: [
                "CEO", "Owner", "Director", "Partner", "President", "Medical Director"
            ],
            TitleStrategy.BROAD: [
                "CEO", "Owner", "Director", "Manager", "Partner", "Coordinator"
            ],
            TitleStrategy.MEDICAL_SPECIFIC: [
                "MD", "DO", "DDS", "Medical Director", "Physician Owner"
            ]
        }
        
        return {
            "min_employees": min_emp,
            "max_employees": max_emp,
            "title_filters": title_lists[self.title_strategy],
            "has_website": self.require_website
        }


class ApolloABManager:
    """Manages Apollo search configuration A/B testing."""
    
    def __init__(self, state_manager):
        """
        Initialize Apollo AB Manager.
        
        Args:
            state_manager: StateManager instance for querying leads
        """
        self.state = state_manager
        self.test_configs = self._initialize_configs()
    
    def _initialize_configs(self) -> List[ApolloSearchConfig]:
        """Initialize test configurations."""
        configs = []
        base_geo = "New York, NY"
        base_specialty = "Dermatology"
        
        # Test employee ranges
        for emp_range in [
            EmployeeRangeStrategy.MICRO,
            EmployeeRangeStrategy.SMALL,
            EmployeeRangeStrategy.MEDIUM
        ]:
            configs.append(ApolloSearchConfig(
                geography_strategy=GeographyStrategy.CITY_SPECIFIC,
                geography_value=base_geo,
                employee_range=emp_range,
                title_strategy=TitleStrategy.DECISION_MAKERS,
                require_website=True,
                specialty=base_specialty
            ))
        
        # Test title strategies
        for title_strat in [
            TitleStrategy.C_LEVEL_ONLY,
            TitleStrategy.OWNERS_ONLY,
            TitleStrategy.DECISION_MAKERS
        ]:
            configs.append(ApolloSearchConfig(
                geography_strategy=GeographyStrategy.CITY_SPECIFIC,
                geography_value=base_geo,
                employee_range=EmployeeRangeStrategy.SMALL,
                title_strategy=title_strat,
                require_website=True,
                specialty=base_specialty
            ))
        
        # Test website requirement
        for require_web in [True, False]:
            configs.append(ApolloSearchConfig(
                geography_strategy=GeographyStrategy.CITY_SPECIFIC,
                geography_value=base_geo,
                employee_range=EmployeeRangeStrategy.SMALL,
                title_strategy=TitleStrategy.DECISION_MAKERS,
                require_website=require_web,
                specialty=base_specialty
            ))
        
        return configs
    
    def get_next_config_to_test(self) -> ApolloSearchConfig:
        """
        Get next config using multi-armed bandit (UCB algorithm).
        
        Balances exploration (under-tested configs) with
        exploitation (best-performing configs).
        
        Returns:
            ApolloSearchConfig to test next
        """
        config_scores = []
        
        for config in self.test_configs:
            config_code = config.to_code()
            
            # Get leads for this config
            leads = self._get_leads_by_apollo_config(config_code)
            
            if not leads or len(leads) < 5:
                # Under-sampled: high exploration bonus
                ucb_score = float('inf')
            else:
                # Calculate success rate (closed deals)
                closed = sum(1 for l in leads if l.get("status") == "closed")
                success_rate = closed / len(leads) if leads else 0
                
                # Calculate UCB
                total_trials = self._get_total_apollo_trials()
                exploration_bonus = 2.0 * math.sqrt(
                    math.log(total_trials) / len(leads) if total_trials > 0 and len(leads) > 0 else 1
                )
                ucb_score = success_rate + exploration_bonus
            
            config_scores.append((config, ucb_score))
        
        # Return config with highest UCB score
        config_scores.sort(key=lambda x: x[1], reverse=True)
        return config_scores[0][0]
    
    def _get_leads_by_apollo_config(self, config_code: str) -> List[Dict]:
        """Get all leads sourced with specific Apollo config."""
        try:
            # Use state manager to query leads
            all_leads = self.state.get_all_leads()
            return [
                data for data in all_leads
                if data.get("apollo_config_code") == config_code
            ]
        except Exception as e:
            print(f"Error getting leads by Apollo config: {e}")
            return []
    
    def _get_total_apollo_trials(self) -> int:
        """Get total number of Apollo searches across all configs."""
        try:
            all_leads = self.state.get_all_leads()
            return len([
                data for data in all_leads
                if data.get("apollo_config_code")
            ])
        except Exception as e:
            print(f"Error getting total Apollo trials: {e}")
            return 0
    
    def get_config_performance_report(self) -> List[Dict]:
        """
        Generate performance report across all Apollo configurations.
        
        Returns:
            List of dicts with config performance metrics
        """
        report = []
        
        for config in self.test_configs:
            config_code = config.to_code()
            leads = self._get_leads_by_apollo_config(config_code)
            
            if not leads:
                continue
            
            sent = len(leads)
            replied = sum(1 for l in leads if l.get("reply_received_at"))
            booked = sum(1 for l in leads if l.get("booked_at"))
            closed = sum(1 for l in leads if l.get("status") == "closed")
            
            # Calculate average lead score for this config
            scores = [l.get("score", 0) for l in leads if l.get("score")]
            avg_score = sum(scores) / len(scores) if scores else 0
            
            # Calculate cost per lead (Apollo credits)
            apollo_credits_used = 0  # Search is usually free
            enriched_count = sum(1 for l in leads if l.get("enriched", False))
            apollo_credits_used = enriched_count * 2  # 2 credits per enrichment
            
            # Calculate ROI
            avg_deal_value = 5000  # Assumed
            revenue = closed * avg_deal_value
            cost = apollo_credits_used * 1  # $1 per credit (approximate)
            roi = ((revenue - cost) / cost * 100) if cost > 0 else 0
            
            report.append({
                "config_code": config_code,
                "geography_strategy": config.geography_strategy.value,
                "employee_range": config.employee_range.value,
                "title_strategy": config.title_strategy.value,
                "website_required": config.require_website,
                "leads_sourced": sent,
                "avg_lead_score": round(avg_score, 1),
                "reply_rate": round(replied / sent * 100, 2) if sent > 0 else 0,
                "booking_rate": round(booked / sent * 100, 2) if sent > 0 else 0,
                "close_rate": round(closed / sent * 100, 2) if sent > 0 else 0,
                "apollo_credits": apollo_credits_used,
                "roi": round(roi, 1)
            })
        
        # Sort by ROI
        report.sort(key=lambda x: x["roi"], reverse=True)
        
        return report

