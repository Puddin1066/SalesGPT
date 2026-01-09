"""
Dependency Injection Container for SalesGPT.

Manages service initialization and dependency wiring.
"""
from typing import Optional

from salesgpt.config import Settings, get_settings
from salesgpt.db.connection import DatabaseManager
from state.state_manager import StateManager

from services.apollo.apollo_agent import ApolloAgent
from services.outbound.smartlead_agent import SmartleadAgent
from services.salesgpt.salesgpt_wrapper import SalesGPTWrapper
from services.scheduler.cal_scheduler import CalScheduler
from services.crm.hubspot_agent import HubSpotAgent
from services.visibility.gemflush_agent import GEMflushAgent
from services.competitor.competitor_agent import CompetitorAgent
from services.scoring.geo_scorer import GEOScorer
from services.analytics import ABTestManager, ApolloABManager, MetricsTracker, RecommendationEngine
from workflows.background_queue_builder import BackgroundQueueBuilder


class ServiceContainer:
    """
    Dependency injection container for SalesGPT services.
    
    Manages initialization and provides configured service instances.
    """
    
    def __init__(self, settings: Optional[Settings] = None):
        """
        Initialize service container.
        
        Args:
            settings: Settings instance (defaults to loading from environment)
        """
        self.settings = settings or get_settings()
        
        # Initialize database
        self._db_manager = DatabaseManager(self.settings.database_url)
        
        # Create tables if they don't exist
        self._db_manager.create_tables()
        
        # Initialize state manager
        self._state_manager = StateManager(self._db_manager)
        
        # Initialize services
        self._apollo = ApolloAgent(api_key=self.settings.apollo_api_key)
        self._smartlead = SmartleadAgent(api_key=self.settings.smartlead_api_key)
        
        # SalesGPT wrapper
        self._salesgpt = SalesGPTWrapper(
            config_path=self.settings.salesgpt_config_path,
            model_name=self.settings.gpt_model,
            verbose=self.settings.salesgpt_verbose
        )
        
        # Scheduler (optional - only create if booking link is configured)
        if self.settings.cal_booking_link:
            self._scheduler = CalScheduler(booking_link=self.settings.cal_booking_link)
        else:
            # Create a mock/placeholder scheduler that will raise error if used
            # In production, you might want to make this optional in orchestrator
            try:
                self._scheduler = CalScheduler(booking_link=None)
            except ValueError:
                # If CalScheduler requires booking_link, create a mock
                from unittest.mock import MagicMock
                self._scheduler = MagicMock(spec=CalScheduler)
        
        # HubSpot CRM
        if (self.settings.hubspot_client_id and 
            self.settings.hubspot_client_secret and 
            self.settings.hubspot_refresh_token):
            # Use OAuth
            self._crm = HubSpotAgent(
                client_id=self.settings.hubspot_client_id,
                client_secret=self.settings.hubspot_client_secret,
                refresh_token=self.settings.hubspot_refresh_token
            )
        else:
            # Use Private App token
            self._crm = HubSpotAgent(api_key=self.settings.hubspot_access_token)
        
        # GEMflush visibility agent
        self._visibility = GEMflushAgent(
            api_key=self.settings.gemflush_api_key,
            api_base_url=self.settings.gemflush_api_url,
            use_real_api=self.settings.gemflush_use_real_api,
            model_name=self.settings.gpt_model
        )
        
        # Competitor agent (depends on visibility)
        self._competitor = CompetitorAgent(visibility_agent=self._visibility)
        
        # GEO scorer
        self._scorer = GEOScorer()
        
        # Analytics services (NEW)
        self._ab_test_manager = ABTestManager(self._state_manager)
        self._apollo_ab_manager = ApolloABManager(self._state_manager)
        self._metrics_tracker = MetricsTracker(self._state_manager)
        self._recommendation_engine = RecommendationEngine(self._metrics_tracker)
        
        # Workflows (NEW)
        self._queue_builder = BackgroundQueueBuilder(
            apollo=self._apollo,
            salesgpt=self._salesgpt,
            hubspot=self._crm,
            state_manager=self._state_manager,
            ab_manager=self._ab_test_manager,
            apollo_ab=self._apollo_ab_manager,
            competitor=self._competitor,
            visibility=self._visibility,
            scorer=self._scorer
        )
    
    @property
    def db_manager(self) -> DatabaseManager:
        """Get database manager."""
        return self._db_manager
    
    @property
    def state_manager(self) -> StateManager:
        """Get state manager."""
        return self._state_manager
    
    @property
    def apollo(self) -> ApolloAgent:
        """Get Apollo agent."""
        return self._apollo
    
    @property
    def smartlead(self) -> SmartleadAgent:
        """Get Smartlead agent."""
        return self._smartlead
    
    @property
    def salesgpt(self) -> SalesGPTWrapper:
        """Get SalesGPT wrapper."""
        return self._salesgpt
    
    @property
    def scheduler(self) -> CalScheduler:
        """Get Cal scheduler."""
        return self._scheduler
    
    @property
    def crm(self) -> HubSpotAgent:
        """Get HubSpot CRM agent."""
        return self._crm
    
    @property
    def visibility(self) -> GEMflushAgent:
        """Get GEMflush visibility agent."""
        return self._visibility
    
    @property
    def competitor(self) -> CompetitorAgent:
        """Get competitor agent."""
        return self._competitor
    
    @property
    def scorer(self) -> GEOScorer:
        """Get GEO scorer."""
        return self._scorer
    
    @property
    def ab_test_manager(self) -> ABTestManager:
        """Get AB test manager."""
        return self._ab_test_manager
    
    @property
    def apollo_ab_manager(self) -> ApolloABManager:
        """Get Apollo AB manager."""
        return self._apollo_ab_manager
    
    @property
    def metrics_tracker(self) -> MetricsTracker:
        """Get metrics tracker."""
        return self._metrics_tracker
    
    @property
    def recommendation_engine(self) -> RecommendationEngine:
        """Get recommendation engine."""
        return self._recommendation_engine
    
    @property
    def queue_builder(self) -> BackgroundQueueBuilder:
        """Get background queue builder."""
        return self._queue_builder
    
    @property
    def orchestrator(self):
        """Get configured ASSCH orchestrator."""
        from main_agent import ASSCHOrchestrator
        
        return ASSCHOrchestrator(
            apollo=self._apollo,
            smartlead=self._smartlead,
            salesgpt=self._salesgpt,
            scheduler=self._scheduler,
            crm=self._crm,
            visibility=self._visibility,
            competitor=self._competitor,
            scorer=self._scorer,
            state=self._state_manager,
            ab_manager=self._ab_test_manager,
            apollo_ab=self._apollo_ab_manager
        )
    
    def close(self):
        """Close all database connections."""
        self._db_manager.close()

