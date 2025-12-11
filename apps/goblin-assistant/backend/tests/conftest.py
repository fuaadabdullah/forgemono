"""
Shared test fixtures and configuration for Goblin Assistant backend tests.
"""

print("conftest.py loaded")

import asyncio
import os
import sys
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from pathlib import Path
from faker import Faker

# Add the backend directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import Base, get_db

# Import all models to ensure they are registered with SQLAlchemy
from models_base import (
    User,
    UserSession,
    AuditLog,
    UserRole,
    UserRoleAssignment,
    Task,
    Stream,
    StreamChunk,
    SearchCollection,
    SearchDocument,
)


# Test database setup
TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def test_db():
    """Create test database and tables."""
    # Force import of all models to ensure they are registered
    import models_base

    print("Creating tables...")
    print(f"Base metadata tables: {list(Base.metadata.tables.keys())}")
    Base.metadata.create_all(bind=engine)
    print("Tables created")
    # Verify tables exist
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table';")
        )
        tables = [row[0] for row in result]
        print(f"Actual tables in DB: {tables}")
    yield
    print("Dropping tables...")
    Base.metadata.drop_all(bind=engine)
    print("Tables dropped")


@pytest.fixture
def db_session(test_db) -> Generator[Session, None, None]:
    """Provide a database session for tests."""
    # Create session directly with the engine
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        # Ensure tables exist in this session
        Base.metadata.create_all(bind=engine)
        # Debug: Check what database this session is using
        result = session.execute(
            text("SELECT file FROM pragma_database_list WHERE name='main';")
        )
        db_file = result.scalar()
        print(f"Session is using database file: {db_file}")
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session) -> Generator[TestClient, None, None]:
    """Provide a test client with database session override."""
    # Temporarily disabled due to import issues
    # def override_get_db():
    #     yield db_session

    # app.dependency_overrides[get_db] = override_get_db

    # with TestClient(app) as test_client:
    #     yield test_client

    # app.dependency_overrides.clear()
    pass  # Skip for now


@pytest.fixture
def faker():
    """Provide a Faker instance for generating test data."""
    return Faker()


@pytest.fixture
def mock_redis():
    """Mock Redis client for tests."""

    class MockRedis:
        def __init__(self):
            self.data = {}

        def get(self, key):
            return self.data.get(key)

        def set(self, key, value, ex=None):
            self.data[key] = value
            return True

        def delete(self, key):
            return self.data.pop(key, None) is not None

        def exists(self, key):
            return key in self.data

        def ping(self):
            return True

    return MockRedis()


# Test markers for pytest
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests (fast, no external dependencies)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (database, Redis, external APIs)"
    )
    config.addinivalue_line("markers", "e2e: End-to-end tests (full user flows)")
    config.addinivalue_line("markers", "slow: Slow running tests")
