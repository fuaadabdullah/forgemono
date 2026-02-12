"""
MiddlewareConfigurator Service for managing FastAPI middleware setup.

This service handles all middleware configuration and setup,
separating it from the main application logic for better organization.
"""

import logging
import os
from typing import List
from fastapi import FastAPI

from .middleware.rate_limiter import RateLimitMiddleware, limiter
from .middleware.logging_middleware import StructuredLoggingMiddleware, setup_logging
from .middleware.request_id_middleware import RequestIDMiddleware
from .middleware.security_headers import SecurityHeadersMiddleware

logger = logging.getLogger(__name__)


class MiddlewareConfigurator:
    """Service for configuring and setting up middleware."""

    def __init__(self):
        """Initialize the MiddlewareConfigurator."""
        self.middleware_added = []

    def configure_all_middleware(self, app: FastAPI) -> None:
        """Configure all middleware for the FastAPI application."""
        logger.info("🔧 Configuring middleware...")

        # Configure logging first
        self._configure_logging()

        # Add middleware in the correct order
        self._add_request_id_middleware(app)
        self._add_logging_middleware(app)
        self._add_security_headers_middleware(app)
        self._add_rate_limiting_middleware(app)
        self._add_cors_middleware(app)

        logger.info(f"✅ Configured {len(self.middleware_added)} middleware components")

    def _configure_logging(self) -> None:
        """Configure structured logging."""
        log_level = os.getenv("LOG_LEVEL", "INFO")
        setup_logging(log_level)
        logger.info(f"✅ Logging configured with level: {log_level}")

    def _add_request_id_middleware(self, app: FastAPI) -> None:
        """Add request ID middleware."""
        app.add_middleware(RequestIDMiddleware)
        self.middleware_added.append("RequestIDMiddleware")
        logger.info("✅ Added RequestIDMiddleware")

    def _add_logging_middleware(self, app: FastAPI) -> None:
        """Add structured logging middleware."""
        app.add_middleware(StructuredLoggingMiddleware)
        self.middleware_added.append("StructuredLoggingMiddleware")
        logger.info("✅ Added StructuredLoggingMiddleware")

    def _add_security_headers_middleware(self, app: FastAPI) -> None:
        """Add security headers middleware."""
        app.add_middleware(SecurityHeadersMiddleware)
        self.middleware_added.append("SecurityHeadersMiddleware")
        logger.info("✅ Added SecurityHeadersMiddleware")

    def _add_rate_limiting_middleware(self, app: FastAPI) -> None:
        """Add rate limiting middleware."""
        app.add_middleware(RateLimitMiddleware)
        self.middleware_added.append("RateLimitMiddleware")
        logger.info("✅ Added RateLimitMiddleware")

    def _add_cors_middleware(self, app: FastAPI) -> None:
        """Add CORS middleware."""
        from fastapi.middleware.cors import CORSMiddleware

        # Configure CORS origins
        cors_origins_str = os.getenv(
            "CORS_ORIGINS", "http://localhost:3000,http://localhost:5173"
        )
        cors_origins = [
            origin.strip() for origin in cors_origins_str.split(",") if origin.strip()
        ]

        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,  # Configure via CORS_ORIGINS env var
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self.middleware_added.append("CORSMiddleware")
        logger.info(f"✅ Added CORSMiddleware with origins: {cors_origins}")

    def get_middleware_list(self) -> List[str]:
        """Get list of configured middleware."""
        return self.middleware_added.copy()

    def cleanup(self) -> None:
        """Clean up middleware resources."""
        # Clean up rate limiter resources if needed
        try:
            limiter.cleanup_old_entries()
            logger.info("✅ Rate limiter cleanup completed")
        except Exception as e:
            logger.warning(f"⚠️  Rate limiter cleanup failed: {e}")