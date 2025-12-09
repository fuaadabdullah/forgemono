from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, text
import os
import httpx
import socket
import pathlib
import urllib.parse
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from database import get_db
from models.routing import ProviderMetric, RoutingProvider
from config import settings

# Import auth components for health checks
try:
    from auth.challenge_store import get_challenge_store_instance

    challenge_store_available = True
except ImportError:
    challenge_store_available = False

# Import session cache for health checks
try:
    from cache.session_cache import get_session_cache

    session_cache_available = True
except ImportError:
    session_cache_available = False

# Import LLM adapters for health checks
try:
    from providers.ollama_adapter import OllamaAdapter
    from providers.openai_adapter import OpenAIAdapter
    from providers.anthropic_adapter import AnthropicAdapter
    from providers.grok_adapter import GrokAdapter
    from providers.deepseek_adapter import DeepSeekAdapter
except ImportError:
    # Adapters may not be available in all environments
    OllamaAdapter = None
    OpenAIAdapter = None
    AnthropicAdapter = None
    GrokAdapter = None
    DeepSeekAdapter = None


async def check_database_health(db_url: str) -> Dict[str, Any]:
    """Perform comprehensive database health check."""
    try:
        # Parse database URL
        if db_url.startswith("postgres") or db_url.startswith("postgresql"):
            # PostgreSQL connection
            import re

            m = re.search(r"@([\w\-\.]+)(?::(\d+))?", db_url)
            if m:
                host = m.group(1)
                port = int(m.group(2)) if m.group(2) else 5432

                # Test TCP connectivity
                s = socket.socket()
                s.settimeout(5)
                s.connect((host, port))
                s.close()

                # Test actual database connection and query
                db = next(get_db())
                try:
                    # Simple query to test database connectivity
                    result = db.execute(text("SELECT 1 as health_check")).fetchone()
                    db.close()

                    if result and result[0] == 1:
                        return {
                            "status": "healthy",
                            "type": "postgresql",
                            "host": host,
                            "port": port,
                            "connection_test": "passed",
                            "query_test": "passed",
                        }
                    else:
                        return {
                            "status": "degraded",
                            "type": "postgresql",
                            "host": host,
                            "port": port,
                            "connection_test": "passed",
                            "query_test": "failed",
                        }
                except Exception as e:
                    db.close()
                    return {
                        "status": "degraded",
                        "type": "postgresql",
                        "host": host,
                        "port": port,
                        "connection_test": "passed",
                        "query_test": "failed",
                        "error": str(e),
                    }
            else:
                return {
                    "status": "unhealthy",
                    "error": "Could not parse PostgreSQL URL",
                }
        else:
            return {"status": "unhealthy", "error": "Unsupported database type"}

    except socket.timeout:
        return {"status": "unhealthy", "error": "Database connection timeout"}
    except socket.gaierror:
        return {"status": "unhealthy", "error": "Database host resolution failed"}
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": f"Database health check failed: {str(e)}",
        }


async def check_llm_provider_health(
    provider_name: str, api_key: str, base_url: str
) -> Dict[str, Any]:
    """Perform comprehensive health check for LLM provider."""
    try:
        if provider_name.lower() == "ollama" and OllamaAdapter:
            # Test Ollama connectivity with detailed checks
            adapter = OllamaAdapter(api_key, base_url)
            models = await adapter.list_models()

            if models and len(models) > 0:
                # Test a simple inference call to verify functionality
                test_model = models[0].get("id", "")
                if test_model:
                    try:
                        # Quick test with minimal tokens to verify inference works
                        test_response = await adapter.chat(
                            model=test_model,
                            messages=[{"role": "user", "content": "Hello"}],
                            max_tokens=5,
                            temperature=0.0,
                        )
                        if test_response and len(test_response.strip()) > 0:
                            return {
                                "status": "healthy",
                                "models_available": len(models),
                                "sample_models": [m.get("id", "") for m in models[:3]],
                                "inference_test": "passed",
                                "response_time_ms": None,  # Could add timing here
                            }
                        else:
                            return {
                                "status": "degraded",
                                "models_available": len(models),
                                "inference_test": "failed",
                                "error": "Empty response from inference test",
                            }
                    except Exception as e:
                        return {
                            "status": "degraded",
                            "models_available": len(models),
                            "inference_test": "failed",
                            "error": f"Inference test failed: {str(e)}",
                        }
                else:
                    return {
                        "status": "degraded",
                        "models_available": len(models),
                        "inference_test": "skipped",
                        "error": "No valid model ID found",
                    }
            else:
                return {"status": "unhealthy", "error": "No models available"}

        elif provider_name.lower() == "openai" and OpenAIAdapter:
            # Test OpenAI connectivity with models list and basic inference
            adapter = OpenAIAdapter(api_key, base_url)
            models = await adapter.list_models()

            if models and len(models) > 0:
                # Test inference with a simple model
                try:
                    test_response = await adapter.chat(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": "Hello"}],
                        max_tokens=5,
                        temperature=0.0,
                    )
                    return {
                        "status": "healthy",
                        "models_available": len(models),
                        "inference_test": "passed",
                    }
                except Exception as e:
                    return {
                        "status": "degraded",
                        "models_available": len(models),
                        "inference_test": "failed",
                        "error": str(e),
                    }
            else:
                return {"status": "unhealthy", "error": "No models available"}

        elif provider_name.lower() == "anthropic" and AnthropicAdapter:
            # Test Anthropic connectivity
            adapter = AnthropicAdapter(api_key, base_url)
            try:
                # Test with Claude model
                test_response = await adapter.chat(
                    model="claude-3-haiku-20240307",
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=5,
                    temperature=0.0,
                )
                return {"status": "healthy", "inference_test": "passed"}
            except Exception as e:
                return {"status": "unhealthy", "error": str(e)}

        else:
            # Fallback to basic HTTP connectivity test
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{base_url}/health", timeout=5)
                if response.status_code < 400:
                    return {"status": "healthy", "http_status": response.status_code}
                else:
                    return {"status": "unhealthy", "http_status": response.status_code}

    except httpx.TimeoutException:
        return {"status": "unhealthy", "error": "Request timeout"}
    except httpx.ConnectError:
        return {"status": "unhealthy", "error": "Connection failed"}
    except Exception as e:
        return {"status": "unhealthy", "error": f"Health check failed: {str(e)}"}


router = APIRouter(prefix="/health", tags=["health"])


class ComprehensiveHealthResponse(BaseModel):
    """Comprehensive health check response with environment awareness"""

    status: str  # 'healthy', 'degraded', 'unhealthy'
    timestamp: str
    environment: str
    components: Dict[str, Any]


@router.get("/", response_model=ComprehensiveHealthResponse)
async def comprehensive_health_check(db: Session = Depends(get_db)):
    """
    Comprehensive health check with environment-aware status reporting.

    Checks critical components: Redis, database, auth routes, and environment safety.
    """
    checks = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.environment,
        "components": {},
    }

    # Redis/Challenge Store check
    if challenge_store_available:
        try:
            challenge_store = get_challenge_store_instance()
            redis_health = await challenge_store.health_check()

            checks["components"]["redis"] = {
                "status": "healthy" if redis_health["redis_available"] else "degraded",
                "fallback_active": redis_health["fallback_mode"],
                "safe_for_environment": redis_health["safe_for_production"],
            }

            # Alert on fallback in production multi-instance
            if redis_health["fallback_mode"] and settings.should_alert_on_fallback:
                checks["components"]["redis"]["alert"] = (
                    "CRITICAL: Memory fallback active in production multi-instance"
                )

        except Exception as e:
            checks["components"]["redis"] = {"status": "unhealthy", "error": str(e)}
            checks["status"] = "unhealthy"
    else:
        checks["components"]["redis"] = {
            "status": "unhealthy",
            "error": "Challenge store not available",
        }
        checks["status"] = "unhealthy"

    # Session Cache check
    if session_cache_available:
        try:
            session_cache = get_session_cache()
            cache_health = session_cache.health_check()

            checks["components"]["session_cache"] = {
                "status": "healthy" if cache_health["available"] else "degraded",
                "memory_used": cache_health.get("memory_used", "unknown"),
                "session_cache_ttl": cache_health.get("session_cache_ttl", "unknown"),
            }

        except Exception as e:
            checks["components"]["session_cache"] = {
                "status": "unhealthy",
                "error": str(e),
            }
            checks["status"] = "unhealthy"
    else:
        checks["components"]["session_cache"] = {
            "status": "unhealthy",
            "error": "Session cache not available",
        }
        checks["status"] = "unhealthy"

    # Database check
    try:
        # Simple connectivity test
        result = db.execute(text("SELECT 1")).fetchone()
        if result:
            checks["components"]["database"] = {"status": "healthy"}
        else:
            checks["components"]["database"] = {
                "status": "degraded",
                "message": "Database query returned no results",
            }
    except Exception as e:
        checks["components"]["database"] = {"status": "unhealthy", "error": str(e)}
        checks["status"] = "unhealthy"

    # Auth routes check
    try:
        from main import app  # Import the main FastAPI app

        auth_routes = [
            r for r in app.routes if hasattr(r, "path") and r.path.startswith("/auth")
        ]
        checks["components"]["auth_routes"] = {
            "status": "healthy" if len(auth_routes) > 0 else "unhealthy",
            "count": len(auth_routes),
            "routes": [r.path for r in auth_routes[:5]],  # Show first 5 routes
        }
        if len(auth_routes) == 0:
            checks["status"] = "unhealthy"
    except Exception as e:
        checks["components"]["auth_routes"] = {
            "status": "unhealthy",
            "error": f"Failed to check routes: {str(e)}",
        }
        checks["status"] = "unhealthy"

    # Configuration validation
    config_issues = []
    if settings.is_production and not settings.database_url:
        config_issues.append("DATABASE_URL required in production")

    if (
        settings.is_production
        and settings.allow_memory_fallback
        and settings.is_multi_instance
    ):
        config_issues.append("Memory fallback not allowed in multi-instance production")

    checks["components"]["configuration"] = {
        "status": "healthy" if not config_issues else "unhealthy",
        "issues": config_issues,
        "environment": settings.environment,
        "multi_instance": settings.is_multi_instance,
    }

    if config_issues:
        checks["status"] = "unhealthy"

    # Overall status determination
    component_statuses = [
        c.get("status", "unknown") for c in checks["components"].values()
    ]

    if "unhealthy" in component_statuses:
        checks["status"] = "unhealthy"
    elif "degraded" in component_statuses:
        checks["status"] = "degraded"
    # Otherwise remains 'healthy'

    return checks


@router.get("/health", response_model=ComprehensiveHealthResponse)
async def simple_health_check(db: Session = Depends(get_db)):
    """
    Simple health check endpoint for load balancers and monitoring systems.
    Same as comprehensive check but accessible at /health path.
    """
    return await comprehensive_health_check(db)


class HealthCheckResponse(BaseModel):
    status: str
    checks: Dict[str, Any]


class ChromaStatusResponse(BaseModel):
    status: str
    collections: int
    documents: int
    last_check: str


class MCPStatusResponse(BaseModel):
    status: str
    servers: List[str]
    active_connections: int
    last_check: str


class RaptorStatusResponse(BaseModel):
    status: str
    running: bool
    config_file: str
    last_check: str


class SandboxStatusResponse(BaseModel):
    status: str
    active_jobs: int
    queue_size: int
    last_check: str


class SchedulerStatusResponse(BaseModel):
    status: str
    jobs: List[Dict[str, Any]]
    last_check: str


class CostTrackingResponse(BaseModel):
    total_cost: float
    cost_today: float
    cost_this_month: float
    by_provider: Dict[str, float]


class LatencyHistoryResponse(BaseModel):
    timestamps: List[str]
    latencies: List[float]


class ServiceError(BaseModel):
    timestamp: str
    message: str
    service: str


class RetestServiceResponse(BaseModel):
    success: bool
    latency: Optional[float]
    message: str


@router.get("/all", response_model=HealthCheckResponse)
async def health_all():
    """Perform full health checks: database, vector DB, and providers"""
    checks: Dict[str, Any] = {}

    # DB check with comprehensive testing
    db_url = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_URL")
    if db_url:
        checks["database"] = await check_database_health(db_url)
    else:
        checks["database"] = {
            "status": "skipped",
            "reason": "DATABASE_URL or SUPABASE_URL not set",
        }

    # Vector DB check (Chroma sqlite file or connection)
    try:
        chroma_path = os.getenv("CHROMA_DB_PATH")
        if not chroma_path:
            # default path in repo
            chroma_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "chroma_db", "chroma.sqlite3"
            )
        chroma_file = pathlib.Path(chroma_path).resolve()
        if chroma_file.exists():
            checks["vector_db"] = {"status": "healthy", "path": str(chroma_file)}
        else:
            # If not file-backed, check hosted vector DBs (Qdrant/Chroma cloud)
            qdrant_url = os.getenv("QDRANT_URL") or os.getenv("CHROMA_API_URL")
            if qdrant_url:
                try:
                    parsed = urllib.parse.urlparse(qdrant_url)
                    host = parsed.hostname
                    port = parsed.port or (443 if parsed.scheme == "https" else 80)
                    # attempt a TCP connection
                    s = socket.socket()
                    s.settimeout(3)
                    s.connect((host, port))
                    s.close()
                    checks["vector_db"] = {
                        "status": "healthy",
                        "host": host,
                        "port": port,
                        "url": qdrant_url,
                    }
                except Exception as e:
                    checks["vector_db"] = {
                        "status": "unhealthy",
                        "url": qdrant_url,
                        "error": str(e),
                    }
            else:
                checks["vector_db"] = {
                    "status": "unhealthy",
                    "path": str(chroma_file),
                    "error": "file not found; set CHROMA_DB_PATH or QDRANT_URL",
                }
    except Exception as e:
        checks["vector_db"] = {"status": "unhealthy", "error": str(e)}

    # Providers check (enhanced with detailed LLM testing)
    providers = []
    try:
        providers_config = [
            {
                "name": "Ollama (Kamatera)",
                "env_key": "KAMATERA_LLM_API_KEY",
                "base_url": os.getenv("KAMATERA_LLM_URL", "http://66.55.77.147:8000"),
                "is_primary": True,
            },
            {
                "name": "Ollama (Local)",
                "env_key": "OLLAMA_API_KEY",
                "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                "is_primary": False,
            },
            {
                "name": "Anthropic",
                "env_key": "ANTHROPIC_API_KEY",
                "base_url": os.getenv(
                    "ANTHROPIC_BASE_URL", "https://api.anthropic.com"
                ),
                "is_primary": False,
            },
            {
                "name": "OpenAI",
                "env_key": "OPENAI_API_KEY",
                "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com"),
                "is_primary": False,
            },
            {
                "name": "Groq",
                "env_key": "GROQ_API_KEY",
                "base_url": os.getenv("GROQ_BASE_URL", "https://api.groq.com"),
                "is_primary": False,
            },
            {
                "name": "DeepSeek",
                "env_key": "DEEPSEEK_API_KEY",
                "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.ai"),
                "is_primary": False,
            },
            {
                "name": "Gemini",
                "env_key": "GEMINI_API_KEY",
                "base_url": os.getenv(
                    "GEMINI_BASE_URL", "https://generative.googleapis.com"
                ),
                "is_primary": False,
            },
        ]

        for p in providers_config:
            # Allow explicit disabling per-provider via <PROVIDER>_ENABLED env var (false/0/no -> disabled)
            enabled_override = os.getenv(
                f"{p['name'].upper().replace(' ', '_').replace('(', '').replace(')', '')}_ENABLED"
            )
            if enabled_override is not None and enabled_override.lower() in (
                "0",
                "false",
                "no",
            ):
                result = {
                    "enabled": False,
                    "is_primary": p.get("is_primary", False),
                }
                providers.append({p["name"]: result})
                continue

            key = os.getenv(p["env_key"]) if p["env_key"] else None
            result = {
                "enabled": bool(key),
                "is_primary": p.get("is_primary", False),
            }

            if key:
                try:
                    # Enhanced LLM provider health check
                    provider_health = await check_llm_provider_health(
                        p["name"].split()[0],
                        key,
                        p[
                            "base_url"
                        ],  # Extract provider name (e.g., "Ollama" from "Ollama (Kamatera)")
                    )
                    result.update(provider_health)

                    # Mark as healthy only if both connectivity and inference work
                    if provider_health.get("status") == "healthy":
                        result["status"] = "healthy"
                    elif provider_health.get("status") == "degraded":
                        result["status"] = "degraded"
                    else:
                        result["status"] = "unhealthy"

                except Exception as e:
                    result["status"] = "unhealthy"
                    result["error"] = str(e)
            else:
                result["status"] = "disabled"

            providers.append({p["name"]: result})

        checks["providers"] = providers
    except Exception as e:
        checks["providers"] = {"status": "unhealthy", "error": str(e)}

    # App-level check
    overall = "healthy"
    for k, v in checks.items():
        if isinstance(v, dict) and v.get("status") == "unhealthy":
            overall = "degraded"
        if isinstance(v, list):
            for item in v:
                # item is like {"Anthropic": {...}}
                for _, s in item.items():
                    if s.get("status") == "unreachable":
                        overall = "degraded"

    return HealthCheckResponse(status=overall, checks=checks)


# ============================================================================
# NEW ENDPOINTS FOR ENHANCED DASHBOARD
# ============================================================================


@router.get("/chroma/status", response_model=ChromaStatusResponse)
async def get_chroma_status():
    """Get detailed Chroma vector database status"""
    try:
        chroma_path = os.getenv("CHROMA_DB_PATH")
        if not chroma_path:
            chroma_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "chroma_db", "chroma.sqlite3"
            )

        chroma_file = pathlib.Path(chroma_path).resolve()

        if chroma_file.exists():
            # Try to import chromadb and get actual collection stats
            try:
                import chromadb

                client = chromadb.PersistentClient(path=str(chroma_file.parent))
                collections = client.list_collections()
                total_docs = sum(
                    [col.count() for col in collections if hasattr(col, "count")]
                )

                return ChromaStatusResponse(
                    status="healthy",
                    collections=len(collections),
                    documents=total_docs,
                    last_check=datetime.now().isoformat(),
                )
            except ImportError:
                # Fallback if chromadb not available - just check file exists
                return ChromaStatusResponse(
                    status="healthy",
                    collections=0,
                    documents=0,
                    last_check=datetime.now().isoformat(),
                )
        else:
            return ChromaStatusResponse(
                status="down",
                collections=0,
                documents=0,
                last_check=datetime.now().isoformat(),
            )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get Chroma status: {str(e)}"
        )


@router.get("/mcp/status", response_model=MCPStatusResponse)
async def get_mcp_status():
    """Get MCP (Model Context Protocol) server status"""
    try:
        # Check for MCP server configuration
        # This is a placeholder - adjust based on your actual MCP setup
        mcp_servers = []
        active_connections = 0

        # Check for common MCP server environment variables
        if os.getenv("MCP_SERVER_URL"):
            mcp_servers.append("primary")
            active_connections += 1

        # Check if local MCP servers are running
        mcp_ports = [8765, 8766]  # Common MCP ports
        for port in mcp_ports:
            try:
                s = socket.socket()
                s.settimeout(1)
                s.connect(("localhost", port))
                s.close()
                mcp_servers.append(f"localhost:{port}")
                active_connections += 1
            except Exception:
                pass

        status = "healthy" if active_connections > 0 else "down"

        return MCPStatusResponse(
            status=status,
            servers=mcp_servers,
            active_connections=active_connections,
            last_check=datetime.now().isoformat(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get MCP status: {str(e)}"
        )


@router.get("/raptor/status", response_model=RaptorStatusResponse)
async def get_raptor_status():
    """Get RAG indexer (Raptor) status"""
    try:
        import sys
        from pathlib import Path

        # Add GoblinOS to path for raptor import
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "GoblinOS"))
        from raptor_mini import raptor

        running = bool(raptor.running) if hasattr(raptor, "running") else False
        config_file = getattr(raptor, "ini_path", "config/raptor.ini")

        status = "healthy" if running else "down"

        return RaptorStatusResponse(
            status=status,
            running=running,
            config_file=config_file,
            last_check=datetime.now().isoformat(),
        )
    except Exception:
        # If raptor can't be imported or checked, return down status
        return RaptorStatusResponse(
            status="down",
            running=False,
            config_file="unknown",
            last_check=datetime.now().isoformat(),
        )


@router.get("/sandbox/status", response_model=SandboxStatusResponse)
async def get_sandbox_status():
    """Get sandbox runner status"""
    try:
        # Check for active sandbox jobs
        active_jobs = 0
        queue_size = 0

        # Try Redis-backed task queue
        try:
            from celery_task_queue import get_task_meta
            import redis

            REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            r = redis.from_url(REDIS_URL)
            keys = r.keys("task:*")

            # Count active jobs (exclude logs and artifacts keys)
            for key in keys:
                k = key.decode("utf-8")
                if ":logs" in k or ":artifacts" in k:
                    continue
                task_id = k.split(":", 1)[1]
                meta = get_task_meta(task_id)
                if meta.get("status") in ["running", "queued"]:
                    if meta.get("status") == "running":
                        active_jobs += 1
                    elif meta.get("status") == "queued":
                        queue_size += 1
        except Exception:
            # Fall back to in-memory TASKS
            try:
                from execute_router import TASKS

                for job_id, info in TASKS.items():
                    if info.get("status") == "running":
                        active_jobs += 1
                    elif info.get("status") == "queued":
                        queue_size += 1
            except Exception:
                pass

        status = "healthy" if active_jobs >= 0 else "down"

        return SandboxStatusResponse(
            status=status,
            active_jobs=active_jobs,
            queue_size=queue_size,
            last_check=datetime.now().isoformat(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get sandbox status: {str(e)}"
        )


@router.get("/scheduler/status", response_model=SchedulerStatusResponse)
async def get_scheduler_status():
    """Get APScheduler status and job information"""
    try:
        from scheduler import get_scheduler_status

        scheduler_info = get_scheduler_status()

        return SchedulerStatusResponse(
            status=scheduler_info.get("status", "unknown"),
            jobs=scheduler_info.get("jobs", []),
            last_check=datetime.now().isoformat(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get scheduler status: {str(e)}"
        )


@router.get("/cost-tracking", response_model=CostTrackingResponse)
async def get_cost_tracking(db: Session = Depends(get_db)):
    """Get aggregated cost tracking across providers"""
    try:
        now = datetime.now()
        today_start = datetime(now.year, now.month, now.day)
        month_start = datetime(now.year, now.month, 1)

        # Query total costs from provider metrics
        total_cost_query = (
            db.query(func.sum(ProviderMetric.cost_incurred))
            .filter(ProviderMetric.cost_incurred.isnot(None))
            .scalar()
        )
        total_cost = float(total_cost_query or 0.0)

        # Today's costs
        cost_today_query = (
            db.query(func.sum(ProviderMetric.cost_incurred))
            .filter(
                ProviderMetric.cost_incurred.isnot(None),
                ProviderMetric.timestamp >= today_start,
            )
            .scalar()
        )
        cost_today = float(cost_today_query or 0.0)

        # This month's costs
        cost_month_query = (
            db.query(func.sum(ProviderMetric.cost_incurred))
            .filter(
                ProviderMetric.cost_incurred.isnot(None),
                ProviderMetric.timestamp >= month_start,
            )
            .scalar()
        )
        cost_this_month = float(cost_month_query or 0.0)

        # Cost by provider
        by_provider = {}
        providers = db.query(RoutingProvider).all()
        for provider in providers:
            provider_cost = (
                db.query(func.sum(ProviderMetric.cost_incurred))
                .filter(
                    ProviderMetric.provider_id == provider.id,
                    ProviderMetric.cost_incurred.isnot(None),
                )
                .scalar()
            )
            by_provider[provider.display_name] = float(provider_cost or 0.0)

        return CostTrackingResponse(
            total_cost=total_cost,
            cost_today=cost_today,
            cost_this_month=cost_this_month,
            by_provider=by_provider,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get cost tracking: {str(e)}"
        )


@router.get("/latency-history/{service}", response_model=LatencyHistoryResponse)
async def get_latency_history(
    service: str, hours: int = 24, db: Session = Depends(get_db)
):
    """Get latency history for a service over the specified hours"""
    try:
        cutoff_time = datetime.now() - timedelta(hours=hours)

        if service == "backend":
            # For backend, we can track API response times from provider metrics
            metrics = (
                db.query(ProviderMetric.timestamp, ProviderMetric.response_time_ms)
                .filter(
                    ProviderMetric.timestamp >= cutoff_time,
                    ProviderMetric.response_time_ms.isnot(None),
                )
                .order_by(ProviderMetric.timestamp)
                .limit(100)  # Limit to last 100 data points
                .all()
            )

            timestamps = [m[0].isoformat() for m in metrics]
            latencies = [float(m[1]) for m in metrics]

        elif service == "chroma":
            # Placeholder for chroma latency - could track query times
            timestamps = []
            latencies = []

        else:
            # For other services, return empty for now
            timestamps = []
            latencies = []

        return LatencyHistoryResponse(timestamps=timestamps, latencies=latencies)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get latency history: {str(e)}"
        )


@router.get("/service-errors/{service}", response_model=List[ServiceError])
async def get_service_errors(service: str, limit: int = 10):
    """Get recent errors for a specific service"""
    try:
        errors = []

        # Check service-specific log files or error tracking
        # This is a placeholder implementation
        # You would integrate with your actual logging system

        if service == "backend":
            log_file = os.path.join(os.path.dirname(__file__), "logs", "app.log")
        elif service == "chroma":
            log_file = os.path.join(os.path.dirname(__file__), "logs", "chroma.log")
        elif service == "raptor":
            log_file = os.path.join(os.path.dirname(__file__), "logs", "raptor.log")
        else:
            log_file = None

        if log_file and os.path.exists(log_file):
            # Read last N lines that contain "error" or "ERROR"
            with open(log_file, "r") as f:
                lines = f.readlines()
                error_lines = [line for line in lines if "error" in line.lower()][
                    -limit:
                ]

                for line in error_lines:
                    # Parse timestamp and message (basic implementation)
                    errors.append(
                        ServiceError(
                            timestamp=datetime.now().isoformat(),
                            message=line.strip(),
                            service=service,
                        )
                    )

        return errors
    except Exception:
        # Return empty list on error rather than failing
        return []


@router.post("/retest/{service}", response_model=RetestServiceResponse)
async def retest_service(service: str, db: Session = Depends(get_db)):
    """Trigger a health retest for a specific service"""
    try:
        start_time = datetime.now()

        if service == "backend":
            # Test basic health endpoint
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get("http://localhost:8000/health")
                    success = response.status_code == 200
            except Exception:
                success = False

        elif service == "chroma":
            # Test Chroma database connection
            try:
                chroma_response = await get_chroma_status()
                success = chroma_response.status == "healthy"
            except Exception:
                success = False

        elif service == "mcp":
            # Test MCP servers
            try:
                mcp_response = await get_mcp_status()
                success = mcp_response.status == "healthy"
            except Exception:
                success = False

        elif service == "raptor":
            # Test Raptor status
            try:
                raptor_response = await get_raptor_status()
                success = raptor_response.status == "healthy"
            except Exception:
                success = False

        elif service == "sandbox":
            # Test Sandbox status
            try:
                sandbox_response = await get_sandbox_status()
                success = sandbox_response.status == "healthy"
            except Exception:
                success = False

        else:
            raise HTTPException(status_code=400, detail=f"Unknown service: {service}")

        end_time = datetime.now()
        latency = (end_time - start_time).total_seconds() * 1000  # Convert to ms

        message = f"{service.capitalize()} is {'healthy' if success else 'unhealthy'}"

        return RetestServiceResponse(success=success, latency=latency, message=message)
    except Exception as e:
        return RetestServiceResponse(
            success=False, latency=None, message=f"Retest failed: {str(e)}"
        )
