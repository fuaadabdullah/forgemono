import os
import sys
import asyncio
from pathlib import Path
from fastapi import FastAPI, Body, APIRouter
from fastapi.middleware.cors import CORSMiddleware

# Initialize monitoring first (before other imports)
from .monitoring import init_sentry
from .opentelemetry_config import init_opentelemetry, instrument_fastapi_app

init_sentry()
init_opentelemetry()

# Ensure dynamic module paths are available before importing project routers
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "GoblinOS"))
# Ensure we do NOT insert the legacy `api/` folder into sys.path as it may
# shadow the actual backend package (see REORG_PLAN.md). If additional
# import paths are required for development, add them explicitly and prefer
# `apps/goblin-assistant/backend/`.

# Import middleware
from .middleware.rate_limiter import RateLimitMiddleware, limiter
from .middleware.logging_middleware import StructuredLoggingMiddleware, setup_logging
from .middleware.request_id_middleware import RequestIDMiddleware
from .middleware.security_headers import SecurityHeadersMiddleware

# Import routers
from .debugger.router import router as debugger_router
from .providers.ollama_adapter import OllamaAdapter

try:  # Prefer full implementation
    from .auth.router import router as auth_router, cleanup_expired_challenges  # type: ignore
except Exception:  # noqa: BLE001
    try:
        from .auth.router import router as auth_router  # type: ignore
    except Exception:  # noqa: BLE001
        # As a last resort define a minimal router stub to keep app booting.
        from fastapi import APIRouter

        auth_router = APIRouter()

    async def cleanup_expired_challenges():  # type: ignore
        """Fallback no-op when real cleanup function is unavailable.
        Returns 0 to indicate no challenges were cleaned.
        """
        return 0


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

# Database imports
from .database import create_tables, SessionLocal
from .seed import seed_database

# Add GoblinOS to path for raptor
try:
    from raptor_mini import raptor  # type: ignore
except ImportError:

    class _RaptorStub:
        def start(self):
            print("Raptor stub start (module not found)")

        def stop(self):
            print("Raptor stub stop (module not found)")

    raptor = _RaptorStub()


async def validate_startup_configuration():
    """Validate critical configuration and dependencies before server starts"""
    print("🔍 Validating startup configuration...")

    issues = []

    # Check configuration
    try:
        from .config import settings

        print(
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
        print("⚠️  Dependency checker not available - skipping automated checks")
    except Exception as e:
        issues.append(f"Dependency validation failed: {e}")

    # Report issues
    if issues:
        print("❌ Startup validation failed:")
        for issue in issues:
            print(f"  - {issue}")
        print(
            "\n🚨 Critical configuration issues detected. Server may not function properly."
        )
        print("   Check the issues above and fix before proceeding to production.")
        # Don't exit - allow server to start with warnings for development
        if settings.is_production:
            print(
                "   In production environment, these issues should be resolved immediately."
            )
    else:
        print("✅ Startup validation passed - all systems ready")

    return len(issues) == 0


"""FastAPI backend main module with deferred initialization.

Adjust import of cleanup_expired_challenges to be resilient when an alternate
auth package (e.g. apps/goblin-assistant/api/auth) shadows the intended
backend/auth module and does not expose the function. We fall back to a stub
to avoid hard startup failure while still cleaning up gracefully when the
real implementation is available.

Version: 1.0.1 - Structured logging enabled
"""

app = FastAPI(
    title="GoblinOS Assistant Backend",
    description="Backend API for GoblinOS Assistant with debug capabilities",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Instrument FastAPI app with OpenTelemetry
instrument_fastapi_app(app)

# Configure structured logging
log_level = os.getenv("LOG_LEVEL", "INFO")
logger = setup_logging(log_level)


# Global variables for routing components
challenge_cleanup_task = None
rate_limiter_cleanup_task = None


SKIP_RAPTOR_INIT = os.getenv("SKIP_RAPTOR_INIT", "0") == "1"


# Create database tables on startup (keep minimal blocking work only)
@app.on_event("startup")
async def startup_event():
    # Validate configuration first
    await validate_startup_configuration()

    create_tables()

    # Seed the database
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()

    # Always start challenge cleanup early (cheap)
    global challenge_cleanup_task
    challenge_cleanup_task = asyncio.create_task(challenge_cleanup_worker())
    print("Started challenge cleanup background task")

    # Start rate limiter cleanup
    global rate_limiter_cleanup_task
    rate_limiter_cleanup_task = asyncio.create_task(rate_limiter_cleanup_worker())
    print("Started rate limiter cleanup background task")

    # Defer expensive initializations to background task for faster readiness
    asyncio.create_task(deferred_initialization())


async def deferred_initialization():
    """Run heavier, optional startup tasks without blocking server accept loop."""
    await asyncio.sleep(0)  # yield control
    # Raptor monitoring system (optional)
    if SKIP_RAPTOR_INIT:
        print("Skipping Raptor monitoring init (SKIP_RAPTOR_INIT=1)")
    else:
        try:
            raptor.start()
            print("Started Raptor monitoring system (deferred)")
        except Exception as e:
            print(f"Warning: Deferred Raptor monitoring start failed: {e}")

    # Initialize APScheduler for lightweight periodic tasks
    try:
        from .scheduler import start_scheduler

        start_scheduler()
        print("Started APScheduler for lightweight periodic tasks (deferred)")
    except Exception as e:
        print(f"Warning: Deferred APScheduler start failed: {e}")

    # Initialize routing probe worker if encryption key is available (optional)
    # REMOVED: APScheduler with Redis locks now handles all periodic probing
    # to prevent duplicate work across replicas


async def challenge_cleanup_worker():
    """Background worker to clean up expired challenges every 10 minutes"""
    while True:
        try:
            await asyncio.sleep(600)  # Run every 10 minutes
            count = await cleanup_expired_challenges()
            if count > 0:
                print(f"Cleaned up {count} expired challenges")
        except asyncio.CancelledError:
            print("Challenge cleanup worker cancelled")
            break
        except Exception as e:
            print(f"Error in challenge cleanup worker: {e}")


async def rate_limiter_cleanup_worker():
    """Background worker to clean up old rate limiter entries every 5 minutes"""
    while True:
        try:
            await asyncio.sleep(300)  # Run every 5 minutes
            limiter.cleanup_old_entries()
            logger.info("Rate limiter cleanup completed")
        except asyncio.CancelledError:
            print("Rate limiter cleanup worker cancelled")
            break
        except Exception as e:
            print(f"Error in rate limiter cleanup worker: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    # Stop APScheduler
    try:
        from .scheduler import stop_scheduler

        stop_scheduler()
        print("Stopped APScheduler")
    except Exception as e:
        print(f"Warning: Failed to stop APScheduler: {e}")

    # Stop Raptor monitoring system
    try:
        raptor.stop()
        print("Stopped Raptor monitoring system")
    except Exception as e:
        print(f"Warning: Failed to stop Raptor monitoring: {e}")

    # Stop routing probe worker
    global routing_probe_worker
    if routing_probe_worker:
        await routing_probe_worker.stop()
        print("Stopped routing probe worker")

    # Stop challenge cleanup task
    global challenge_cleanup_task
    if challenge_cleanup_task:
        challenge_cleanup_task.cancel()
        try:
            await challenge_cleanup_task
        except asyncio.CancelledError:
            pass
        print("Stopped challenge cleanup background task")

    # Stop rate limiter cleanup task
    global rate_limiter_cleanup_task
    if rate_limiter_cleanup_task:
        rate_limiter_cleanup_task.cancel()
        try:
            await rate_limiter_cleanup_task
        except asyncio.CancelledError:
            pass
        print("Stopped rate limiter cleanup background task")


# Add request ID middleware (must be before logging middleware)
app.add_middleware(RequestIDMiddleware)

# Add structured logging middleware
app.add_middleware(StructuredLoggingMiddleware)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# CORS middleware for frontend integration
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

# Create versioned API router
v1_router = APIRouter(prefix="/v1")

# Include all routers under v1
v1_router.include_router(auth_router, tags=["auth"])
v1_router.include_router(search_router, tags=["search"])
v1_router.include_router(settings_router, tags=["settings"])
v1_router.include_router(execute_router, tags=["execute"])
v1_router.include_router(api_keys_router, tags=["api-keys"])
v1_router.include_router(parse_router, tags=["parse"])
v1_router.include_router(routing_router, tags=["routing"])
v1_router.include_router(chat_router, tags=["chat"])
v1_router.include_router(api_router, tags=["api"])
v1_router.include_router(stream_router, tags=["stream"])
v1_router.include_router(raptor_router, tags=["raptor"])  # Raptor monitoring endpoints
v1_router.include_router(health_router, tags=["health"])  # Health monitoring endpoints
v1_router.include_router(
    dashboard_router, tags=["dashboard"]
)  # Optimized dashboard endpoints
v1_router.include_router(goblins_router, tags=["goblins"])
v1_router.include_router(cost_router, tags=["cost"])
v1_router.include_router(user_auth_router, tags=["auth"])

# Include routers (keeping legacy routes for backward compatibility)
app.include_router(debugger_router)
app.include_router(v1_router)  # Versioned API routes
app.include_router(auth_router)  # Legacy auth routes
app.include_router(jwt_auth_router)  # JWT authentication routes
app.include_router(search_router)
app.include_router(settings_router)
app.include_router(execute_router)
app.include_router(api_keys_router)
app.include_router(parse_router)
app.include_router(routing_router)
app.include_router(chat_router)
app.include_router(api_router)
app.include_router(stream_router)
app.include_router(raptor_router)  # Raptor monitoring endpoints
app.include_router(health_router)  # Health monitoring endpoints
app.include_router(dashboard_router)  # Optimized dashboard endpoints


@app.get("/")
async def root():
    return {"message": "GoblinOS Assistant Backend API"}


@app.get("/health")
async def health():
    # Base health
    result = {"status": "healthy"}

    return result


ollama_router = APIRouter()


@ollama_router.post("/api/generate")
async def ollama_generate(prompt: str = Body(...), model: str = Body("llama2")):
    adapter = OllamaAdapter()
    result = adapter.generate(prompt, model)
    return result


app.include_router(ollama_router)
