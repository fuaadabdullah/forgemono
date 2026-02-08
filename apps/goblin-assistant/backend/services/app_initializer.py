"""
AppInitializer Service for managing FastAPI application initialization.

This service handles all application startup and shutdown logic,
separating it from the main module for better organization and testability.
"""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional
from fastapi import FastAPI
from sqlalchemy.orm import Session

from .monitoring import init_sentry
from .opentelemetry_config import init_opentelemetry, instrument_fastapi_app
from .middleware.rate_limiter import RateLimitMiddleware, limiter
from .middleware.logging_middleware import StructuredLoggingMiddleware, setup_logging
from .middleware.request_id_middleware import RequestIDMiddleware
from .middleware.security_headers import SecurityHeadersMiddleware
from .database import create_tables, SessionLocal
from .seed import seed_database
from .scheduler import start_scheduler, stop_scheduler
from .autoscaling_service import AutoscalingService

logger = logging.getLogger(__name__)


class AppInitializer:
    """Service for initializing and configuring the FastAPI application."""

    def __init__(self):
        """Initialize the AppInitializer."""
        self.app = None
        self.db = None
        self.autoscaling_service = None
        self.challenge_cleanup_task = None
        self.rate_limiter_cleanup_task = None

    def create_app(self) -> FastAPI:
        """Create and configure the FastAPI application."""
        # Initialize monitoring first (before other imports)
        init_sentry()
        init_opentelemetry()

        # Create FastAPI app
        self.app = FastAPI(
            title="GoblinOS Assistant Backend",
            description="Backend API for GoblinOS Assistant with debug capabilities",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc",
            openapi_url="/openapi.json",
        )

        # Instrument FastAPI app with OpenTelemetry
        instrument_fastapi_app(self.app)

        # Configure structured logging
        log_level = os.getenv("LOG_LEVEL", "INFO")
        setup_logging(log_level)

        # Add middleware
        self._add_middleware()

        # Add routers
        self._add_routers()

        # Set up event handlers
        self._setup_event_handlers()

        return self.app

    def _add_middleware(self) -> None:
        """Add middleware to the FastAPI application."""
        # Add request ID middleware (must be before logging middleware)
        self.app.add_middleware(RequestIDMiddleware)

        # Add structured logging middleware
        self.app.add_middleware(StructuredLoggingMiddleware)

        # Add security headers middleware
        self.app.add_middleware(SecurityHeadersMiddleware)

        # Add rate limiting middleware
        self.app.add_middleware(RateLimitMiddleware)

        # CORS middleware for frontend integration
        cors_origins_str = os.getenv(
            "CORS_ORIGINS", "http://localhost:3000,http://localhost:5173"
        )
        cors_origins = [
            origin.strip() for origin in cors_origins_str.split(",") if origin.strip()
        ]
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,  # Configure via CORS_ORIGINS env var
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _add_routers(self) -> None:
        """Add routers to the FastAPI application."""
        # Import routers
        from .debugger.router import router as debugger_router
        from .search_router import router as search_router
        from .settings_router import router as settings_router
        from .execute_router import router as execute_router
        from .auth.api_keys_router import router as api_keys_router
        from .auth.auth_router import router as jwt_auth_router
        from .parse_router import router as parse_router
        from .routing_router import router as routing_router
        from .chat_router import router as chat_router
        from .api_router import router as api_router
        from .stream_router import router as stream_router
        from .health_router import router as health_router
        from .health.llm_health import router as llm_health_router
        from .dashboard_router import router as dashboard_router
        from .routers.goblins_router import router as goblins_router
        from .routers.cost_router import router as cost_router
        from .routers.user_auth_router import router as user_auth_router

        try:
            from .raptor_router import router as raptor_router
        except ImportError:
            # Create a stub router if raptor_mini is not available
            from fastapi import APIRouter

            raptor_router = APIRouter()

        # Create versioned API router
        v1_router = APIRouter(prefix="/v1")

        # Include all routers under v1
        v1_router.include_router(debugger_router)
        v1_router.include_router(search_router, tags=["search"])
        v1_router.include_router(settings_router, tags=["settings"])
        v1_router.include_router(execute_router, tags=["execute"])
        v1_router.include_router(api_keys_router, tags=["api-keys"])
        v1_router.include_router(jwt_auth_router, tags=["auth"])
        v1_router.include_router(parse_router, tags=["parse"])
        v1_router.include_router(routing_router, tags=["routing"])
        v1_router.include_router(chat_router, tags=["chat"])
        v1_router.include_router(api_router, tags=["api"])
        v1_router.include_router(stream_router, tags=["stream"])
        v1_router.include_router(raptor_router, tags=["raptor"])
        v1_router.include_router(health_router, tags=["health"])
        v1_router.include_router(llm_health_router, tags=["health"])
        v1_router.include_router(dashboard_router, tags=["dashboard"])
        v1_router.include_router(goblins_router, tags=["goblins"])
        v1_router.include_router(cost_router, tags=["cost"])
        v1_router.include_router(user_auth_router, tags=["auth"])

        # Include routers (keeping legacy routes for backward compatibility)
        self.app.include_router(debugger_router)
        self.app.include_router(v1_router)  # Versioned API routes
        self.app.include_router(search_router)
        self.app.include_router(settings_router)
        self.app.include_router(execute_router)
        self.app.include_router(api_keys_router)
        self.app.include_router(jwt_auth_router)
        self.app.include_router(parse_router)
        self.app.include_router(routing_router)
        self.app.include_router(chat_router)
        self.app.include_router(api_router)
        self.app.include_router(stream_router)
        self.app.include_router(raptor_router)
        self.app.include_router(health_router)
        self.app.include_router(llm_health_router)
        self.app.include_router(dashboard_router)

    def _setup_event_handlers(self) -> None:
        """Set up application event handlers."""
        self.app.on_event("startup")(self._startup_event)
        self.app.on_event("shutdown")(self._shutdown_event)

    async def _startup_event(self) -> None:
        """Handle application startup."""
        # Validate configuration first
        await self._validate_startup_configuration()

        # Initialize database
        self._initialize_database()

        # Start background tasks
        self._start_background_tasks()

        # Start deferred initialization
        asyncio.create_task(self._deferred_initialization())

    async def _shutdown_event(self) -> None:
        """Handle application shutdown."""
        # Stop background tasks
        self._stop_background_tasks()

        # Stop scheduler
        self._stop_scheduler()

        # Stop autoscaling service
        if self.autoscaling_service:
            await self.autoscaling_service.close()

    def _initialize_database(self) -> None:
        """Initialize the database."""
        create_tables()

        # Seed the database
        self.db = SessionLocal()
        try:
            seed_database(self.db)
        finally:
            self.db.close()

    def _start_background_tasks(self) -> None:
        """Start background tasks."""
        # Start challenge cleanup task
        self.challenge_cleanup_task = asyncio.create_task(
            self._challenge_cleanup_worker()
        )
        logger.info("Started challenge cleanup background task")

        # Start rate limiter cleanup task
        self.rate_limiter_cleanup_task = asyncio.create_task(
            self._rate_limiter_cleanup_worker()
        )
        logger.info("Started rate limiter cleanup background task")

    def _stop_background_tasks(self) -> None:
        """Stop background tasks."""
        # Stop challenge cleanup task
        if self.challenge_cleanup_task:
            self.challenge_cleanup_task.cancel()
            try:
                asyncio.run(self.challenge_cleanup_task)
            except asyncio.CancelledError:
                pass
            logger.info("Stopped challenge cleanup background task")

        # Stop rate limiter cleanup task
        if self.rate_limiter_cleanup_task:
            self.rate_limiter_cleanup_task.cancel()
            try:
                asyncio.run(self.rate_limiter_cleanup_task)
            except asyncio.CancelledError:
                pass
            logger.info("Stopped rate limiter cleanup background task")

    def _stop_scheduler(self) -> None:
        """Stop the scheduler."""
        try:
            stop_scheduler()
            logger.info("Stopped APScheduler")
        except Exception as e:
            logger.warning(f"Warning: Failed to stop APScheduler: {e}")

    async def _validate_startup_configuration(self) -> None:
        """Validate critical configuration and dependencies before server starts."""
        logger.info("🔍 Validating startup configuration...")

        issues = []

        # Check configuration
        try:
            from config import settings

            logger.info(
                f"✅ Configuration loaded: environment={settings.environment}, instances={settings.instance_count}"
            )

            # Validate production requirements
            if settings.is_production and not settings.database_url:
                issues.append("DATABASE_URL required in production environment")

            if (
                settings.is_production
                and settings.allow_memory_fallback
                and settings.is_multi_instance
            ):
                issues.append("Memory fallback not allowed in multi-instance production")

            if settings.is_production and not os.getenv("ROUTING_ENCRYPTION_KEY"):
                issues.append(
                    "ROUTING_ENCRYPTION_KEY required in production for chat routing"
                )

        except ImportError:
            issues.append("Configuration system not available")
        except Exception as e:
            issues.append(f"Configuration validation failed: {e}")

        # Check critical dependencies
        try:
            from .scripts.check_dependencies import check_pydantic_email, check_redis

            if not check_pydantic_email():
                issues.append("Email validation dependencies not properly configured")
            redis_available = check_redis()
            if (
                not redis_available
                and settings.is_production
                and settings.is_multi_instance
            ):
                issues.append(
                    "Redis required but not available in multi-instance production"
                )
        except ImportError:
            logger.warning("⚠️  Dependency checker not available - skipping automated checks")
        except Exception as e:
            issues.append(f"Dependency validation failed: {e}")

        # Report issues
        if issues:
            logger.error("❌ Startup validation failed:")
            for issue in issues:
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
        else:
            logger.info("✅ Startup validation passed - all systems ready")

    async def _deferred_initialization(self) -> None:
        """Run heavier, optional startup tasks without blocking server accept loop."""
        await asyncio.sleep(0)  # yield control

        # Initialize autoscaling service
        try:
            self.autoscaling_service = AutoscalingService()
            await self.autoscaling_service.initialize()
            logger.info("Started autoscaling service (deferred)")
        except Exception as e:
            logger.warning(f"Warning: Deferred autoscaling service start failed: {e}")

        # Initialize scheduler
        try:
            start_scheduler()
            logger.info("Started APScheduler for lightweight periodic tasks (deferred)")
        except Exception as e:
            logger.warning(f"Warning: Deferred APScheduler start failed: {e}")

    async def _challenge_cleanup_worker(self) -> None:
        """Background worker to clean up expired challenges every 10 minutes."""
        while True:
            try:
                await asyncio.sleep(600)  # Run every 10 minutes
                # Note: This would need to be implemented based on the actual challenge system
                logger.debug("Challenge cleanup worker running")
            except asyncio.CancelledError:
                logger.info("Challenge cleanup worker cancelled")
                break
            except Exception as e:
                logger.error(f"Error in challenge cleanup worker: {e}")

    async def _rate_limiter_cleanup_worker(self) -> None:
        """Background worker to clean up old rate limiter entries every 5 minutes."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                limiter.cleanup_old_entries()
                logger.info("Rate limiter cleanup completed")
            except asyncio.CancelledError:
                logger.info("Rate limiter cleanup worker cancelled")
                break
            except Exception as e:
                logger.error(f"Error in rate limiter cleanup worker: {e}")

    def get_app(self) -> FastAPI:
        """Get the configured FastAPI application."""
        if not self.app:
            self.create_app()
        return self.app
