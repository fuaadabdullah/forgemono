import os
import sys
import asyncio
from pathlib import Path
from fastapi import FastAPI, Body, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Add current directory to path for relative imports
sys.path.insert(0, str(Path(__file__).parent))

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
from .health.llm_health import router as llm_health_router
from .dashboard_router import router as dashboard_router
from .rag_router import router as rag_router
from .routers.goblins_router import router as goblins_router
from .routers.cost_router import router as cost_router
from .routers.user_auth_router import router as user_auth_router
from .support_router import router as support_router

# Multi-cloud orchestrator
try:
    from .orchestrator import orchestrator_router
except ImportError:
    from fastapi import APIRouter

    orchestrator_router = APIRouter()

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

    # Seed the database only if database is properly initialized
    from .database import _db_initialized

    if _db_initialized and SessionLocal is not None:
        db = SessionLocal()
        try:
            seed_database(db)
        finally:
            db.close()
    else:
        print("[WARNING] Skipping database seeding - database not properly initialized")
        print("[WARNING] Set DATABASE_URL to a valid PostgreSQL connection string")

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

    # Stop routing probe worker (if it exists)
    try:
        global routing_probe_worker
        if routing_probe_worker:
            await routing_probe_worker.stop()
            print("Stopped routing probe worker")
    except (NameError, AttributeError):
        # routing_probe_worker not initialized or doesn't exist
        pass

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
v1_router.include_router(rag_router, tags=["rag"])
v1_router.include_router(raptor_router, tags=["raptor"])  # Raptor monitoring endpoints
v1_router.include_router(health_router, tags=["health"])  # Health monitoring endpoints
v1_router.include_router(llm_health_router, tags=["health"])  # LLM gateway health
v1_router.include_router(
    dashboard_router, tags=["dashboard"]
)  # Optimized dashboard endpoints
v1_router.include_router(goblins_router, tags=["goblins"])
v1_router.include_router(cost_router, tags=["cost"])
v1_router.include_router(user_auth_router, tags=["auth"])
v1_router.include_router(support_router, tags=["support"])
v1_router.include_router(
    orchestrator_router, tags=["orchestrator"]
)  # Multi-cloud AI orchestration

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
app.include_router(rag_router)
app.include_router(raptor_router)  # Raptor monitoring endpoints
app.include_router(health_router)  # Health monitoring endpoints
app.include_router(llm_health_router)  # LLM gateway health
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
    """Generate completion with automatic fallback - prioritizes GCP self-hosted and free-tier providers."""
    import httpx

    messages = [{"role": "user", "content": prompt}]
    errors = []

    # 1. Try GCP Ollama self-hosted first (short timeout)
    ollama_url = os.getenv("OLLAMA_GCP_URL") or os.getenv("OLLAMA_BASE_URL")
    api_key = os.getenv("LOCAL_LLM_API_KEY")

    if ollama_url:
        try:
            adapter = OllamaAdapter(api_key=api_key, base_url=ollama_url)
            result = await adapter.generate(messages, model=model)
            return result
        except Exception as e:
            errors.append(f"Ollama/GCP: {e}")
            logger.warning(f"Ollama/GCP failed: {e}")

    # 1b. Try GCP llama.cpp server as secondary self-hosted option
    llamacpp_url = os.getenv("LLAMACPP_GCP_URL")
    if llamacpp_url:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{llamacpp_url.rstrip('/')}/v1/chat/completions",
                    headers={"Content-Type": "application/json"},
                    json={
                        "messages": messages,
                        "max_tokens": 1024,
                    },
                )
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return {
                    "content": content,
                    "usage": data.get("usage", {}),
                    "model": data.get("model", "llamacpp"),
                    "provider": "llamacpp-gcp",
                    "finish_reason": data["choices"][0].get("finish_reason", "stop"),
                }
        except Exception as e:
            errors.append(f"LlamaCpp/GCP: {e}")
            logger.warning(f"LlamaCpp/GCP failed: {e}")

    # 2. Try Google Gemini (reliable, generous free tier)
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}",
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"maxOutputTokens": 1024},
                    },
                )
                response.raise_for_status()
                data = response.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                usage_meta = data.get("usageMetadata", {})
                return {
                    "content": text,
                    "usage": {
                        "prompt_tokens": usage_meta.get("promptTokenCount", 0),
                        "completion_tokens": usage_meta.get("candidatesTokenCount", 0),
                        "total_tokens": usage_meta.get("totalTokenCount", 0),
                    },
                    "model": "gemini-2.0-flash",
                    "provider": "gemini",
                    "finish_reason": data["candidates"][0].get("finishReason", "STOP"),
                }
        except Exception as e:
            errors.append(f"Gemini: {e}")
            logger.warning(f"Gemini failed: {e}")

    # 3. Try Groq (free tier - very reliable, fast)
    groq_key = os.getenv("GROK_API_KEY") or os.getenv("GROQ_API_KEY")
    if groq_key and groq_key != "placeholder":
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {groq_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "llama-3.1-8b-instant",
                        "messages": messages,
                        "max_tokens": 1024,
                    },
                )
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return {
                    "content": content,
                    "usage": data.get("usage", {}),
                    "model": data.get("model", "llama-3.1-8b-instant"),
                    "provider": "groq",
                    "finish_reason": data["choices"][0].get("finish_reason", "stop"),
                }
        except Exception as e:
            errors.append(f"Groq: {e}")
            logger.warning(f"Groq failed: {e}")

    # 4. Try DeepSeek (very cheap and reliable)
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    if deepseek_key and deepseek_key != "placeholder":
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.deepseek.com/chat/completions",
                    headers={
                        "Authorization": f"Bearer {deepseek_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": messages,
                        "max_tokens": 1024,
                    },
                )
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return {
                    "content": content,
                    "usage": data.get("usage", {}),
                    "model": data.get("model", "deepseek-chat"),
                    "provider": "deepseek",
                    "finish_reason": data["choices"][0].get("finish_reason", "stop"),
                }
        except Exception as e:
            errors.append(f"DeepSeek: {e}")
            logger.warning(f"DeepSeek failed: {e}")

    # 5. Fallback to OpenAI
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key and openai_key != "placeholder":
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {openai_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "gpt-4o-mini",
                        "messages": messages,
                        "max_tokens": 1024,
                    },
                )
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return {
                    "content": content,
                    "usage": data.get("usage", {}),
                    "model": data.get("model", "gpt-4o-mini"),
                    "provider": "openai",
                    "finish_reason": data["choices"][0].get("finish_reason", "stop"),
                }
        except Exception as e:
            errors.append(f"OpenAI: {e}")
            logger.warning(f"OpenAI failed: {e}")

    # 6. Final fallback to Anthropic
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key and anthropic_key != "placeholder":
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": anthropic_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "claude-3-haiku-20240307",
                        "max_tokens": 1024,
                        "messages": messages,
                    },
                )
                response.raise_for_status()
                data = response.json()
                content = data["content"][0]["text"]
                return {
                    "content": content,
                    "usage": data.get("usage", {}),
                    "model": data.get("model", "claude-3-haiku-20240307"),
                    "provider": "anthropic",
                    "finish_reason": data.get("stop_reason", "stop"),
                }
        except Exception as e:
            errors.append(f"Anthropic: {e}")
            logger.error(f"All providers failed: {errors}")

    raise HTTPException(
        status_code=503,
        detail=f"All inference providers unavailable. Errors: {'; '.join(errors)}",
    )


app.include_router(ollama_router)
