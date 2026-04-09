"""
Centralized configuration management using Pydantic Settings.

All environment variables and configuration are managed here.
"""
from typing import Optional
from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized configuration for SalesGPT.
    
    All configuration is loaded from environment variables or .env file.
    """
    
    # Database Configuration
    # NOTE: We prefer SALESGPT_DATABASE_URL for this app's internal state DB so
    # DATABASE_URL can be used by other systems (e.g., Supabase pooler).
    database_url: str = Field(
        default="sqlite:///./salesgpt.db",
        validation_alias=AliasChoices("SALESGPT_DATABASE_URL", "DATABASE_URL"),
    )
    
    # External data sources (optional)
    # Supabase Postgres (pooler) for signup detection (auth.users)
    supabase_database_url: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("SUPABASE_DATABASE_URL", "DATABASE_URL"),
    )
    
    # API Keys - Required
    openai_api_key: str = ""
    apollo_api_key: str = ""
    smartlead_api_key: str = ""
    hubspot_access_token: str = Field(
        default="",
        validation_alias=AliasChoices("HUBSPOT_ACCESS_TOKEN", "HUBSPOT_API_KEY", "HUBSPOT_PAT"),
    )  # Private App access token
    
    # API Keys - Optional
    cal_api_key: Optional[str] = None
    cal_booking_link: Optional[str] = None
    gemflush_api_key: Optional[str] = None
    gemflush_api_url: Optional[str] = None
    
    # Stripe (optional, used for paid conversion tracking)
    stripe_api_key: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("STRIPE_API_KEY", "STRIPE_SECRET_KEY"),
    )
    stripe_webhook_secret: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("STRIPE_WEBHOOK_SECRET", "STRIPE_WEBHOOK_SECRET_LIVE"),
    )
    stripe_pro_price_id_live: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("STRIPE_PRO_PRICE_ID_LIVE",),
    )
    
    # HubSpot OAuth (optional, alternative to access_token)
    hubspot_client_id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("HUBSPOT_CLIENT_ID", "HS_CLIENT_ID"),
    )
    hubspot_client_secret: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("HUBSPOT_CLIENT_SECRET", "HS_CLIENT_SECRET"),
    )
    hubspot_refresh_token: Optional[str] = None
    
    # Outbound email identity (used by Zoho Mail compat and, if enabled, Smartlead)
    smartlead_from_email: str = Field(
        default="",
        validation_alias=AliasChoices(
            "SMARTLEAD_FROM_EMAIL",
            "OUTBOUND_FROM_EMAIL",
            "ZOHO_MAIL_FROM",
        ),
    )
    smartlead_from_name: str = Field(
        default="ASSCH Team",
        validation_alias=AliasChoices(
            "SMARTLEAD_FROM_NAME",
            "OUTBOUND_FROM_NAME",
            "ZOHO_MAIL_FROM_NAME",
        ),
    )
    smartlead_reply_to: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "SMARTLEAD_REPLY_TO",
            "OUTBOUND_REPLY_TO",
            "ZOHO_MAIL_REPLY_TO",
        ),
    )
    smartlead_campaign_name: str = Field(
        default="ASSCH Outreach",
        validation_alias=AliasChoices("SMARTLEAD_CAMPAIGN_NAME", "OUTBOUND_CAMPAIGN_NAME"),
    )
    # When set, outbound pipelines reuse this campaign (no create / no new sequences from code)
    smartlead_campaign_id: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("SMARTLEAD_CAMPAIGN_ID"),
    )
    
    # Marketing automation master switch (CLI scripts exit unless True or --force)
    marketing_automation_enabled: bool = False
    
    # Zoho stack (CRM + Mail) — replaces HubSpot + Smartlead in ServiceContainer when true
    use_zoho_stack: bool = False
    zoho_client_id: Optional[str] = None
    zoho_client_secret: Optional[str] = None
    zoho_refresh_token: Optional[str] = None
    zoho_accounts_domain: str = "https://accounts.zoho.com"
    zoho_crm_api_base: str = "https://www.zohoapis.com/crm/v6"
    zoho_mail_api_base: str = "https://mail.zoho.com"
    zoho_mail_account_id: Optional[str] = None
    zoho_mail_send_delay_seconds: float = 0.0
    
    # Webhook Security
    webhook_secret_key: str = ""  # Optional for development
    webhook_port: int = 8001
    
    # LLM Configuration
    gpt_model: str = "gpt-3.5-turbo-0613"
    salesgpt_config_path: str = "examples/example_agent_setup.json"
    salesgpt_verbose: bool = False
    
    # GEMflush Configuration
    gemflush_use_real_api: bool = False
    
    # Default Campaign Settings
    default_geography: str = "New York, NY"
    default_specialty: str = "Dermatology"
    gemflush_campaign_target_users: int = 50
    gemflush_min_geo_score: float = 50.0
    
    # Default Competitor (for GEMflush)
    default_competitor: str = "local competitors"
    
    # Analytics settings (NEW)
    ab_testing_enabled: bool = True
    min_sample_size_for_recommendations: int = 10
    ucb_exploration_parameter: float = 2.0
    default_batch_size: int = 50
    queue_refill_threshold: int = 20
    
    # SFA Configuration
    sfa_min_adopter_score: float = 50.0
    sfa_min_tier: str = "medium"
    sfa_batch_size: int = 100
    sfa_default_industry: str = "medical"  # legal, real_estate, medical
    sfa_default_location: Optional[str] = None
    
    # Mock API Configuration
    use_mock_apis: bool = False
    mock_api_url: str = "http://localhost:8001"
    apollo_api_url: Optional[str] = None  # Override Apollo base URL
    smartlead_api_url: Optional[str] = None  # Override Smartlead base URL
    hubspot_api_url: Optional[str] = None  # Override HubSpot base URL
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Ignore extra env vars not in model
    )
    
    def __init__(self, **kwargs):
        """Initialize settings with defaults and validation."""
        super().__init__(**kwargs)
        
        # Set default reply_to if not provided
        if not self.smartlead_reply_to:
            self.smartlead_reply_to = self.smartlead_from_email


# Global settings instance (lazy-loaded)
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Factory function for settings with singleton pattern.
    
    Returns:
        Settings instance (cached after first call)
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

