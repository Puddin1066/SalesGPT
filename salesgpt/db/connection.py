"""
Database connection manager for SalesGPT.

Handles SQLAlchemy session management and database initialization.
"""
from typing import Generator, Optional
from contextlib import contextmanager
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.pool import StaticPool
from sqlalchemy.engine import Engine

from salesgpt.models.database import Base


class DatabaseManager:
    """
    Database connection manager with session handling.
    
    Supports SQLite with connection pooling and proper session management.
    """
    
    def __init__(self, database_url: str):
        """
        Initialize database manager.
        
        Args:
            database_url: Database connection URL (e.g., "sqlite:///./salesgpt.db")
        """
        self.database_url = database_url
        self._engine = None
        self._session_factory = None
        self._scoped_session = None
        
        self._initialize_engine()
        self._initialize_session()
    
    def _initialize_engine(self):
        """Initialize SQLAlchemy engine with appropriate configuration."""
        # For SQLite, use StaticPool to handle connection pooling properly
        connect_args = {}
        poolclass = None
        
        if self.database_url.startswith("sqlite"):
            # SQLite-specific configuration
            connect_args = {"check_same_thread": False}
            poolclass = StaticPool
        
        self._engine = create_engine(
            self.database_url,
            connect_args=connect_args,
            poolclass=poolclass,
            echo=False  # Set to True for SQL query logging
        )
        
        # Enable foreign key constraints for SQLite
        if self.database_url.startswith("sqlite"):
            @event.listens_for(Engine, "connect")
            def set_sqlite_pragma(dbapi_conn, connection_record):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
    
    def _initialize_session(self):
        """Initialize session factory."""
        self._session_factory = sessionmaker(
            bind=self._engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False
        )
        self._scoped_session = scoped_session(self._session_factory)
    
    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """
        Context manager for database sessions.
        
        Usage:
            with db_manager.session() as session:
                # Use session here
                session.commit()
        
        Yields:
            SQLAlchemy Session object
        """
        session = self._scoped_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_session(self) -> Session:
        """
        Get a new database session.
        
        Note: You must manually close the session when done.
        For automatic management, use the context manager instead.
        
        Returns:
            SQLAlchemy Session object
        """
        return self._scoped_session()
    
    def create_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(bind=self._engine)
    
    def drop_tables(self):
        """Drop all database tables (use with caution!)."""
        Base.metadata.drop_all(bind=self._engine)
    
    def close(self):
        """Close all database connections."""
        if self._scoped_session:
            self._scoped_session.remove()
        if self._engine:
            self._engine.dispose()


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_db_session(database_url: str) -> Generator[Session, None, None]:
    """
    Get a database session using global database manager.
    
    Args:
        database_url: Database connection URL
        
    Yields:
        SQLAlchemy Session object
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(database_url)
    
    with _db_manager.session() as session:
        yield session

