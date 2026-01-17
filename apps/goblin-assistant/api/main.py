#!/usr/bin/env python3
"""
Main FastAPI application for Goblin Assistant
Combines all the routers into a single application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# Load environment variables from .env.local if it exists
try:
    from dotenv import load_dotenv
    import pathlib

    # Get the directory of this file (goblin-assistant directory)
    current_dir = pathlib.Path(__file__).parent.parent

    # Try to load .env files from the goblin-assistant root
    env_local = current_dir / ".env.local"
    env_file = current_dir / ".env"

    if env_local.exists():
        load_dotenv(str(env_local))
    if env_file.exists():
        load_dotenv(str(env_file))
except ImportError:
    # dotenv not available, continue without it
    import sys

    print(
        "Warning: python-dotenv not installed, skipping .env loading", file=sys.stderr
    )

    print(
        "Warning: python-dotenv not installed, skipping .env loading", file=sys.stderr
    )

# Initialize Sentry for error monitoring
try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.starlette import StarletteIntegration

    sentry_sdk.init(
        dsn=os.getenv(
            "SENTRY_DSN",
            "https://5c879ce5d51bef64d0790a645415d5cc@o4510481074683904.ingest.us.sentry.io/4510481074946048",
        ),
        # Enable performance monitoring
        traces_sample_rate=1.0,
        # Enable profiling
        profiles_sample_rate=1.0,
        # Enable request body capture
        send_default_pii=True,
        # Integrations
        integrations=[
            StarletteIntegration(transaction_style="endpoint"),
            FastApiIntegration(transaction_style="endpoint"),
        ],
        # Environment
        environment=os.getenv("ENVIRONMENT", "development"),
        # Release tracking
        release=os.getenv("RELEASE_VERSION", "goblin-assistant@1.0.0"),
    )
    print("✅ Sentry SDK initialized for error monitoring")
except ImportError:
    print("⚠️  Sentry SDK not available - install with: pip install sentry-sdk")
except Exception as e:
    print(f"⚠️  Failed to initialize Sentry SDK: {e}")

# Import all routers (use package-qualified imports so tests can import api.main)
from .api_router import router as api_router
from .auth.router import router as auth_router
from .routing_router import router as routing_router
from .execute_router import router as execute_router
from .execute_router_v1 import router as execute_router_v1
from .execute_router_v2 import router as execute_router_v2
from .parse_router import router as parse_router
from .raptor_router import router as raptor_router

# Import middlewares (from middleware.py file, not middleware/ package)
from .middleware import (
    AuthenticationMiddleware,
    SecurityHeadersMiddleware,
    ErrorHandlingMiddleware,
)

from .chat_router import router as chat_router
from .semantic_chat_router import router as semantic_chat_router
from .write_time_router import router as write_time_router
from .health import router as health_router
from .ops_router import router as ops_router
from .api_keys_router import router as api_keys_router
from .settings_router import router as settings_router
from .search_router import router as search_router
from .stream_router import router as stream_router
from .routes.privacy import router as privacy_router  # Updated to new location
from .secrets_router import (
    router as secrets_router,
    init_secrets_adapter,
    cleanup_secrets_adapter,
)
from .observability.debug_router import router as debug_router
from .storage.cache import cache
from .storage.database import init_db

from .monitoring import monitor

# Import routing analytics router (new)
try:
    from .routes.routing_analytics import router as routing_analytics_router

    ROUTING_ANALYTICS_AVAILABLE = True
except ImportError:
    ROUTING_ANALYTICS_AVAILABLE = False
    routing_analytics_router = None

# Create FastAPI app
app = FastAPI(
    title="Goblin Assistant API",
    description="AI-powered development assistant with multi-provider routing",
    version="1.0.0",
)


@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup"""
    try:
        print("🚀 Starting Goblin Assistant API...")

        # Initialize Redis cache
        print("📦 Initializing Redis cache...")
        try:
            await cache.init_redis()
            print("✅ Redis cache initialized")
        except Exception as e:
            print(f"⚠️  Redis initialization failed: {e}")
            print("   Continuing without Redis cache - performance may be reduced")

        # Initialize database tables (optional for now)
        print("🗄️  Checking database availability...")
        try:
            db_initialized = await init_db()
            if db_initialized:
                print("✅ Database initialized")
            else:
                print("⚠️  Database initialization skipped - running in limited mode")
        except Exception as e:
            print(f"⚠️  Database initialization failed: {e}")
            print("   Continuing without database - some features may be limited")

        # Start provider monitoring
        print("📊 Starting provider monitoring...")
        try:
            await monitor.start()
            print("✅ Provider monitoring started")
        except Exception as e:
            print(f"⚠️  Provider monitoring failed to start: {e}")
            print("   Continuing without provider monitoring...")

        # Start AI provider health monitoring (smart routing)
        print("🧠 Starting AI provider health monitoring...")
        try:
            from .services.provider_health import health_monitor

            await health_monitor.start_monitoring()
            print("✅ AI provider health monitoring started")
        except Exception as e:
            print(f"⚠️  AI provider health monitoring failed: {e}")
            print(
                "   Continuing without health monitoring - routing may be degraded..."
            )

        # Initialize secrets adapter
        print("🔐 Initializing secrets adapter...")
        try:
            await init_secrets_adapter()
            print("✅ Secrets adapter initialized")
        except Exception as e:
            print(f"⚠️  Warning: Failed to initialize secrets adapter: {e}")
            print("   Continuing startup without secrets management...")

        # Check privacy features
        print("🔒 Checking privacy & security features...")
        try:
            from .services.sanitization import sanitize_input_for_model
            from .services.telemetry import log_inference_metrics

            print("✅ PII sanitization available")
            print("✅ Telemetry with redaction available")
        except Exception as e:
            print(f"⚠️  Warning: Privacy features not fully loaded: {e}")

        try:
            from .services import VECTOR_STORE_AVAILABLE

            if VECTOR_STORE_AVAILABLE:
                print("✅ Safe vector store available")
            else:
                print(
                    "⚠️  Safe vector store unavailable (sentence-transformers not installed)"
                )
        except Exception:
            pass

        print("🎉 Goblin Assistant API startup complete!")

    except Exception as e:
        print(f"❌ Critical startup error: {e}")
        print("💥 Application will restart due to startup failure")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    try:
        print("🛑 Shutting down Goblin Assistant API...")

        # Stop AI provider health monitoring
        print("🧠 Stopping AI provider health monitoring...")
        try:
            from .services.provider_health import health_monitor

            await health_monitor.stop_monitoring()
            print("✅ AI provider health monitoring stopped")
        except Exception as e:
            print(f"⚠️  Warning: Failed to stop health monitoring: {e}")

        print("📊 Stopping provider monitoring...")
        await monitor.stop()
        print("✅ Provider monitoring stopped")

        print("📦 Closing Redis cache...")
        await cache.close()
        print("✅ Redis cache closed")

        print("🔐 Cleaning up secrets adapter...")
        try:
            await cleanup_secrets_adapter()
            print("✅ Secrets adapter cleaned up")
        except Exception as e:
            print(f"⚠️  Warning: Failed to cleanup secrets adapter: {e}")

        print("🎉 Goblin Assistant API shutdown complete!")

    except Exception as e:
        print(f"❌ Error during shutdown: {e}")
        # Don't raise here as we're shutting down


# Add Error Handling middleware
app.add_middleware(ErrorHandlingMiddleware)

# Add Security Headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Add Rate Limiting middleware for privacy/security (requires Redis)
try:
    from .middleware.rate_limiter import RateLimiter

    rate_limiter = RateLimiter(
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
        requests_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "100")),
        requests_per_hour=int(os.getenv("RATE_LIMIT_PER_HOUR", "1000")),
    )
    app.middleware("http")(rate_limiter)
    print("✅ Rate limiting middleware enabled (100/min, 1000/hour)")
except ImportError:
    print("⚠️  Rate limiting unavailable - install redis: pip install redis")
except Exception as e:
    print(f"⚠️  Rate limiting disabled: {e}")

# Add Authentication middleware
app.add_middleware(
    AuthenticationMiddleware,
    exclude_paths=[
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/auth/register",
        "/auth/login",
        "/auth/oauth/google",
        "/auth/oauth/google/callback",
        "/auth/passkey/register",
        "/auth/passkey/authenticate",
        "/api/chat",  # Allow chat API in development
        "/chat",  # Allow chat routes in development
    ],
)

# Add CORS middleware
# Environment-aware CORS configuration
environment = os.getenv("ENVIRONMENT", "development").lower()
if environment == "production":
    # Production: Only allow specific origins, no wildcards
    allowed_origins = (
        os.getenv("ALLOWED_ORIGINS", "").split(",")
        if os.getenv("ALLOWED_ORIGINS")
        else []
    )
    if not allowed_origins:
        print("⚠️  SECURITY WARNING: No ALLOWED_ORIGINS configured for production!")
        print("   Set ALLOWED_ORIGINS environment variable with comma-separated URLs")
        # Fall back to the canonical frontend + worker domains so users aren't blocked by CORS
        allowed_origins = [
            "https://goblin.fuaad.ai",  # Primary frontend (Cloudflare)
            "https://api.goblin.fuaad.ai",  # API domain (used for preflight checks)
            "https://goblin-assistant-edge.fuaadabdullah.workers.dev",  # Worker dev domain
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
else:
    # Development: Allow localhost
    allowed_origins = (
        os.getenv("ALLOWED_ORIGINS", "").split(",")
        if os.getenv("ALLOWED_ORIGINS")
        else ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001"]
    )

if "*" in allowed_origins:
    print("🚨 SECURITY RISK: CORS is configured to allow all origins (*)!")
    print(
        "   This is acceptable only for development. Set specific origins for production."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"]
    if environment != "production"
    else [
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-API-Key",
        "X-CSRF-Token",
    ],
)

# Include all routers
app.include_router(api_router)
app.include_router(auth_router)
app.include_router(routing_router)
app.include_router(execute_router)  # Legacy /execute endpoints
app.include_router(execute_router_v1)  # New /v1/execute endpoints
app.include_router(execute_router_v2)  # Docker-isolated /v2/execute endpoints
app.include_router(parse_router)
app.include_router(raptor_router)
app.include_router(api_keys_router)
app.include_router(settings_router)
app.include_router(search_router)
app.include_router(stream_router)
app.include_router(chat_router)
app.include_router(semantic_chat_router)
app.include_router(write_time_router)
app.include_router(health_router)
app.include_router(ops_router)
app.include_router(secrets_router)
app.include_router(privacy_router)  # GDPR/CCPA compliance
app.include_router(debug_router)

# Include routing analytics router (new smart routing)
if ROUTING_ANALYTICS_AVAILABLE and routing_analytics_router:
    app.include_router(routing_analytics_router)


@app.get("/test")
async def test_endpoint():
    """Simple test endpoint without database"""
    return {"message": "Server is working", "status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003)
