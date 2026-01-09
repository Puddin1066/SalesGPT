"""
Analytics service for A/B testing and performance tracking.

Exports:
- ABTestManager: Email variant testing
- ApolloABManager: Apollo search configuration testing
- MetricsTracker: Performance metrics tracking
- RecommendationEngine: Optimization recommendations
"""

from services.analytics.ab_test_manager import ABTestManager, EmailVariant
from services.analytics.apollo_ab_manager import ApolloABManager, ApolloSearchConfig
from services.analytics.metrics_tracker import MetricsTracker
from services.analytics.recommendations import RecommendationEngine

__all__ = [
    "ABTestManager",
    "EmailVariant",
    "ApolloABManager",
    "ApolloSearchConfig",
    "MetricsTracker",
    "RecommendationEngine"
]

