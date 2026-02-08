"""
Refactored main module using the new service architecture.

This demonstrates how the main module can be simplified by using
the new service classes for better organization and maintainability.
"""

import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import the new services
from .services.app_initializer import AppInitializer
from .services.database_initializer import DatabaseInitializer
from .services.middleware_configurator import MiddlewareConfigurator
from .services.router_configurator import RouterConfigurator
from .services.background_task_manager import BackgroundTaskManager
from .services.startup_validator import StartupValidator

# Import monitoring and configuration
from .monitoring import init_sentry
from .opentelemetry_config import init_opentelemetry, instrument_fastapi_app

logger = logging.getLogger(__name__)


class Application:
    """Main application class using the new service architecture."""

    def __init__(self):
        """Initialize the application with all services."""
        self.app_initializer = AppInitializer()
        self.database_initializer = DatabaseInitializer()
        self.middleware_configurator = MiddlewareConfigurator()
        self.router_configurator = RouterConfigurator()
        self.background_task_manager = BackgroundTaskManager()
        self.startup_validator = StartupValidator()

        self.app: Optional[FastAPI] = None

    async def initialize(self) -> FastAPI:
        """Initialize the application with all services."""
        logger.info("🚀 Initializing GoblinOS Assistant Backend...")

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

        # Validate startup configuration
        validation_passed = await self.startup_validator.validate_startup()
        if not validation_passed:
            logger.warning("⚠️  Startup validation had issues, but continuing...")

        # Initialize database
        self.database_initializer.initialize_database()

        # Configure middleware
        self.middleware_configurator.configure_all_middleware(self.app)

        # Configure routers
        self.router_configurator.configure_all_routers(self.app)

        # Set up event handlers
        self._setup_event_handlers()

        logger.info("✅ Application initialization completed")
        return self.app

    def _setup_event_handlers(self) -> None:
        """Set up application event handlers."""
        self.app.on_event("startup")(self._startup_event)
        self.app.on_event("shutdown")(self._shutdown_event)

    async def _startup_event(self) -> None:
        """Handle application startup."""
        logger.info("🚀 Application startup event triggered")

        # Start background tasks
        await self.background_task_manager.start_background_tasks()

        # Start deferred initialization
        asyncio.create_task(self._deferred_initialization())

        logger.info("✅ Application startup completed")

    async def _shutdown_event(self) -> None:
        """Handle application shutdown."""
        logger.info("🛑 Application shutdown event triggered")

        # Stop background tasks
        await self.background_task_manager.stop_background_tasks()

        # Clean up services
        self._cleanup_services()

        logger.info("✅ Application shutdown completed")

    async def _deferred_initialization(self) -> None:
        """Run heavier, optional startup tasks without blocking server accept loop."""
        await asyncio.sleep(0)  # yield control

        logger.info("🔧 Running deferred initialization...")

        # Additional initialization tasks can go here
        # These won't block the server from starting

        logger.info("✅ Deferred initialization completed")

    def _cleanup_services(self) -> None:
        """Clean up all services."""
        self.database_initializer.cleanup()
        self.middleware_configurator.cleanup()
        self.router_configurator.cleanup()
        self.background_task_manager.cleanup()
        self.startup_validator.cleanup()
        logger.info("✅ All services cleaned up")

    def get_app(self) -> FastAPI:
        """Get the configured FastAPI application."""
        if not self.app:
            raise RuntimeError("Application not initialized. Call initialize() first.")
        return self.app


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager."""
    # Startup
    application = Application()
    await application.initialize()

    yield

    # Shutdown
    # Cleanup is handled by the application shutdown event


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = Application()
    return application.get_app()


def main():
    """Main entry point for the application."""
    # Configure logging
    log_level = os.getenv("LOG_LEVEL", "INFO")
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create application
    app = create_app()

    # Get configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("RELOAD", "false").lower() == "true"

    logger.info(f"🚀 Starting server on {host}:{port}")
    logger.info(f"🔧 Auto-reload: {reload}")

    # Run server
    uvicorn.run(
        "main_refactored:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level.lower(),
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("👋 Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Server failed to start: {e}")
        sys.exit(1)
