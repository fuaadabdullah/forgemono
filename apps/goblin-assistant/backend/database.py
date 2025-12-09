from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Generator
import os
from dotenv import load_dotenv

# Import Vault client for database credentials
try:
    from .vault_client import get_vault_manager

    VAULT_AVAILABLE = True
except ImportError:
    VAULT_AVAILABLE = False

load_dotenv()


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


# Get database URL
db_config = get_database_config()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./goblin_assistant.db")

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
    pool_config = {
        "poolclass": QueuePool,  # Use QueuePool for better connection management
        "pool_size": int(os.getenv("DB_POOL_SIZE", "20")),  # Base pool size
        "max_overflow": int(
            os.getenv("DB_MAX_OVERFLOW", "10")
        ),  # Max connections beyond pool_size
        "pool_timeout": int(
            os.getenv("DB_POOL_TIMEOUT", "30")
        ),  # Timeout for getting connection
        "pool_recycle": int(
            os.getenv("DB_POOL_RECYCLE", "3600")
        ),  # Recycle connections after 1 hour
        "pool_pre_ping": True,  # Test connections before use to catch stale connections
        "echo": False,  # Disable SQL logging in production
    }

    # PostgreSQL-specific connect args
    connect_args = {
        "connect_timeout": 10,  # Connection timeout in seconds
        "options": "-c statement_timeout=30000",  # 30s query timeout
    }

    # Add SSL certificate if using Supabase
    ssl_cert_path = os.getenv("DB_SSL_CERT_PATH")
    if ssl_cert_path and os.path.exists(ssl_cert_path):
        connect_args["sslmode"] = "verify-ca"
        connect_args["sslrootcert"] = ssl_cert_path
else:
    # SQLite-specific connect args
    connect_args = {"check_same_thread": False}

# Create engine with production-ready configuration
engine = create_engine(DATABASE_URL, connect_args=connect_args, **pool_config)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """Drop all tables"""
    Base.metadata.drop_all(bind=engine)
