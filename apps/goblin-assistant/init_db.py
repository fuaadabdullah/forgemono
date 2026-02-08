#!/usr/bin/env python3
"""
Database initialization script for goblin-assistant.
Creates all database tables defined in models.py.
"""

import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from database import engine, Base

# Import all models so they are registered with Base metadata
from models_base import (
    User,
    Task,
    Stream,
    StreamChunk,
    SearchCollection,
    SearchDocument,
)


def init_database():
    """Create all database tables."""
    try:
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        sys.exit(1)


if __name__ == "__main__":
    init_database()
