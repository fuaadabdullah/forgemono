"""
Chat API endpoint with intelligent routing to local and cloud LLMs.
Uses the routing service to select the best model based on request characteristics.
"""

from fastapi import APIRouter, Depends, Request, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import logging
import os

from database import get_db
from config import settings
from services.routing import RoutingService
from services.output_verification import VerificationPipeline
from services.rag_service import RAGService
from services.inference_scaling_service import InferenceScalingService
from services.latency_monitoring_service import LatencyMonitoringService
from gateway_service import get_gateway_service, TokenBudgetExceeded, MaxTokensExceeded
from providers import (
    OllamaAdapter,
    GrokAdapter,
    OpenAIAdapter,
    AnthropicAdapter,
    DeepSeekAdapter,
)
from errors import (
    raise_validation_error,
    raise_internal_error,
    raise_service_unavailable,
    raise_problem,
)
from auth.policies import AuthScope
from auth_service import get_auth_service

logger = logging.getLogger(__name__)

# Security schemes
security = HTTPBearer()


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


# Simple token counting approximation (rough estimate: ~4 chars per token)
def estimate_tokens(text: str) -> int:
    """Estimate token count for text. Rough approximation: ~4 characters per token."""
    if not text:
        return 0
    # More accurate approximation: count words and adjust for punctuation/subwords
    words = len(text.split())
    # Adjust for average subword tokenization (roughly 1.3 tokens per word)
    return max(1, int(words * 1.3))


# Get encryption key from environment
ROUTING_ENCRYPTION_KEY = os.getenv("ROUTING_ENCRYPTION_KEY")
if not ROUTING_ENCRYPTION_KEY:
    raise ValueError(
        "ROUTING_ENCRYPTION_KEY environment variable must be set for chat routing functionality"
    )

# Initialize latency monitoring service
latency_monitor = LatencyMonitoringService()

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatMessage(BaseModel):
    role: str = Field(
        ..., description="Role of the message sender (user, assistant, system)"
    )
    content: str = Field(..., description="Content of the message")


class ChatCompletionRequest(BaseModel):
    messages: List[ChatMessage] = Field(
        ..., description="List of messages in the conversation"
    )
    model: Optional[str] = Field(
        None,
        description="Specific model to use (optional, auto-routed if not provided)",
    )
    intent: Optional[str] = Field(
        None, description="Explicit intent (code-gen, creative, rag, chat, etc.)"
    )
    latency_target: Optional[str] = Field(
        "medium", description="Latency requirement (ultra_low, low, medium, high)"
    )
    context: Optional[str] = Field(
        None, description="Additional context for RAG/retrieval"
    )
    cost_priority: Optional[bool] = Field(
        False, description="Prioritize cost over quality"
    )
    stream: Optional[bool] = Field(False, description="Stream the response")
    temperature: Optional[float] = Field(None, description="Override temperature")
    max_tokens: Optional[int] = Field(None, description="Override max tokens")
    top_p: Optional[float] = Field(None, description="Override top_p")
    enable_verification: Optional[bool] = Field(
        True, description="Enable output safety verification (default: True)"
    )
    enable_confidence_scoring: Optional[bool] = Field(
        True, description="Enable confidence scoring and escalation (default: True)"
    )
    auto_escalate: Optional[bool] = Field(
        True,
        description="Automatically escalate to better model if confidence is low (default: True)",
    )
    sla_target_ms: Optional[float] = Field(
        None, description="SLA target response time in milliseconds"
    )
    cost_budget: Optional[float] = Field(
        None, description="Maximum cost per request in USD"
    )


class ChatCompletionResponse(BaseModel):
    id: str
    model: str
    provider: str
    intent: Optional[str] = None
    routing_explanation: Optional[str] = None
    verification_result: Optional[Dict[str, Any]] = None
    confidence_result: Optional[Dict[str, Any]] = None
    rag_context: Optional[Dict[str, Any]] = None
    inference_scaling: Optional[Dict[str, Any]] = None
    escalated: Optional[bool] = False
    original_model: Optional[str] = None
    choices: List[Dict[str, Any]]
    usage: Optional[Dict[str, int]] = None
    metadata: Optional[Dict[str, Any]] = None


def validate_chat_request(request: ChatCompletionRequest):
    """Validate chat completion request parameters."""
    errors = {}

    # Validate messages
    if not request.messages:
        errors["messages"] = ["At least one message is required"]

    if len(request.messages) > 50:
        errors["messages"] = ["Maximum 50 messages allowed"]

    total_content_length = 0
    for i, msg in enumerate(request.messages):
        if not msg.content or not msg.content.strip():
            errors.setdefault("messages", []).append(
                f"Message {i}: content cannot be empty"
            )

        if len(msg.content) > 10000:  # 10KB per message
            errors.setdefault("messages", []).append(
                f"Message {i}: content too long (max 10KB)"
            )

        total_content_length += len(msg.content)

    if total_content_length > 50000:  # 50KB total
        errors["messages"] = ["Total message content too long (max 50KB)"]

    # Validate temperature
    if request.temperature is not None and (
        request.temperature < 0 or request.temperature > 2
    ):
        errors["temperature"] = ["Must be between 0 and 2"]

    # Validate max_tokens
    if request.max_tokens is not None and (
        request.max_tokens < 1 or request.max_tokens > 4096
    ):
        errors["max_tokens"] = ["Must be between 1 and 4096"]

    # Validate top_p
    if request.top_p is not None and (request.top_p < 0 or request.top_p > 1):
        errors["top_p"] = ["Must be between 0 and 1"]

    if errors:
        raise_validation_error("Request validation failed", errors=errors)


def should_use_scaling(
    request: ChatCompletionRequest, messages: List[Dict[str, str]]
) -> bool:
    """
    Determine if inference-time scaling should be used for this request.

    Uses scaling for complex queries that are likely to benefit from multiple
    candidate generation and PRM-based selection to reduce hallucinations.
    """
    # Always use scaling for explicit complex intents
    if request.intent in ["explain", "analyze", "solve", "reason"]:
        return True

    # Use scaling for long queries (>200 words) that might be complex
    user_query = messages[-1]["content"] if messages else ""
    word_count = len(user_query.split())

    if word_count > 200:
        return True

    # Use scaling for queries with complex keywords (but avoid false positives)
    complex_keywords = [
        "explain",
        "analyze",
        "why",
        "solve",
        "reason",
        "compare",
        "evaluate",
        "design",
        "implement",
        "optimize",
        "troubleshoot",
        "debug",
        "architecture",
        "system",
        "complex",
        "difficult",
        "algorithm",
        "theory",
        "mathematical",
        "scientific",
    ]

    query_lower = user_query.lower()

    # Check for complex keywords, but require minimum length to avoid greetings
    has_complex_keyword = any(keyword in query_lower for keyword in complex_keywords)
    if has_complex_keyword and len(user_query.split()) > 3:
        return True

    # Use scaling for multi-part questions (containing ?, and, or)
    if "?" in user_query and (" and " in query_lower or " or " in query_lower):
        return True

    return False


def get_routing_service(db: Session = Depends(get_db)) -> RoutingService:
    """Dependency to get routing service instance."""
    return RoutingService(db, ROUTING_ENCRYPTION_KEY)


@router.post("/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(
    request: ChatCompletionRequest,
    req: Request,
    service: RoutingService = Depends(get_routing_service),
    scopes: List[str] = Depends(require_scope(AuthScope.WRITE_CONVERSATIONS)),
):
    """
    Create a chat completion with intelligent routing to the best model.

    This endpoint automatically selects the optimal local or cloud LLM based on:
    - Intent (code-gen, creative, rag, chat, classification, etc.)
    - Context length (short vs long documents)
    - Latency requirements (ultra-low, low, medium, high)
    - Cost priority (optimize for cost vs quality)

    Examples:

    1. Code Generation (routes to mistral:7b):
       {
         "messages": [{"role": "user", "content": "Write a Python function to sort a list"}]
       }

    2. Quick Status Check (routes to gemma:2b):
       {
         "messages": [{"role": "user", "content": "What's the status?"}],
         "latency_target": "ultra_low"
       }

    3. Long Document RAG (routes to qwen2.5:3b):
       {
         "messages": [{"role": "user", "content": "Summarize the key points"}],
         "context": "<long document>",
         "intent": "rag"
       }

    4. Conversational Chat (routes to phi3:3.8b):
       {
         "messages": [
           {"role": "user", "content": "Hi!"},
           {"role": "assistant", "content": "Hello!"},
           {"role": "user", "content": "Can you help me?"}
         ],
         "latency_target": "low"
       }
    """
    try:
        # Validate request parameters
        validate_chat_request(request)

        # Convert messages to dict format
        messages = [
            {"role": msg.role, "content": msg.content} for msg in request.messages
        ]

        # Gateway-level protections and classification
        gateway_service = get_gateway_service()
        gateway_result = None
        try:
            gateway_result = await gateway_service.process_request(
                messages=messages,
                max_tokens=request.max_tokens,
                context=request.context,
            )

            # Log gateway analysis
            logger.info(
                f"Gateway analysis: intent={gateway_result.intent.value}, "
                f"estimated_tokens={gateway_result.estimated_tokens}, "
                f"risk_score={gateway_result.risk_score:.2f}, "
                f"allowed={gateway_result.allowed}"
            )

            # Check if request should be denied
            if not gateway_result.allowed:
                raise HTTPException(
                    status_code=400,
                    detail="Request flagged as high-risk. Please reduce token limits or simplify request.",
                )

        except TokenBudgetExceeded:
            raise HTTPException(
                status_code=429,
                detail="Token budget exceeded. Please try again later or contact support.",
                headers={"Retry-After": "3600"},  # 1 hour
            )
        except MaxTokensExceeded as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Build requirements for routing
        requirements = {
            "messages": messages,
            "intent": request.intent
            or gateway_result.intent.value,  # Use gateway classification if not specified
            "latency_target": request.latency_target,
            "context": request.context,
            "cost_priority": request.cost_priority,
        }

        # If model is specified, add it to requirements
        if request.model:
            requirements["model"] = request.model

        # Route the request
        # Get client IP for rate limiting
        client_ip = req.client.host if req.client else None
        request_path = req.url.path if req.url else None

        routing_result = await service.route_request(
            capability="chat",
            requirements=requirements,
            sla_target_ms=request.sla_target_ms,
            cost_budget=request.cost_budget,
            latency_priority=request.latency_target,
            client_ip=client_ip,
            user_id=getattr(req.state, "user_id", None)
            if hasattr(req, "state")
            else None,
            request_path=request_path,
        )

        # Handle autoscaling responses
        if not routing_result.get("success"):
            error_msg = routing_result.get("error", "Unknown error")

            # Check if rate limited
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
                elif fallback_level == "cheap_model":
                    # Allow but log that we're using fallback
                    logger.warning(
                        f"Rate limited request {routing_result.get('request_id')} using cheap fallback"
                    )

            raise_service_unavailable(f"No suitable provider available: {error_msg}")

        # Check if this is emergency mode
        if routing_result.get("emergency_mode"):
            logger.warning(
                f"Request {routing_result.get('request_id')} served in emergency mode"
            )

        provider_info = routing_result["provider"]
        selected_model = provider_info.get("model", request.model or "auto-selected")

        # Get recommended parameters (or use provided overrides)
        recommended_params = routing_result.get("recommended_params", {})
        temperature = (
            request.temperature
            if request.temperature is not None
            else recommended_params.get("temperature", 0.2)
        )
        max_tokens = (
            request.max_tokens
            if request.max_tokens is not None
            else recommended_params.get("max_tokens", 512)
        )
        top_p = (
            request.top_p
            if request.top_p is not None
            else recommended_params.get("top_p", 0.95)
        )

        # Get system prompt if available
        system_prompt = routing_result.get("system_prompt")
        if system_prompt and not any(msg["role"] == "system" for msg in messages):
            messages = [{"role": "system", "content": system_prompt}] + messages

        # Handle RAG requests with extended context
        rag_context = None
        if request.intent == "rag" or (request.context and len(request.context) > 1000):
            try:
                rag_service = RAGService(
                    enable_enhanced=settings.enable_enhanced_rag,
                    chroma_path=settings.rag_chroma_path,
                )
                user_query = messages[-1]["content"] if messages else ""

                # Generate session ID for caching
                session_id = f"session_{hash(user_query + str(request.context or ''))}"

                # Use enhanced RAG pipeline if enabled, otherwise use standard pipeline
                if settings.enable_enhanced_rag:
                    rag_result = await rag_service.enhanced_rag_pipeline(
                        query=user_query,
                        session_id=session_id,
                        filters={"intent": "rag"} if request.intent == "rag" else None,
                    )
                else:
                    rag_result = await rag_service.rag_pipeline(
                        query=user_query,
                        session_id=session_id,
                        filters={"intent": "rag"} if request.intent == "rag" else None,
                    )

                rag_context = rag_result

                # If RAG found relevant context, modify the prompt
                if rag_result.get("context", {}).get("chunks"):
                    # Replace the last user message with RAG-enhanced prompt
                    rag_prompt = rag_result["prompt"]
                    messages[-1] = {"role": "user", "content": rag_prompt}

                    # Increase max tokens for RAG responses (they need more context)
                    max_tokens = min(max_tokens * 2, 4096)

                    logger.info(
                        f"RAG: Retrieved {rag_result['context']['filtered_count']} chunks, {rag_result['context']['total_tokens']} tokens"
                    )

            except Exception as e:
                logger.warning(f"RAG processing failed: {e}")
                # Continue without RAG if it fails

        # Initialize the adapter for the selected provider
        # For now, we'll focus on Ollama (local LLMs)
        if provider_info["name"].lower() == "ollama":
            # Get Ollama configuration - prefer Kamatera for production
            use_local_llm = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"

            if use_local_llm:
                # Local development mode
                ollama_base_url = os.getenv(
                    "LOCAL_LLM_PROXY_URL", "http://localhost:11434"
                )
                ollama_api_key = os.getenv("LOCAL_LLM_API_KEY", "")
            else:
                # Production mode - use Kamatera-hosted LLM runtime
                ollama_base_url = os.getenv(
                    "KAMATERA_LLM_URL", "http://localhost:11434"
                )
                ollama_api_key = os.getenv("KAMATERA_LLM_API_KEY", "")

            adapter = OllamaAdapter(ollama_api_key, ollama_base_url)

            # Initialize verification pipeline if needed
            verification_pipeline = None
            if request.enable_verification or request.enable_confidence_scoring:
                verification_pipeline = VerificationPipeline(adapter)

            # Track escalation attempts
            original_model = selected_model
            escalated = False
            max_escalations = 2
            escalation_count = 0

            response_text = None
            verification_result = None
            confidence_result = None
            scaling_result = None
            response_time_ms = None  # Track response time for metadata

            # Check if we should use inference-time scaling for complex queries
            use_scaling = should_use_scaling(request, messages)

            if use_scaling:
                logger.info("Using inference-time scaling for complex query")
                scaling_service = InferenceScalingService()

                # Get the user query for scaling
                user_query = messages[-1]["content"] if messages else ""

                # Perform inference scaling
                scaling_result = await scaling_service.scale_inference(
                    query=user_query,
                    adapter=adapter,
                    model=selected_model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                if scaling_result.get("success"):
                    # Use the best chain from scaling
                    response_text = scaling_result["best_chain"]["response"]
                    logger.info(
                        f"Inference scaling successful. Best score: {scaling_result['best_chain']['score']:.2f}"
                    )
                else:
                    logger.warning(
                        "Inference scaling failed, falling back to standard generation"
                    )
                    use_scaling = False

            # If not using scaling or scaling failed, use standard generation with escalation
            if not use_scaling:
                # Attempt generation with escalation loop
                while escalation_count <= max_escalations:
                    # Make the completion request with timing
                    import time

                    start_time = time.time()

                    try:
                        response_text = await adapter.chat(
                            model=selected_model,
                            messages=messages,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            top_p=top_p,
                        )
                        success = True
                    except Exception as e:
                        success = False
                        raise e
                    finally:
                        # Record latency metrics
                        end_time = time.time()
                        response_time_ms = (end_time - start_time) * 1000
                        tokens_used = (
                            estimate_tokens(response_text) if response_text else 0
                        )

                        try:
                            await latency_monitor.record_metric(
                                provider_name="ollama",
                                model_name=selected_model,
                                response_time_ms=response_time_ms,
                                tokens_used=tokens_used,
                                success=success,
                            )
                        except Exception as e:
                            logger.warning(f"Failed to record latency metric: {e}")

                    # If verification/scoring disabled, accept immediately
                    if not (
                        request.enable_verification or request.enable_confidence_scoring
                    ):
                        break

                    # Run verification and confidence scoring
                    (
                        verification_result,
                        confidence_result,
                    ) = await verification_pipeline.verify_and_score(
                        original_prompt=messages[-1][
                            "content"
                        ],  # Get last user message
                        model_output=response_text,
                        model_used=selected_model,
                        context={
                            "intent": request.intent,
                            "latency_target": request.latency_target,
                        },
                        skip_verification=not request.enable_verification,
                    )

                    # Check if we should reject the output
                    if verification_pipeline.should_reject_output(
                        verification_result, confidence_result
                    ):
                        raise_problem(
                            status=422,
                            title="Output Rejected",
                            detail="Output rejected due to safety or quality concerns",
                            type_uri="https://api.goblin.fuaad.ai/errors/output-rejected",
                            code="OUTPUT_REJECTED",
                            errors={
                                "verification": {
                                    "is_safe": verification_result.is_safe,
                                    "safety_score": verification_result.safety_score,
                                    "issues": verification_result.issues,
                                },
                                "confidence": {
                                    "score": confidence_result.confidence_score,
                                    "reasoning": confidence_result.reasoning,
                                },
                            },
                        )

                    # Check if we should escalate
                    if request.auto_escalate and verification_pipeline.should_escalate(
                        verification_result, confidence_result, selected_model
                    ):
                        next_model = verification_pipeline.get_escalation_target(
                            selected_model
                        )

                        if next_model and escalation_count < max_escalations:
                            logger.info(
                                f"Escalating from {selected_model} to {next_model} "
                                f"(confidence: {confidence_result.confidence_score:.2f})",
                                extra={
                                    "correlation_id": getattr(
                                        req.state, "correlation_id", None
                                    ),
                                    "request_id": getattr(
                                        req.state, "request_id", None
                                    ),
                                },
                            )
                            selected_model = next_model
                            escalated = True
                            escalation_count += 1
                            continue

                    # If we get here, accept the output
                    break

            # Build response
            response_data = {
                "id": routing_result["request_id"],
                "model": selected_model,
                "provider": provider_info["display_name"],
                "intent": routing_result.get("intent"),
                "routing_explanation": routing_result.get("routing_explanation"),
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": response_text},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": routing_result.get("context_length", 0),
                    "completion_tokens": estimate_tokens(response_text),
                    "total_tokens": routing_result.get("context_length", 0)
                    + estimate_tokens(response_text),
                },
                "metadata": {
                    "response_time_ms": response_time_ms,
                    "tokens_used": tokens_used,
                    "success": success,
                },
            }

            # Add verification results if enabled
            if verification_result:
                response_data["verification_result"] = {
                    "is_safe": verification_result.is_safe,
                    "safety_score": verification_result.safety_score,
                    "issues": verification_result.issues,
                    "explanation": verification_result.explanation,
                }

            if confidence_result:
                response_data["confidence_result"] = {
                    "confidence_score": confidence_result.confidence_score,
                    "reasoning": confidence_result.reasoning,
                    "recommended_action": confidence_result.recommended_action,
                }

            if escalated:
                response_data["escalated"] = True
                response_data["original_model"] = original_model

            # Add RAG context if available
            if rag_context:
                response_data["rag_context"] = {
                    "chunks_retrieved": rag_context.get("context", {}).get(
                        "filtered_count", 0
                    ),
                    "total_tokens": rag_context.get("context", {}).get(
                        "total_tokens", 0
                    ),
                    "cached": rag_context.get("cached", False),
                    "session_id": rag_context.get("session_id"),
                }

            # Add inference scaling results if used
            if scaling_result:
                response_data["inference_scaling"] = {
                    "used": True,
                    "best_score": scaling_result["best_chain"]["score"],
                    "candidates_count": scaling_result["candidates_count"],
                    "score_distribution": scaling_result["scaling_info"][
                        "score_distribution"
                    ],
                    "evaluation": scaling_result["best_chain"]["evaluation"],
                }

            return ChatCompletionResponse(**response_data)

        else:
            # Handle cloud providers (OpenAI, Anthropic, Grok, DeepSeek, etc.)
            provider_name = provider_info["name"].lower()

            # Map provider names to adapter classes and their env var keys
            provider_adapters = {
                "openai": (OpenAIAdapter, "OPENAI_API_KEY", None),
                "anthropic": (AnthropicAdapter, "ANTHROPIC_API_KEY", None),
                "grok": (GrokAdapter, "GROK_API_KEY", "https://api.x.ai/v1"),
                "deepseek": (DeepSeekAdapter, "DEEPSEEK_API_KEY", None),
            }

            if provider_name not in provider_adapters:
                raise_problem(
                    status=501,
                    title="Not Implemented",
                    detail=f"Provider {provider_info['name']} not yet implemented in chat endpoint",
                    type_uri="https://api.goblin.fuaad.ai/errors/not-implemented",
                    code="PROVIDER_NOT_IMPLEMENTED",
                )

            # Get adapter class, API key env var, and base URL
            adapter_class, api_key_env, base_url = provider_adapters[provider_name]
            api_key = os.getenv(api_key_env)

            if not api_key:
                raise_internal_error(
                    f"API key not configured for provider {provider_info['name']}"
                )

            # Initialize adapter
            adapter = adapter_class(api_key, base_url)

            # Make the completion request with timing
            import time

            start_time = time.time()

            try:
                response_text = await adapter.chat(
                    model=selected_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=top_p,
                )
                success = True
            except Exception as e:
                success = False
                raise e
            finally:
                # Record latency metrics
                end_time = time.time()
                response_time_ms = (end_time - start_time) * 1000
                tokens_used = estimate_tokens(response_text) if response_text else 0

                try:
                    await latency_monitor.record_metric(
                        provider_name=provider_name,
                        model_name=selected_model,
                        response_time_ms=response_time_ms,
                        tokens_used=tokens_used,
                        success=success,
                    )
                except Exception as e:
                    logger.warning(f"Failed to record latency metric: {e}")

            # Build response
            response_data = {
                "id": routing_result["request_id"],
                "model": selected_model,
                "provider": provider_info["display_name"],
                "intent": routing_result.get("intent"),
                "routing_explanation": routing_result.get("routing_explanation"),
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": response_text},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": routing_result.get("context_length", 0),
                    "completion_tokens": estimate_tokens(response_text),
                    "total_tokens": routing_result.get("context_length", 0)
                    + estimate_tokens(response_text),
                },
                "metadata": {
                    "response_time_ms": response_time_ms,
                    "tokens_used": tokens_used,
                    "success": success,
                },
            }

            # Record token usage in gateway service
            if tokens_used > 0:
                try:
                    await gateway_service.record_usage(
                        None,  # No API key with JWT auth
                        tokens_used,
                        intent=gateway_result.intent,
                        success=success,
                    )
                except Exception as e:
                    logger.warning(f"Failed to record token usage: {e}")

            return ChatCompletionResponse(**response_data)

    except Exception as e:
        # Record failed request in anomaly detector
        if gateway_result:
            try:
                await gateway_service.record_usage(
                    None,  # No API key with JWT auth
                    0,  # No tokens used for failed requests
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


@router.get("/models")
async def list_available_models(
    req: Request,
    service: RoutingService = Depends(get_routing_service),
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
