"""
Configuration module for SalesGPT.

Provides centralized configuration management using Pydantic Settings.
"""
from salesgpt.config.settings import Settings, get_settings

__all__ = ["Settings", "get_settings"]



