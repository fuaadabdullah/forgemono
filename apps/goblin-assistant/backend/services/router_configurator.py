"""
RouterConfigurator Service for managing FastAPI router setup.

This service handles all router configuration and setup,
separating it from the main application logic for better organization.
"""

import logging
from typing import List
from fastapi import APIRouter, FastAPI

logger = logging.getLogger(__name__)


class RouterConfigurator:
    """Service for configuring and setting up routers."""

    def __init__(self):
        """Initialize the RouterConfigurator."""
        self.routers_added = []

    def configure_all_routers(self, app: FastAPI) -> None:
        """Configure all routers for the FastAPI application."""
        logger.info("🔧 Configuring routers...")

        # Create versioned API router
        v1_router = self._create_versioned_router()

        # Add routers to the main application
        self._add_debugger_router(app)
        self._add_versioned_routers(app, v1_router)
        self._add_legacy_routers(app)

        logger.info(f"✅ Configured {len(self.routers_added)} router components")

    def _create_versioned_router(self) -> APIRouter:
        """Create the versioned API router."""
        v1_router = APIRouter(prefix="/v1")
        logger.info("✅ Created versioned API router (v1)")
        return v1_router

    def _add_debugger_router(self, app: FastAPI) -> None:
        """Add the debugger router."""
        try:
            from .debugger.router import router as debugger_router
            app.include_router(debugger_router)
            self.routers_added.append("debugger_router")
            logger.info("✅ Added debugger router")
        except ImportError as e:
            logger.warning(f"⚠️  Failed to import debugger router: {e}")

    def _add_versioned_routers(self, app: FastAPI, v1_router: APIRouter) -> None:
        """Add versioned routers to the application."""
        # Import and add all v1 routers
        router_configs = [
            ("search_router", "search"),
            ("settings_router", "settings"),
            ("execute_router", "execute"),
            ("auth.api_keys_router", "api-keys"),
            ("auth.auth_router", "auth"),
            ("parse_router", "parse"),
            ("routing_router", "routing"),
            ("chat_router", "chat"),
            ("api_router", "api"),
            ("stream_router", "stream"),
            ("raptor_router", "raptor"),
            ("health_router", "health"),
            ("health.llm_health", "health"),
            ("dashboard_router", "dashboard"),
            ("routers.goblins_router", "goblins"),
            ("routers.cost_router", "cost"),
            ("routers.user_auth_router", "auth"),
        ]

        for router_import, tag in router_configs:
            try:
                if router_import == "raptor_router":
                    # Special handling for raptor router
                    try:
                        from .raptor_router import router as raptor_router
                        v1_router.include_router(raptor_router, tags=[tag])
                        self.routers_added.append(f"{router_import} (v1)")
                        logger.info(f"✅ Added {router_import} to v1 router")
                    except ImportError:
                        logger.warning(f"⚠️  raptor_router not available, skipping")
                        continue
                else:
                    # Regular router import
                    router_module = __import__(f".{router_import}", fromlist=["router"])
                    router = router_module.router
                    v1_router.include_router(router, tags=[tag])
                    self.routers_added.append(f"{router_import} (v1)")
                    logger.info(f"✅ Added {router_import} to v1 router")

            except ImportError as e:
                logger.warning(f"⚠️  Failed to import {router_import}: {e}")
            except AttributeError as e:
                logger.warning(f"⚠️  Router not found in {router_import}: {e}")

        # Include the versioned router in the main app
        app.include_router(v1_router)
        self.routers_added.append("v1_router")
        logger.info("✅ Added v1 router to main application")

    def _add_legacy_routers(self, app: FastAPI) -> None:
        """Add legacy routers for backward compatibility."""
        legacy_router_configs = [
            "search_router",
            "settings_router",
            "execute_router",
            "auth.api_keys_router",
            "auth.auth_router",
            "parse_router",
            "routing_router",
            "chat_router",
            "api_router",
            "stream_router",
            "health_router",
            "health.llm_health",
            "dashboard_router",
        ]

        for router_import in legacy_router_configs:
            try:
                if router_import == "health.llm_health":
                    from .health.llm_health import router as llm_health_router
                    app.include_router(llm_health_router)
                    self.routers_added.append(f"{router_import} (legacy)")
                    logger.info(f"✅ Added {router_import} as legacy router")
                else:
                    router_module = __import__(f".{router_import}", fromlist=["router"])
                    router = router_module.router
                    app.include_router(router)
                    self.routers_added.append(f"{router_import} (legacy)")
                    logger.info(f"✅ Added {router_import} as legacy router")

            except ImportError as e:
                logger.warning(f"⚠️  Failed to import legacy {router_import}: {e}")
            except AttributeError as e:
                logger.warning(f"⚠️  Router not found in legacy {router_import}: {e}")

    def get_router_list(self) -> List[str]:
        """Get list of configured routers."""
        return self.routers_added.copy()

    def cleanup(self) -> None:
        """Clean up router resources."""
        logger.info("Router resources cleaned up")