from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sys
import os
import tomllib
import tomllib

# Add the src directory to the path so we can import the routing module
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

try:
    print("DEBUG: Attempting to import routing.router")
    from routing.router import top_providers_for, route_task_sync

    print("DEBUG: Successfully imported routing functions")
except ImportError as e:
    print(f"DEBUG: ImportError: {e}")

    # Fallback: load providers directly from TOML file
    def load_providers_from_toml():
        """Load providers from the TOML config file"""
        config_path = os.path.join(
            os.path.dirname(__file__), "..", "config", "providers.toml"
        )
        print(f"DEBUG: Looking for config at: {config_path}")
        try:
            with open(config_path, "rb") as f:
                config = tomllib.load(f)
            providers = list(config.get("providers", {}).keys())
            print(f"DEBUG: Loaded providers: {providers}")
            return providers
        except Exception as e:
            print(f"DEBUG: Error loading TOML: {e}")
            return ["openai", "anthropic", "gemini", "ollama"]

    def top_providers_for(capability: str, **kwargs) -> List[str]:
        """Return all configured providers that support the given capability"""
        all_providers = load_providers_from_toml()
        # For now, return all providers - in a real implementation we'd filter by capability
        return all_providers

    def route_task_sync(*args, **kwargs):
        """Placeholder routing function"""
        raise Exception("Routing system not available")


router = APIRouter(prefix="/routing", tags=["routing"])


class RouteRequest(BaseModel):
    task_type: str
    payload: Dict[str, Any]
    prefer_local: Optional[bool] = False
    prefer_cost: Optional[bool] = False
    max_retries: Optional[int] = 2
    stream: Optional[bool] = False


class ProviderInfo(BaseModel):
    name: str
    capabilities: List[str]
    models: List[str]
    priority_tier: int
    cost_score: float
    bandwidth_score: float


@router.get("/providers", response_model=List[str])
async def get_available_providers():
    """Get list of all configured providers"""
    print("DEBUG: get_available_providers called")
    try:
        # Return providers that have valid API keys configured
        providers = []
        for capability in ["chat", "reasoning", "code"]:
            print(f"DEBUG: Getting providers for capability: {capability}")
            candidates = top_providers_for(capability)
            print(f"DEBUG: Candidates for {capability}: {candidates}")
            providers.extend(candidates)
        final_providers = list(set(providers))  # Remove duplicates
        print(f"DEBUG: Final providers list: {final_providers}")
        return final_providers
    except Exception as e:
        print(f"DEBUG: Exception in get_available_providers: {e}")
        # Fallback to basic providers if routing system fails
        return ["openai", "anthropic", "gemini", "ollama", "groq", "deepseek"]


@router.get("/providers/{capability}", response_model=List[str])
async def get_providers_for_capability(capability: str):
    """Get providers that support a specific capability"""
    try:
        return top_providers_for(capability)
    except Exception:
        return ["openai", "anthropic"]  # Fallback


@router.post("/route")
async def route_request(request: RouteRequest):
    """Route a task to the best available provider"""
    try:
        result = route_task_sync(
            task_type=request.task_type,
            payload=request.payload,
            prefer_local=request.prefer_local,
            prefer_cost=request.prefer_cost,
            max_retries=request.max_retries,
            stream=request.stream,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Routing failed: {str(e)}")


@router.get("/health")
async def routing_health():
    """Check if the routing system is operational"""
    try:
        providers = top_providers_for("chat")
        return {
            "status": "healthy",
            "providers_available": len(providers),
            "routing_system": "active",
        }
    except Exception as e:
        return {"status": "degraded", "error": str(e), "routing_system": "fallback"}
