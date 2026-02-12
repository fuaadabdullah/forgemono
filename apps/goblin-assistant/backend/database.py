from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Generator
import os
import sys
from dotenv import load_dotenv

# Import Vault client for database credentials
try:
    from .vault_client import get_vault_manager

    VAULT_AVAILABLE = True
except ImportError:
    VAULT_AVAILABLE = False

load_dotenv()

# Ensure a single module instance across import paths.
if __name__ == "database":
    sys.modules.setdefault("backend.database", sys.modules[__name__])
elif __name__ == "backend.database":
    sys.modules.setdefault("database", sys.modules[__name__])


# Database configuration - try Vault first, fallback to environment variables
def get_database_config():
    """Get database configuration from Vault or environment variables"""
    if VAULT_AVAILABLE and os.getenv("USE_VAULT", "").lower() in ("true", "1", "yes"):
        try:
            vault_manager = get_vault_manager()
            vault_config = vault_manager.get_database_config()
            if (
                vault_config
                and vault_config.get("username")
                and vault_config.get("password")
            ):
                return vault_config
        except Exception:
            pass  # Fall back to environment variables

    # Fallback to environment variables
    return {
        "username": os.getenv("DB_USERNAME", ""),
        "password": os.getenv("DB_PASSWORD", ""),
        "host": os.getenv("DB_HOST", ""),
        "database": os.getenv("DB_NAME", ""),
    }


# Get database URL - prioritize environment variable for production
db_config = get_database_config()
_raw_db_url = os.getenv("DATABASE_URL", "")

# For production (Fly.io), DATABASE_URL should be set to Supabase PostgreSQL
# For local dev, fallback to SQLite with mounted volume support
if _raw_db_url and (
    _raw_db_url.startswith("postgres") or _raw_db_url.startswith("postgresql")
):
    DATABASE_URL = _raw_db_url
    print(f"[DB] Using PostgreSQL database")
else:
    # SQLite fallback for local development only
    _sqlite_fallback = (
        "/app/data/goblin_assistant.db"
        if os.path.isdir("/app/data")
        else "./goblin_assistant.db"
    )
    DATABASE_URL = f"sqlite:///{_sqlite_fallback}"
    print(
        f"[DB WARNING] DATABASE_URL not set or not PostgreSQL - using SQLite fallback: {_sqlite_fallback}"
    )
    print(
        f"[DB WARNING] For production, set DATABASE_URL to your Supabase PostgreSQL connection string"
    )

# Override with Vault credentials if available
if db_config["username"] and db_config["password"] and db_config["host"]:
    DATABASE_URL = f"postgresql://{db_config['username']}:{db_config['password']}@{db_config['host']}:5432/{db_config['database']}"

# Production PostgreSQL configuration
is_postgres = DATABASE_URL.startswith("postgresql") or DATABASE_URL.startswith(
    "postgres"
)

# Connection pool settings (only for PostgreSQL)
pool_config = {}
if is_postgres:
    # When using Supabase connection pooler (Supavisor), use smaller pool size
    # since the pooler handles connection management
    is_supabase = "supabase" in DATABASE_URL or "pooler.supabase" in DATABASE_URL

    pool_config = {
        "poolclass": QueuePool,
        # Smaller pool when using external pooler (Supabase Supavisor)
        "pool_size": int(os.getenv("DB_POOL_SIZE", "5" if is_supabase else "20")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "5" if is_supabase else "10")),
        "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
        "pool_recycle": int(
            os.getenv("DB_POOL_RECYCLE", "300" if is_supabase else "3600")
        ),
        "pool_pre_ping": True,
        "echo": False,
    }

    # PostgreSQL-specific connect args
    connect_args = {
        "connect_timeout": 10,
        "options": "-c statement_timeout=30000",
    }

    # Supabase requires SSL
    if is_supabase:
        connect_args["sslmode"] = "require"

    # Custom SSL certificate if provided
    ssl_cert_path = os.getenv("DB_SSL_CERT_PATH")
    if ssl_cert_path and os.path.exists(ssl_cert_path):
        connect_args["sslmode"] = "verify-ca"
        connect_args["sslrootcert"] = ssl_cert_path
else:
    # SQLite-specific connect args
    connect_args = {"check_same_thread": False}

# Create engine with production-ready configuration
try:
    engine = create_engine(DATABASE_URL, connect_args=connect_args, **pool_config)
    # Create SessionLocal class
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    _db_initialized = True
except Exception as e:
    print(f"[DB WARNING] Failed to initialize database engine: {e}")
    print(f"[DB WARNING] Database-dependent features will not work")
    engine = None
    SessionLocal = None
    _db_initialized = False

# Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session"""
    if not _db_initialized or SessionLocal is None:
        raise RuntimeError(
            "Database not initialized. Please configure DATABASE_URL with a valid PostgreSQL connection string."
        )
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables - gracefully handles database unavailability"""
    if not _db_initialized or engine is None:
        print("[DB WARNING] Skipping create_tables - database not initialized")
        return
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        # In production with SQLite (misconfigured), log warning but don't crash
        # App features requiring database will fail individually
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Unable to create database tables: {e}")
        logger.warning(
            "Database-dependent features may not work. Please configure DATABASE_URL with a PostgreSQL connection string."
        )
        if not is_postgres:
            print(
                "[DB WARNING] Database initialization failed - SQLite path not writable."
            )
            print(
                "[DB WARNING] Set DATABASE_URL to a PostgreSQL connection string (e.g., from Supabase)"
            )


def drop_tables():
    """Drop all tables"""
    Base.metadata.drop_all(bind=engine)
