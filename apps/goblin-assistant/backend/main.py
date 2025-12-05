import os
import sys
import asyncio
from pathlib import Path
from fastapi import FastAPI, Body, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response

# Ensure dynamic module paths are available before importing project routers
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "GoblinOS"))
sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

# Import middleware
from middleware.rate_limiter import RateLimitMiddleware, limiter
from middleware.logging_middleware import StructuredLoggingMiddleware, setup_logging
from middleware.request_id_middleware import RequestIDMiddleware
from middleware.metrics import PrometheusMiddleware, get_metrics, CONTENT_TYPE_LATEST

# Import routers
from debugger.router import router as debugger_router
from providers.ollama_adapter import OllamaAdapter

try:  # Prefer full implementation
    from backend.auth.router import router as auth_router, cleanup_expired_challenges  # type: ignore
except Exception:  # noqa: BLE001
    try:
        from auth.router import router as auth_router  # type: ignore
    except Exception:  # noqa: BLE001
        # As a last resort define a minimal router stub to keep app booting.
        from fastapi import APIRouter

        auth_router = APIRouter()

    async def cleanup_expired_challenges():  # type: ignore
        """Fallback no-op when real cleanup function is unavailable.
        Returns 0 to indicate no challenges were cleaned.
        """
        return 0


from search_router import router as search_router
from settings_router import router as settings_router
from execute_router import router as execute_router
from api_keys_router import router as api_keys_router
from parse_router import router as parse_router
from routing_router import router as routing_router
from chat_router import router as chat_router
from api_router import router as api_router
from stream_router import router as stream_router
from health_router import router as health_router
from dashboard_router import router as dashboard_router
from tasks.provider_probe_worker import ProviderProbeWorker

try:
    from raptor_router import router as raptor_router
except ImportError:
    # Create a stub router if raptor_mini is not available
    from fastapi import APIRouter

    raptor_router = APIRouter()

# Database imports
from database import create_tables
from backend.auth.challenge_store import get_challenge_store_instance

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
        from config import settings

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

    # Check challenge store
    try:
        challenge_store = get_challenge_store_instance()
        health = challenge_store.health_check()
        print(
            f"✅ Challenge store initialized: redis_available={health['redis_available']}"
        )

        if health.get("fallback_mode") and settings.should_alert_on_fallback:
            issues.append(
                "CRITICAL: Challenge store in fallback mode in production multi-instance"
            )

    except Exception as e:
        issues.append(f"Challenge store validation failed: {e}")

    # Check critical dependencies
    try:
        from scripts.check_dependencies import check_pydantic_email, check_redis

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

Version: 1.0.1 - Datadog logging enabled
"""

app = FastAPI(
    title="GoblinOS Assistant Backend",
    description="Backend API for GoblinOS Assistant with debug capabilities",
    version="1.0.0",
)

# Configure structured logging
log_level = os.getenv("LOG_LEVEL", "INFO")
logger = setup_logging(log_level)


# Global variables for routing components
routing_probe_worker = None
challenge_cleanup_task = None
rate_limiter_cleanup_task = None


SKIP_RAPTOR_INIT = os.getenv("SKIP_RAPTOR_INIT", "0") == "1"
SKIP_PROBE_INIT = os.getenv("SKIP_PROBE_INIT", "0") == "1"


# Create database tables on startup (keep minimal blocking work only)
@app.on_event("startup")
async def startup_event():
    # Validate configuration first
    await validate_startup_configuration()

    create_tables()

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

    # Initialize routing probe worker if encryption key is available (optional)
    global routing_probe_worker
    if SKIP_PROBE_INIT:
        print("Skipping routing probe worker init (SKIP_PROBE_INIT=1)")
    else:
        routing_encryption_key = os.getenv("ROUTING_ENCRYPTION_KEY")
        if routing_encryption_key:
            try:
                routing_probe_worker = ProviderProbeWorker(routing_encryption_key)
                await routing_probe_worker.start()
                print("Started routing probe worker (deferred)")
            except Exception as e:
                print(f"Warning: Deferred routing probe worker start failed: {e}")
        else:
            print("ROUTING_ENCRYPTION_KEY not set; probe worker not started")


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


# Add Prometheus metrics middleware (must be before other middleware)
app.add_middleware(PrometheusMiddleware)

# Add request ID middleware (must be before logging middleware)
app.add_middleware(RequestIDMiddleware)

# Add structured logging middleware
app.add_middleware(StructuredLoggingMiddleware)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# CORS middleware for frontend integration
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,  # Configure via CORS_ORIGINS env var
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(debugger_router)
app.include_router(auth_router)
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

    # Include auth challenge store health when available
    try:
        cs = get_challenge_store_instance()
        if hasattr(cs, "health_check"):
            result["challenge_store"] = cs.health_check()
    except Exception as e:
        result["challenge_store"] = {"error": str(e)}

    return result


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint for monitoring."""
    return Response(content=get_metrics(), media_type=CONTENT_TYPE_LATEST)


ollama_router = APIRouter()


@ollama_router.post("/api/generate")
async def ollama_generate(prompt: str = Body(...), model: str = Body("llama2")):
    adapter = OllamaAdapter()
    result = adapter.generate(prompt, model)
    return result


app.include_router(ollama_router)
