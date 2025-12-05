"""
Environment-Aware Configuration System

Provides centralized configuration management with environment-specific settings,
validation, and computed properties for the Goblin Assistant backend.
"""

from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    """Application settings with environment-aware defaults"""

    # Environment
    environment: Literal["development", "staging", "production"] = "development"
    instance_count: int = 1

    # Redis Configuration
    redis_url: str = "redis://localhost:6379"
    redis_timeout: int = 5
    allow_memory_fallback: bool = False

    # Authentication
    challenge_ttl: int = 300  # 5 minutes
    debug_auth: bool = False
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    # Email Validation
    require_email_validation: bool = True
    allow_disposable_emails: bool = False

    # Database
    database_url: str = ""

    # Logging
    log_level: str = "INFO"

    @property
    def is_multi_instance(self) -> bool:
        """Check if running in multi-instance mode"""
        return self.instance_count > 1

    @property
    def should_alert_on_fallback(self) -> bool:
        """Determine if fallback mode should trigger alerts"""
        return self.environment == "production" and self.is_multi_instance

    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment == "development"

    class Config:
        """Pydantic configuration"""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Allow extra fields from .env file

        @classmethod
        def customise_sources(cls, init_settings, env_settings, file_secret_settings):
            """Customize settings sources with environment variable precedence"""
            return (
                init_settings,
                env_settings,  # Environment variables
                file_secret_settings,  # .env file
            )


# Global settings instance
settings = Settings()


# Environment-specific validation
def validate_environment_config():
    """Validate configuration based on environment"""
    if settings.is_production and not settings.database_url:
        raise ValueError("DATABASE_URL is required in production")

    if (
        settings.is_production
        and settings.allow_memory_fallback
        and settings.is_multi_instance
    ):
        raise ValueError(
            "Memory fallback not allowed in multi-instance production. "
            "Redis is required for distributed challenge storage."
        )

    if settings.environment not in ["development", "staging", "production"]:
        raise ValueError(f"Invalid environment: {settings.environment}")


# Run validation on import
validate_environment_config()
