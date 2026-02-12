from __future__ import annotations

# Essay endpoint request/response models
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Tuple, TYPE_CHECKING
from fastapi import APIRouter, Request, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import os
import asyncio
import logging
import sys


class EssayRequest(BaseModel):
    prompt: str
    length: Optional[int] = 500
    style: Optional[str] = "academic"


class EssayResponse(BaseModel):
    essay: str
    status: str


async def _research_topic(prompt: str) -> str:
    """Research the essay topic using Tavily API."""
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    if not tavily_api_key:
        return "No research available - Tavily API key not configured."

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": tavily_api_key,
                    "query": prompt,
                    "search_depth": "advanced",
                    "include_answer": True,
                    "include_raw_content": False,
                    "max_results": 5,
                },
            )
            response.raise_for_status()
            data = response.json()

            # Extract relevant information from search results
            research_info = []
            if "answer" in data and data["answer"]:
                research_info.append(f"Summary: {data['answer']}")

            if "results" in data:
                for result in data["results"][:3]:  # Limit to top 3 results
                    title = result.get("title", "")
                    content = result.get("content", "")
                    if content:
                        research_info.append(f"{title}: {content[:300]}...")

            return (
                "\n\n".join(research_info)
                if research_info
                else "No relevant research found."
            )

    except Exception as e:
        return f"Research failed: {str(e)}"


async def _generate_essay_with_llm(
    prompt: str, length: int, style: str, research_data: str
) -> str:
    """Generate essay using OpenAI directly."""
    try:
        from openai import OpenAI

        # Get API key from environment
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            return f"Essay generation failed: OpenAI API key not configured. Research data: {research_data[:500]}..."

        client = OpenAI(api_key=openai_api_key)

        # Construct the essay generation prompt
        system_prompt = f"""You are an expert essay writer. Write a {style} essay on the following topic.
        Use the provided research information to support your arguments.
        Aim for approximately {length} words.
        Structure the essay with an introduction, body paragraphs, and conclusion.
        Use proper {style} language and formatting."""

        user_prompt = f"""Topic: {prompt}

Research Information:
{research_data}

Please write a complete {style} essay on this topic using the research provided."""

        # Make the LLM call
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using cost-efficient model
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=length * 4,  # Rough estimate: 4 tokens per word
            temperature=0.7,
        )

        essay_content = response.choices[0].message.content.strip()

        # Add word count and style info
        word_count = len(essay_content.split())
        return f"**{style.title()} Essay** ({word_count} words)\n\n{essay_content}"

    except Exception as e:
        return f"Essay generation failed: {str(e)}. Research data: {research_data[:500]}..."


essay_router = APIRouter()


@essay_router.post("/essay", response_model=EssayResponse)
async def generate_essay(request: Request, essay_req: EssayRequest):
    """
    Generate an essay based on the provided prompt, length, and style.
    Uses Tavily for research and LLM for generation.
    Returns essay text and status.
    """
    try:
        prompt = essay_req.prompt
        length = essay_req.length or 500
        style = essay_req.style or "academic"

        # Step 1: Research the topic using Tavily
        research_data = await _research_topic(prompt)

        # Step 2: Generate essay using LLM
        essay = await _generate_essay_with_llm(prompt, length, style, research_data)

        return EssayResponse(essay=essay, status="success")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Essay generation failed: {str(e)}"
        )


def register_essay_endpoint(app):
    app.include_router(essay_router)


"""
Chat API endpoint with intelligent routing to local and cloud LLMs.
Uses the routing service to select the best model based on request characteristics.
"""

# Type-only imports for static analysis
if TYPE_CHECKING:
    from backend.database import get_db
    from backend.config import settings
    from backend.services.token_accounting import TokenAccountingService
    from backend.services.latency_monitoring_service import LatencyMonitoringService
    from backend.gateway_service import (
        get_gateway_service,
        TokenBudgetExceeded,
        MaxTokensExceeded,
    )
    from backend.errors import (
        raise_validation_error,
        raise_internal_error,
        raise_service_unavailable,
        raise_problem,
    )
    from backend.auth.policies import AuthScope
    from backend.auth_service import get_auth_service
    from backend.services import (
        request_validation,
        response_builder,
        provider_factory,
        rag_processor,
        scaling_processor,
        verification_processor,
        config_processor,
        utils,
        chat_controller,
    )
    from backend.services.routing_compat import (
        get_routing_service_compat as get_routing_service,
    )
    from backend.services.routing import RoutingService
else:
    # Runtime imports with fallback for different execution contexts
    try:
        from .database import get_db
        from .config import settings
        from .services.token_accounting import TokenAccountingService
        from .services.latency_monitoring_service import LatencyMonitoringService
        from .gateway_service import (
            get_gateway_service,
            TokenBudgetExceeded,
            MaxTokensExceeded,
        )
        from .errors import (
            raise_validation_error,
            raise_internal_error,
            raise_service_unavailable,
            raise_problem,
        )
        from .auth.policies import AuthScope
        from .auth_service import get_auth_service
        from .services import (
            request_validation,
            response_builder,
            provider_factory,
            rag_processor,
            scaling_processor,
            verification_processor,
            config_processor,
            utils,
            chat_controller,
        )
        from services.routing_compat import (
            get_routing_service_compat as get_routing_service,
        )
    except ImportError:  # pragma: no cover - support direct module imports in tests
        from database import get_db
        from config import settings
        from services.token_accounting import TokenAccountingService
        from services.latency_monitoring_service import LatencyMonitoringService
        from backend.gateway_service import (
            get_gateway_service,
            TokenBudgetExceeded,
            MaxTokensExceeded,
        )
        from errors import (
            raise_validation_error,
            raise_internal_error,
            raise_service_unavailable,
            raise_problem,
        )
        from auth.policies import AuthScope
        from backend.auth_service import get_auth_service
        from services import (
            request_validation,
            response_builder,
            provider_factory,
            rag_processor,
            scaling_processor,
            verification_processor,
            config_processor,
            utils,
        )

        try:
            from services.routing_compat import (
                get_routing_service_compat as get_routing_service,
            )
        except ImportError:
            try:
                from .services.routing_compat import (
                    get_routing_service_compat as get_routing_service,
                )
            except ImportError:
                # Last resort for test environments
                if "services" not in sys.modules:
                    sys.path.append(os.path.join(os.path.dirname(__file__), "services"))
                from routing_compat import (
                    get_routing_service_compat as get_routing_service,
                )

    # Runtime fallback for RoutingService type
    RoutingService = Any  # type: ignore[misc,assignment]

logger = logging.getLogger(__name__)

# Re-export get_routing_encryption_key for backward compatibility with tests
get_routing_encryption_key = config_processor.get_routing_encryption_key

# Security schemes
security = HTTPBearer()
token_accountant = TokenAccountingService()

# Initialize latency monitoring service
latency_monitor = LatencyMonitoringService()

router = APIRouter(prefix="/chat", tags=["chat"])

# During pytest import-time the FastAPI router will attempt to introspect
# dependencies which can pull in heavy or application-only types (DB
# sessions, ML libs). Make decorators no-ops when running under pytest so
# unit tests can import handler functions directly without registering
# routes.
# os and sys already imported at top of file

if ("PYTEST_CURRENT_TEST" in os.environ) or ("pytest" in sys.modules):

    class _NoopRouter:
        """No-op router for test environments."""

        @staticmethod
        def _noop_decorator(*_args, **_kwargs):
            def _decor(f):
                return f

            return _decor

        post = _noop_decorator
        get = _noop_decorator
        put = _noop_decorator
        delete = _noop_decorator

    router = _NoopRouter()


def require_scope(required_scope: AuthScope):
    """Dependency to require a specific scope."""

    def scope_checker(
        credentials: HTTPAuthorizationCredentials = Security(security),
    ) -> List[str]:
        auth_service = get_auth_service()

        # Try JWT token first
        token = credentials.credentials
        claims = auth_service.validate_access_token(token)

        if claims:
            # Convert AuthScope enums back to strings
            scopes = auth_service.get_user_scopes(claims)
            scope_values = [scope.value for scope in scopes]

            if required_scope.value not in scope_values:
                raise HTTPException(
                    status_code=403,
                    detail=f"Insufficient permissions. Required scope: {required_scope.value}",
                )
            return scope_values

        raise HTTPException(status_code=401, detail="Invalid authentication")

    return scope_checker


# Import the request validation service
ChatCompletionRequest = request_validation.ChatCompletionRequest
ChatCompletionResponse = response_builder.ChatCompletionResponse
# Backwards-compatible exports expected by older tests and callers
# (tests import these directly from `chat_router`). Keep as thin wrappers
# that delegate to the validation service so behavior is unchanged.
ChatMessage = request_validation.ChatMessage


def validate_chat_request(request: ChatCompletionRequest) -> None:
    """Backward-compatible wrapper used by legacy callers and tests."""
    return request_validation.validate_chat_request(request)


async def _check_gateway_and_prepare(
    request: ChatCompletionRequest,
    gateway_service,
) -> Tuple[List[Dict], Any]:
    """
    Validate request, prepare messages, and run gateway checks.

    Returns:
        Tuple of (prepared_messages, gateway_result)
    """
    # Validate request using the validation service
    request_validation.validate_chat_request(request)
    messages = config_processor.prepare_messages(request)

    # Run gateway checks
    gateway_result = await gateway_service.process_request(
        messages=messages,
        max_tokens=request.max_tokens,
        context=request.context,
    )

    # Be defensive: tests may inject MagicMocks (no `.value` or numeric types),
    # so coerce/format safely to avoid raising during logging.
    try:
        intent_val = getattr(
            getattr(gateway_result, "intent", None), "value", gateway_result.intent
        )
    except Exception:
        intent_val = str(getattr(gateway_result, "intent", None))

    estimated_tokens = getattr(gateway_result, "estimated_tokens", None)
    risk_score = getattr(gateway_result, "risk_score", None)
    allowed = getattr(gateway_result, "allowed", None)

    risk_str = (
        f"{risk_score:.2f}" if isinstance(risk_score, (int, float)) else str(risk_score)
    )
    est_tokens_str = str(estimated_tokens)

    logger.info(
        "Gateway analysis: intent=%s, estimated_tokens=%s, risk_score=%s, allowed=%s",
        intent_val,
        est_tokens_str,
        risk_str,
        allowed,
    )

    if not gateway_result.allowed:
        raise HTTPException(
            status_code=400,
            detail="Request flagged as high-risk. Please reduce token limits or simplify request.",
        )

    return messages, gateway_result


async def create_chat_completion(
    request: ChatCompletionRequest,
    req: Request,
    service: "RoutingService" = Depends(get_routing_service),
    scopes: List[str] = Depends(require_scope(AuthScope.WRITE_CONVERSATIONS)),
):
    """
    Create a chat completion with intelligent routing to the best model.

    This endpoint automatically selects the optimal local or cloud LLM based on:
    - Intent (code-gen, creative, rag, chat, classification, etc.)
    - Context length (short vs long documents)
    - Latency requirements (ultra-low, low, medium, high)
    - Cost priority (optimize for cost vs quality)

    Examples (abridged):
      - Code gen, quick status, long-document RAG, conversational chat.

    Note: route registration is deferred at import-time in tests to avoid
    FastAPI trying to introspect application-only dependency types.
    """

    gateway_service = get_gateway_service()
    gateway_result = None

    try:
        controller = chat_controller.ChatController()
        orchestration_result = await controller.orchestrate_completion(
            request, req, service, gateway_service
        )

        # Check if orchestration failed
        if not orchestration_result.get("success", True):
            routing_result = orchestration_result.get("routing_result", {})
            error_msg = orchestration_result.get("error", "Unknown error")

            if "Rate limit exceeded" in error_msg:
                fallback_level = routing_result.get("fallback_level", "deny")
                retry_after = routing_result.get("retry_after")

                if fallback_level == "deny":
                    raise HTTPException(
                        status_code=429,
                        detail="Rate limit exceeded. Please try again later.",
                        headers={
                            "Retry-After": str(int(retry_after))
                            if retry_after
                            else "60"
                        },
                    )
                if fallback_level == "cheap_model":
                    logger.warning(
                        f"Rate limited request {routing_result.get('request_id')} using cheap fallback"
                    )

            # Custom error for creative/essay requests
            if request.messages and any(
                "essay" in m.content.lower() or "creative" in m.content.lower()
                for m in request.messages
            ):
                raise HTTPException(
                    status_code=503,
                    detail="Essay generation failed. Please try again or rephrase your request.",
                )

            raise_service_unavailable(f"No suitable provider available: {error_msg}")

        # Check for emergency mode
        routing_result = orchestration_result.get("routing_result", {})
        if routing_result.get("emergency_mode"):
            logger.warning(
                f"Request {routing_result.get('request_id')} served in emergency mode"
            )

        # Record token usage for successful requests
        gateway_result = orchestration_result.get("gateway_result")
        if orchestration_result.get("tokens_used", 0) > 0 and gateway_result:
            try:
                await gateway_service.record_usage(
                    None,
                    orchestration_result["tokens_used"],
                    intent=gateway_result.intent,
                    success=orchestration_result.get("success", True),
                )
            except Exception as e:
                logger.warning(f"Failed to record token usage: {e}")

        return ChatCompletionResponse(**orchestration_result)

    except Exception as e:
        if gateway_result:
            try:
                await gateway_service.record_usage(
                    None,
                    0,
                    intent=gateway_result.intent,
                    success=False,
                    error_type=type(e).__name__,
                )
            except Exception as record_error:
                logger.warning(
                    f"Failed to record failed request anomaly: {record_error}"
                )

        logger.error(
            f"Chat completion failed: {e}",
            exc_info=True,
            extra={
                "correlation_id": getattr(req.state, "correlation_id", None),
                "request_id": getattr(req.state, "request_id", None),
            },
        )
        raise_internal_error(f"Chat completion failed: {str(e)}")


# Register the route only when not running under pytest — keep import-time
# behavior harmless for unit tests so the module can be imported during
# collection without FastAPI introspection of app-only types.
# os and sys already imported at top of file

if ("PYTEST_CURRENT_TEST" not in os.environ) and ("pytest" not in sys.modules):
    router.post("/completions", response_model=None)(create_chat_completion)


@router.get("/models")
async def list_available_models(
    req: Request,
    service: "RoutingService" = Depends(get_routing_service),
):
    """
    List all available models across all providers.
    Includes routing recommendations for each model.
    """
    try:
        providers = await service.discover_providers()

        models = []
        for provider in providers:
            for model in provider["models"]:
                models.append(
                    {
                        "id": model["id"],
                        "provider": provider["display_name"],
                        "provider_name": provider["name"],
                        "capabilities": model.get("capabilities", []),
                        "context_window": model.get("context_window", 0),
                        "pricing": model.get("pricing", {}),
                    }
                )

        # Add routing recommendations
        routing_recommendations = {
            "gemma:2b": "Ultra-fast responses, classification, status checks",
            "phi3:3.8b": "Low-latency chat, conversational UI",
            "qwen2.5:3b": "Long context (32K), multilingual, RAG",
            "mistral:7b": "High quality, code generation, creative writing",
        }

        for model in models:
            model["routing_recommendation"] = routing_recommendations.get(
                model["id"], "General purpose"
            )

        return {
            "models": models,
            "total_count": len(models),
            "routing_info": {
                "automatic": True,
                "factors": [
                    "intent",
                    "context_length",
                    "latency_target",
                    "cost_priority",
                ],
                "documentation": "/docs/LOCAL_LLM_ROUTING.md",
            },
        }

    except Exception as e:
        logger.error(
            f"Failed to list models: {e}",
            extra={
                "correlation_id": getattr(req.state, "correlation_id", None),
                "request_id": getattr(req.state, "request_id", None),
            },
        )
        raise_internal_error(f"Failed to list models: {str(e)}")


@router.get("/routing-info")
async def get_routing_info():
    """
    Get information about the intelligent routing system.
    """
    return {
        "routing_system": "intelligent",
        "version": "1.0",
        "factors": {
            "intent": {
                "description": "Detected or explicit intent (code-gen, creative, rag, chat, etc.)",
                "options": [
                    "code-gen",
                    "creative",
                    "explain",
                    "summarize",
                    "rag",
                    "retrieval",
                    "chat",
                    "classification",
                    "status",
                    "translation",
                ],
                "auto_detect": True,
            },
            "latency_target": {
                "description": "Target latency for response",
                "options": ["ultra_low", "low", "medium", "high"],
                "default": "medium",
            },
            "context_length": {
                "description": "Length of the conversation context",
                "thresholds": {
                    "short": "< 2000 tokens",
                    "medium": "2000-8000 tokens",
                    "long": "> 8000 tokens (uses qwen2.5:3b with 32K window)",
                },
            },
            "cost_priority": {
                "description": "Prioritize cost over quality",
                "default": False,
                "effect": "Routes to smaller, faster models when enabled",
            },
        },
        "models": {
            "gemma:2b": {
                "size": "1.7GB",
                "context": "8K tokens",
                "latency": "5-8s",
                "best_for": ["ultra_fast", "classification", "status_checks"],
                "params": {"temperature": 0.0, "max_tokens": 40},
            },
            "phi3:3.8b": {
                "size": "2.2GB",
                "context": "4K tokens",
                "latency": "10-12s",
                "best_for": ["low_latency_chat", "conversational_ui", "quick_qa"],
                "params": {"temperature": 0.15, "max_tokens": 128},
            },
            "qwen2.5:3b": {
                "size": "1.9GB",
                "context": "32K tokens",
                "latency": "14s",
                "best_for": [
                    "long_context",
                    "multilingual",
                    "rag",
                    "document_retrieval",
                ],
                "params": {"temperature": 0.0, "max_tokens": 1024},
            },
            "mistral:7b": {
                "size": "4.4GB",
                "context": "8K tokens",
                "latency": "14-15s",
                "best_for": [
                    "high_quality",
                    "code_generation",
                    "creative_writing",
                    "explanations",
                ],
                "params": {"temperature": 0.2, "max_tokens": 512},
            },
        },
        "cost": {
            "per_request": "$0 (self-hosted)",
            "monthly_infrastructure": "$15-20",
            "savings_vs_cloud": "86-92% ($110-240/month)",
        },
    }
