"""
Pytest fixtures for database testing.

Provides in-memory SQLite database for testing.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from salesgpt.models.database import Base
from salesgpt.db.connection import DatabaseManager


@pytest.fixture
def test_db_engine():
    """Create in-memory SQLite engine for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def test_db_session(test_db_engine):
    """Create database session for testing."""
    Session = sessionmaker(bind=test_db_engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def test_db_manager():
    """Create database manager with in-memory database."""
    db_manager = DatabaseManager("sqlite:///:memory:")
    db_manager.create_tables()
    yield db_manager
    db_manager.close()


@pytest.fixture
def test_state_manager(test_db_manager):
    """Create state manager with test database."""
    from state.state_manager import StateManager
    return StateManager(test_db_manager)

