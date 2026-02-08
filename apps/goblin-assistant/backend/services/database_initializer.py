"""
DatabaseInitializer Service for managing database setup and configuration.

This service handles all database-related initialization tasks,
separating them from the main application logic for better organization.
"""

import logging
from typing import Optional
from sqlalchemy.orm import Session

from .database import create_tables, SessionLocal
from .seed import seed_database

logger = logging.getLogger(__name__)


class DatabaseInitializer:
    """Service for initializing and managing database operations."""

    def __init__(self):
        """Initialize the DatabaseInitializer."""
        self.db: Optional[Session] = None

    def initialize_database(self) -> None:
        """Initialize the database schema and seed data."""
        logger.info("🔧 Initializing database...")

        try:
            # Create database tables
            self._create_tables()

            # Seed initial data
            self._seed_database()

            logger.info("✅ Database initialization completed successfully")

        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise

    def _create_tables(self) -> None:
        """Create database tables."""
        logger.info("Creating database tables...")
        create_tables()
        logger.info("✅ Database tables created successfully")

    def _seed_database(self) -> None:
        """Seed the database with initial data."""
        logger.info("Seeding database with initial data...")

        self.db = SessionLocal()
        try:
            seed_database(self.db)
            logger.info("✅ Database seeded successfully")
        except Exception as e:
            logger.error(f"❌ Database seeding failed: {e}")
            raise
        finally:
            self.db.close()
            self.db = None

    def get_database_session(self) -> Session:
        """Get a database session."""
        if not self.db:
            self.db = SessionLocal()
        return self.db

    def close_database_session(self) -> None:
        """Close the database session."""
        if self.db:
            self.db.close()
            self.db = None

    def validate_database_connection(self) -> bool:
        """Validate that the database connection is working."""
        try:
            db = SessionLocal()
            # Try a simple query to test the connection
            db.execute("SELECT 1").scalar()
            db.close()
            logger.info("✅ Database connection validated successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection validation failed: {e}")
            return False

    def cleanup(self) -> None:
        """Clean up database resources."""
        self.close_database_session()
        logger.info("Database resources cleaned up")