from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import httpx
import socket
import pathlib
from typing import Dict, Any
import urllib.parse
import socket

router = APIRouter(prefix="/health", tags=["health"])


class HealthCheckResponse(BaseModel):
    status: str
    checks: Dict[str, Any]


@router.get("/all", response_model=HealthCheckResponse)
async def health_all():
    """Perform full health checks: database, vector DB, and providers"""
    checks: Dict[str, Any] = {}

    # DB check (Supabase / Postgres)
    db_url = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_URL")
    if db_url:
        try:
            # Simple TCP connect test for DB host:port
            # Accept URL formats: postgres://user:pass@host:port/db
            host = None
            port = None
            if db_url.startswith("postgres") or db_url.startswith("postgresql"):
                # parse host and port
                import re

                m = re.search(r"@([\w\-\.]+)(?::(\d+))?", db_url)
                if m:
                    host = m.group(1)
                    port = int(m.group(2)) if m.group(2) else 5432
            else:
                # If SUPABASE_URL is given (https), try TCP connect to its host/443
                import urllib.parse

                parsed = urllib.parse.urlparse(db_url)
                host = parsed.hostname
                port = parsed.port or (443 if parsed.scheme == "https" else 80)

            if host:
                s = socket.socket()
                s.settimeout(2)
                s.connect((host, port))
                s.close()
                checks["database"] = {"status": "healthy", "host": host, "port": port}
            else:
                checks["database"] = {"status": "skipped", "reason": "Could not parse database URL"}
        except Exception as e:
            checks["database"] = {"status": "unhealthy", "error": str(e)}
    else:
        checks["database"] = {"status": "skipped", "reason": "DATABASE_URL or SUPABASE_URL not set"}

    # Vector DB check (Chroma sqlite file or connection)
    try:
        chroma_path = os.getenv("CHROMA_DB_PATH")
        if not chroma_path:
            # default path in repo
            chroma_path = os.path.join(os.path.dirname(__file__), "..", "..", "chroma_db", "chroma.sqlite3")
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
                    checks["vector_db"] = {"status": "healthy", "host": host, "port": port, "url": qdrant_url}
                except Exception as e:
                    checks["vector_db"] = {"status": "unhealthy", "url": qdrant_url, "error": str(e)}
            else:
                checks["vector_db"] = {"status": "unhealthy", "path": str(chroma_file), "error": "file not found; set CHROMA_DB_PATH or QDRANT_URL"}
    except Exception as e:
        checks["vector_db"] = {"status": "unhealthy", "error": str(e)}

    # Providers check (basic connectivity)
    providers = []
    try:
        providers_config = [
            {"name": "Anthropic", "env_key": "ANTHROPIC_API_KEY", "base_url": os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")},
            {"name": "OpenAI", "env_key": "OPENAI_API_KEY", "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com")},
            {"name": "Groq", "env_key": "GROQ_API_KEY", "base_url": os.getenv("GROQ_BASE_URL", "https://api.groq.com")},
            {"name": "DeepSeek", "env_key": "DEEPSEEK_API_KEY", "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.ai")},
            {"name": "Gemini", "env_key": "GEMINI_API_KEY", "base_url": os.getenv("GEMINI_BASE_URL", "https://generative.googleapis.com")},
        ]

        async with httpx.AsyncClient(timeout=3) as client:
            for p in providers_config:
                # Allow explicit disabling per-provider via <PROVIDER>_ENABLED env var (false/0/no -> disabled)
                enabled_override = os.getenv(f"{p['name'].upper()}_ENABLED")
                if enabled_override is not None and enabled_override.lower() in ("0", "false", "no"):
                    result = {"enabled": False}
                    providers.append({p["name"]: result})
                    continue

                key = os.getenv(p["env_key"]) if p["env_key"] else None
                result = {"enabled": bool(key)}
                if key:
                    try:
                        # Try DNS resolution first
                        parsed = urllib.parse.urlparse(p["base_url"])
                        dns_host = parsed.hostname
                        try:
                            socket.getaddrinfo(dns_host, 0)
                        except Exception as de:
                            raise Exception(f"DNS lookup failed for {dns_host}: {de}")
                        # Try a lightweight request to the base_url
                        r = await client.get(p["base_url"], timeout=3)
                        result["status_code"] = r.status_code
                        result["status"] = "reachable" if r.status_code < 400 else "unreachable"
                    except Exception as e:
                        result["status"] = "unreachable"
                        result["error"] = str(e)
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
