"""
Database module for SalesGPT.

Provides database connection management and session handling.
"""
from salesgpt.db.connection import DatabaseManager, get_db_session

__all__ = ["DatabaseManager", "get_db_session"]



