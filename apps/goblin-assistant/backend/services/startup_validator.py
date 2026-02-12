"""
StartupValidator Service for validating application startup requirements.

This service handles all startup validation and configuration checks,
separating it from the main application logic for better organization.
"""

import logging
import os
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class StartupValidator:
    """Service for validating startup configuration and dependencies."""

    def __init__(self):
        """Initialize the StartupValidator."""
        self.validation_issues: List[str] = []

    async def validate_startup(self) -> bool:
        """Validate all startup requirements and dependencies."""
        logger.info("🔍 Validating startup configuration...")

        # Check configuration
        self._validate_configuration()

        # Check critical dependencies
        self._validate_dependencies()

        # Report validation results
        return self._report_validation_results()

    def _validate_configuration(self) -> None:
        """Validate configuration settings."""
        try:
            from config import settings

            logger.info(
                f"✅ Configuration loaded: environment={settings.environment}, instances={settings.instance_count}"
            )

            # Validate production requirements
            if settings.is_production and not settings.database_url:
                self.validation_issues.append("DATABASE_URL required in production environment")

            if (
                settings.is_production
                and settings.allow_memory_fallback
                and settings.is_multi_instance
            ):
                self.validation_issues.append("Memory fallback not allowed in multi-instance production")

            if settings.is_production and not os.getenv("ROUTING_ENCRYPTION_KEY"):
                self.validation_issues.append(
                    "ROUTING_ENCRYPTION_KEY required in production for chat routing"
                )

        except ImportError:
            self.validation_issues.append("Configuration system not available")
        except Exception as e:
            self.validation_issues.append(f"Configuration validation failed: {e}")

    def _validate_dependencies(self) -> None:
        """Validate critical dependencies."""
        try:
            from .scripts.check_dependencies import check_pydantic_email, check_redis

            if not check_pydantic_email():
                self.validation_issues.append("Email validation dependencies not properly configured")
            
            redis_available = check_redis()
            if (
                not redis_available
                and settings.is_production
                and settings.is_multi_instance
            ):
                self.validation_issues.append(
                    "Redis required but not available in multi-instance production"
                )

        except ImportError:
            logger.warning("⚠️  Dependency checker not available - skipping automated checks")
        except Exception as e:
            self.validation_issues.append(f"Dependency validation failed: {e}")

    def _report_validation_results(self) -> bool:
        """Report validation results and return success status."""
        if self.validation_issues:
            logger.error("❌ Startup validation failed:")
            for issue in self.validation_issues:
                logger.error(f"  - {issue}")
            
            logger.error(
                "\n🚨 Critical configuration issues detected. Server may not function properly."
            )
            logger.error("   Check the issues above and fix before proceeding to production.")
            
            # Don't exit - allow server to start with warnings for development
            if settings.is_production:
                logger.error(
                    "   In production environment, these issues should be resolved immediately."
                )
            
            return False
        else:
            logger.info("✅ Startup validation passed - all systems ready")
            return True

    def get_validation_issues(self) -> List[str]:
        """Get list of validation issues."""
        return self.validation_issues.copy()

    def add_custom_validation(self, validation_func: callable, description: str) -> None:
        """Add a custom validation function."""
        try:
            result = validation_func()
            if not result:
                self.validation_issues.append(f"Custom validation failed: {description}")
        except Exception as e:
            self.validation_issues.append(f"Custom validation error ({description}): {e}")

    def cleanup(self) -> None:
        """Clean up validation resources."""
        self.validation_issues.clear()
        logger.info("Startup validation resources cleaned up")
