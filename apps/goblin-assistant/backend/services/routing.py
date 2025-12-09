"""
Routing service for provider discovery, health monitoring, and intelligent task routing.
"""

import uuid
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session

from models.routing import RoutingProvider, ProviderMetric, RoutingRequest

from providers import (
    OpenAIAdapter,
    AnthropicAdapter,
    GrokAdapter,
    DeepSeekAdapter,
    OllamaAdapter,
    LlamaCppAdapter,
    SilliconflowAdapter,
    MoonshotAdapter,
    ElevenLabsAdapter,
)
from providers.registry import get_provider_registry
from providers.base import InferenceRequest
from services.encryption import EncryptionService
from services.local_llm_routing import (
    select_model,
    get_system_prompt,
    get_routing_explanation,
    detect_intent,
    get_context_length,
    Intent,
    LatencyTarget,
)
from services.autoscaling_service import AutoscalingService, FallbackLevel
from services.latency_monitoring_service import LatencyMonitoringService

logger = logging.getLogger(__name__)


class RoutingService:
    """Service for intelligent routing of AI tasks to appropriate providers."""

    def __init__(self, db: Session, encryption_key: str):
        """Initialize routing service.

        Args:
            db: Database session
            encryption_key: Key for decrypting API keys
        """
        self.db = db
        self.encryption_service = EncryptionService(encryption_key)
        self.latency_monitor = LatencyMonitoringService()
        self.autoscaling_service = AutoscalingService()

        # SLA and cost configuration
        self.default_sla_targets = {
            "ultra_low": 500,  # ms
            "low": 1000,  # ms
            "medium": 2000,  # ms
            "high": 5000,  # ms
        }

        self.cost_budget_weights = {
            "latency_priority": 0.3,  # Weight for latency in scoring
            "cost_priority": 0.4,  # Weight for cost in scoring
            "sla_compliance": 0.3,  # Weight for SLA compliance
        }

        self.adapters = {
            "openai": OpenAIAdapter,
            "anthropic": AnthropicAdapter,
            "grok": GrokAdapter,
            "deepseek": DeepSeekAdapter,
            "ollama": OllamaAdapter,
            "llamacpp": LlamaCppAdapter,
            "silliconflow": SilliconflowAdapter,
            "moonshot": MoonshotAdapter,
            "elevenlabs": ElevenLabsAdapter,
        }

    async def initialize(self):
        """Initialize async components"""
        await self.autoscaling_service.initialize()
        logger.info("Routing service initialized with autoscaling")

    async def discover_providers(self) -> List[Dict[str, Any]]:
        """Discover all active providers and their capabilities.

        Returns:
            List of provider information dictionaries
        """
        import asyncio

        # Run database query in thread pool
        def _sync_query():
            return (
                self.db.query(RoutingProvider).filter(RoutingProvider.is_active).all()
            )

        providers = await asyncio.to_thread(_sync_query)

        result = []
        for provider in providers:
            # Decrypt API key
            try:
                api_key = self.encryption_service.decrypt(provider.api_key_encrypted)
            except Exception as e:
                logger.error(
                    f"Failed to decrypt API key for provider {provider.name}: {e}"
                )
                continue

            # Get adapter
            adapter_class = self.adapters.get(provider.name.lower())
            if not adapter_class:
                logger.warning(f"No adapter found for provider {provider.name}")
                continue

            # Initialize adapter
            adapter = adapter_class(api_key, provider.base_url)

            # Get models
            models = await adapter.list_models()

            result.append(
                {
                    "id": provider.id,
                    "name": provider.name,
                    "display_name": provider.display_name,
                    "capabilities": provider.capabilities,
                    "models": models,
                    "priority": provider.priority,
                    "is_active": provider.is_active,
                }
            )

        return result

    async def route_request(
        self,
        capability: str,
        requirements: Optional[Dict[str, Any]] = None,
        sla_target_ms: Optional[float] = None,
        cost_budget: Optional[float] = None,
        latency_priority: Optional[str] = None,
        client_ip: Optional[str] = None,
        user_id: Optional[str] = None,
        request_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Route a request to the best available provider with autoscaling support.

        Args:
            capability: Required capability (e.g., "chat", "vision")
            requirements: Additional requirements for the request
            sla_target_ms: SLA target response time in milliseconds
            cost_budget: Maximum cost per request in USD
            latency_priority: Latency priority ('ultra_low', 'low', 'medium', 'high')
            client_ip: Client IP for rate limiting
            user_id: User ID for rate limiting
            request_path: Request path for emergency endpoint detection

        Returns:
            Dict with routing decision and provider info
        """
        request_id = str(uuid.uuid4())

        try:
            # Check autoscaling and rate limiting first
            autoscaling_result = await self._check_autoscaling(
                client_ip, user_id, request_path, capability
            )

            if not autoscaling_result["allowed"]:
                return {
                    "success": False,
                    "error": "Rate limit exceeded",
                    "fallback_level": autoscaling_result["fallback_level"].value,
                    "retry_after": autoscaling_result["retry_after"],
                    "request_id": request_id,
                }

            fallback_level = autoscaling_result["fallback_level"]

            # If emergency mode or emergency endpoint, use minimal routing
            if (
                fallback_level == FallbackLevel.EMERGENCY
                or autoscaling_result["emergency_endpoint"]
            ):
                return await self._route_emergency_request(
                    capability, requirements, request_id
                )

            # If cheap model fallback requested, modify requirements
            if fallback_level == FallbackLevel.CHEAP_MODEL:
                requirements = requirements or {}
                requirements["model"] = self.autoscaling_service.cheap_fallback_model
                requirements["fallback_mode"] = True
                logger.info(f"Using cheap fallback model for request {request_id}")

            # Check if this is a chat request that can be handled by local LLMs
            if capability == "chat" and requirements:
                local_routing = await self._try_local_llm_routing(requirements)
                if local_routing:
                    # Log the routing decision
                    await self._log_routing_request(
                        request_id=request_id,
                        capability=capability,
                        requirements=requirements,
                        selected_provider_id=local_routing.get("provider_id"),
                        success=True,
                    )

                    return {
                        "success": True,
                        "request_id": request_id,
                        "provider": local_routing["provider"],
                        "capability": capability,
                        "requirements": requirements,
                        "routing_explanation": local_routing.get("explanation"),
                        "recommended_params": local_routing.get("params"),
                        "system_prompt": local_routing.get("system_prompt"),
                    }

            # Find suitable providers
            candidates = await self._find_suitable_providers(capability, requirements)

            if not candidates:
                return {
                    "success": False,
                    "error": f"No providers available for capability: {capability}",
                    "request_id": request_id,
                }

            # Check if we should use fallback due to latency issues
            use_fallback = await self._should_use_fallback(
                candidates, sla_target_ms, latency_priority
            )

            if use_fallback:
                fallback_provider = await self._get_fallback_provider()
                if fallback_provider:
                    logger.info(
                        f"Using fallback provider: {fallback_provider['display_name']}"
                    )

                    # Log the routing decision
                    await self._log_routing_request(
                        request_id=request_id,
                        capability=capability,
                        requirements=requirements,
                        selected_provider_id=fallback_provider["id"],
                        success=True,
                    )

                    return {
                        "success": True,
                        "request_id": request_id,
                        "provider": fallback_provider,
                        "capability": capability,
                        "requirements": requirements,
                        "is_fallback": True,
                        "fallback_reason": "latency_sla_violation",
                    }

            # Score and rank providers
            scored_providers = await self._score_providers(
                candidates,
                capability,
                requirements,
                sla_target_ms,
                cost_budget,
                latency_priority,
            )

            if not scored_providers:
                return {
                    "success": False,
                    "error": "No healthy providers available",
                    "request_id": request_id,
                }

            # Select best provider
            selected_provider = scored_providers[0]

            # Log the routing decision
            await self._log_routing_request(
                request_id=request_id,
                capability=capability,
                requirements=requirements,
                selected_provider_id=selected_provider["id"],
                success=True,
            )

            return {
                "success": True,
                "request_id": request_id,
                "provider": selected_provider,
                "capability": capability,
                "requirements": requirements or {},
            }

        except Exception as e:
            logger.error(f"Routing failed for capability {capability}: {e}")

            # Log failed routing
            await self._log_routing_request(
                request_id=request_id,
                capability=capability,
                requirements=requirements,
                success=False,
                error_message=str(e),
            )

            return {"success": False, "error": str(e), "request_id": request_id}

    async def _try_local_llm_routing(
        self, requirements: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Try to route request to local LLM based on intelligent routing rules.

        Args:
            requirements: Request requirements including messages, latency_target, etc.

        Returns:
            Dict with local provider info and routing details, or None if not suitable
        """
        try:
            # Extract routing parameters
            messages = requirements.get("messages", [])
            if not messages:
                return None

            # Get optional routing hints
            intent = requirements.get("intent")
            if intent and isinstance(intent, str):
                try:
                    intent = Intent(intent)
                except ValueError:
                    intent = None

            latency_target = requirements.get("latency_target", "medium")
            if isinstance(latency_target, str):
                try:
                    latency_target = LatencyTarget(latency_target)
                except ValueError:
                    latency_target = LatencyTarget.MEDIUM

            context_provided = requirements.get("context")
            cost_priority = requirements.get("cost_priority", False)

            # Check autoscaling service for rate limiting and fallback
            client_ip = requirements.get("client_ip", "unknown")
            user_id = requirements.get("user_id")

            (
                allowed,
                fallback_level,
                rate_limit_metadata,
            ) = await self.autoscaling_service.check_rate_limit(
                client_ip=client_ip, user_id=user_id
            )

            if not allowed:
                logger.warning(
                    f"Request denied due to rate limiting: {rate_limit_metadata}"
                )
                return {
                    "error": "Rate limit exceeded",
                    "fallback_level": fallback_level.value,
                    "retry_after": 60,
                    "request_id": requirements.get("request_id"),
                }

            force_cheap_fallback = fallback_level == FallbackLevel.CHEAP_MODEL

            # Select model using routing logic
            model_id, params = select_model(
                messages=messages,
                intent=intent,
                latency_target=latency_target,
                context_provided=context_provided,
                cost_priority=cost_priority,
                force_cheap_fallback=force_cheap_fallback,
            )

            # Find Ollama provider
            def _sync_find_provider():
                return (
                    self.db.query(RoutingProvider)
                    .filter(RoutingProvider.name == "ollama", RoutingProvider.is_active)
                    .first()
                )

            ollama_provider = await asyncio.to_thread(_sync_find_provider)

            if not ollama_provider:
                logger.warning("Ollama provider not found or not active")
                return None

            # Get system prompt
            detected_intent = intent or detect_intent(messages)
            system_prompt = get_system_prompt(detected_intent)

            # Get routing explanation
            context_length = get_context_length(messages)
            if context_provided:
                from services.local_llm_routing import estimate_token_count

                context_length += estimate_token_count(context_provided)

            explanation = get_routing_explanation(
                model_id, detected_intent, context_length, latency_target
            )

            # Build provider info
            provider_info = {
                "id": ollama_provider.id,
                "name": ollama_provider.name,
                "display_name": ollama_provider.display_name,
                "model": model_id,
                "capabilities": ollama_provider.capabilities,
                "priority": ollama_provider.priority,
            }

            return {
                "provider": provider_info,
                "provider_id": ollama_provider.id,
                "params": params,
                "system_prompt": system_prompt,
                "explanation": explanation,
                "intent": detected_intent.value,
                "context_length": context_length,
            }

        except Exception as e:
            logger.error(f"Local LLM routing failed: {e}")
            return None

    async def _find_suitable_providers(
        self, capability: str, requirements: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Find providers that can handle the given capability and requirements.

        Args:
            capability: Required capability
            requirements: Additional requirements

        Returns:
            List of suitable provider dictionaries
        """
        providers = await self.discover_providers()

        suitable = []
        for provider in providers:
            # Check if provider supports the capability
            if capability not in provider["capabilities"]:
                continue

            # Check additional requirements
            if requirements:
                if not self._check_requirements(provider, requirements):
                    continue

            suitable.append(provider)

        return suitable

    def _check_requirements(
        self, provider: Dict[str, Any], requirements: Dict[str, Any]
    ) -> bool:
        """Check if provider meets additional requirements.

        Args:
            provider: Provider information
            requirements: Requirements to check

        Returns:
            True if requirements are met
        """
        # Check model requirements
        if "model" in requirements:
            required_model = requirements["model"]
            if not any(model["id"] == required_model for model in provider["models"]):
                return False

        # Check context window requirements
        if "min_context_window" in requirements:
            min_window = requirements["min_context_window"]
            if not any(
                model["context_window"] >= min_window for model in provider["models"]
            ):
                return False

        # Check vision capability
        if requirements.get("vision_required", False):
            if "vision" not in provider["capabilities"]:
                return False

        return True

    async def _score_providers(
        self,
        providers: List[Dict[str, Any]],
        capability: str,
        requirements: Optional[Dict[str, Any]] = None,
        sla_target_ms: Optional[float] = None,
        cost_budget: Optional[float] = None,
        latency_priority: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Score and rank providers based on health, performance, cost, and SLA compliance.

        Args:
            providers: List of provider candidates
            capability: Required capability
            requirements: Additional requirements
            sla_target_ms: SLA target response time in milliseconds
            cost_budget: Maximum cost per request in USD
            latency_priority: Latency priority level

        Returns:
            List of providers with scores, sorted by score descending
        """
        scored = []

        for provider in providers:
            score = await self._calculate_provider_score(
                provider,
                capability,
                requirements,
                sla_target_ms,
                cost_budget,
                latency_priority,
            )
            if score > 0:  # Only include providers with positive scores (healthy)
                provider_with_score = provider.copy()
                provider_with_score["score"] = score
                scored.append(provider_with_score)

        # Sort by score descending
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored

    async def _calculate_provider_score(
        self,
        provider: Dict[str, Any],
        capability: str,
        requirements: Optional[Dict[str, Any]] = None,
        sla_target_ms: Optional[float] = None,
        cost_budget: Optional[float] = None,
        latency_priority: Optional[str] = None,
    ) -> float:
        """Calculate a score for a provider based on multiple factors including SLA and cost.

        Args:
            provider: Provider information
            capability: Required capability
            requirements: Additional requirements
            sla_target_ms: SLA target response time in milliseconds
            cost_budget: Maximum cost per request in USD
            latency_priority: Latency priority level

        Returns:
            Score between 0-100 (0 = unusable, 100 = perfect)
        """
        base_score = 50.0  # Start with neutral score

        # Get recent health metrics
        health_score = await self._get_health_score(provider["id"])
        base_score += (
            health_score * self.cost_budget_weights["latency_priority"]
        )  # Weighted health score

        # Priority bonus
        priority_bonus = provider["priority"] * 2.0
        base_score += priority_bonus

        # SLA compliance bonus/penalty
        if sla_target_ms:
            sla_score = await self._calculate_sla_score(provider, sla_target_ms)
            base_score += sla_score * self.cost_budget_weights["sla_compliance"]

        # Cost factor with budget consideration
        cost_penalty = await self._calculate_cost_penalty_with_budget(
            provider, capability, cost_budget
        )
        base_score -= cost_penalty * self.cost_budget_weights["cost_priority"]

        # Performance bonus (faster = better, adjusted for latency priority)
        performance_bonus = await self._get_performance_bonus(provider["id"])
        latency_weight = 1.0
        if latency_priority:
            latency_weight = self._get_latency_weight(latency_priority)
        base_score += performance_bonus * latency_weight

        # Capability match bonus
        capability_bonus = self._calculate_capability_bonus(
            provider, capability, requirements
        )
        base_score += capability_bonus

        # Ensure score is within bounds
        return max(0.0, min(100.0, base_score))

    async def _get_health_score(self, provider_id: int) -> float:
        """Get health score for provider based on recent metrics.

        Args:
            provider_id: Provider ID

        Returns:
            Health score (-50 to 50)
        """
        # Get metrics from last hour
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)

        def _sync_get_metrics():
            return (
                self.db.query(ProviderMetric)
                .filter(
                    ProviderMetric.provider_id == provider_id,
                    ProviderMetric.timestamp >= one_hour_ago,
                )
                .all()
            )

        metrics = await asyncio.to_thread(_sync_get_metrics)

        if not metrics:
            return 0.0  # No data = neutral

        # Calculate average health metrics
        total_metrics = len(metrics)
        healthy_count = sum(1 for m in metrics if m.is_healthy)
        health_rate = healthy_count / total_metrics if total_metrics > 0 else 0

        # Average response time (prefer faster)
        avg_response_time = (
            sum(m.response_time_ms for m in metrics if m.response_time_ms)
            / len([m for m in metrics if m.response_time_ms])
            if metrics
            else 1000
        )

        # Response time score (faster = better, max 2000ms = 0 points)
        response_time_score = max(0, 25 - (avg_response_time / 80))

        # Health score: -50 (all unhealthy) to 50 (all healthy)
        health_score = (health_rate - 0.5) * 100

        return health_score + response_time_score

    async def _calculate_cost_penalty(
        self, provider: Dict[str, Any], capability: str
    ) -> float:
        """Calculate cost penalty for provider.

        Args:
            provider: Provider info
            capability: Required capability

        Returns:
            Cost penalty (0-20, higher = more expensive)
        """
        # Find cheapest model for capability
        min_cost = float("inf")
        for model in provider["models"]:
            if capability in model["capabilities"]:
                # Use input token cost as proxy
                cost = model["pricing"].get("input", 0.002)
                min_cost = min(min_cost, cost)

        if min_cost == float("inf"):
            return 10.0  # Default penalty

        # Penalty based on cost relative to baseline (0.001 = 0 penalty, 0.01 = 20 penalty)
        return min(20.0, (min_cost - 0.001) * 2000)

    async def _get_performance_bonus(self, provider_id: int) -> float:
        """Get performance bonus based on recent metrics.

        Args:
            provider_id: Provider ID

        Returns:
            Performance bonus (0-15)
        """
        # Get recent metrics
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)

        def _sync_get_recent_metrics():
            return (
                self.db.query(ProviderMetric)
                .filter(
                    ProviderMetric.provider_id == provider_id,
                    ProviderMetric.timestamp >= one_hour_ago,
                )
                .order_by(ProviderMetric.timestamp.desc())
                .limit(10)
                .all()
            )

        metrics = await asyncio.to_thread(_sync_get_recent_metrics)

        if not metrics:
            return 0.0

        # Average response time
        response_times = [m.response_time_ms for m in metrics if m.response_time_ms]
        if not response_times:
            return 0.0

        avg_response_time = sum(response_times) / len(response_times)

        # Bonus for faster response times (under 500ms = 15 points, over 2000ms = 0)
        if avg_response_time <= 500:
            return 15.0
        elif avg_response_time >= 2000:
            return 0.0
        else:
            return 15.0 * (2000 - avg_response_time) / 1500

    def _calculate_capability_bonus(
        self,
        provider: Dict[str, Any],
        capability: str,
        requirements: Optional[Dict[str, Any]] = None,
    ) -> float:
        """Calculate bonus for capability match.

        Args:
            provider: Provider info
            capability: Required capability
            requirements: Additional requirements

        Returns:
            Capability bonus (0-10)
        """
        bonus = 0.0

        # Base capability match
        if capability in provider["capabilities"]:
            bonus += 5.0

        # Specific model requirement
        if requirements and "model" in requirements:
            required_model = requirements["model"]
            if any(model["id"] == required_model for model in provider["models"]):
                bonus += 5.0

        return bonus

    async def _calculate_sla_score(
        self, provider: Dict[str, Any], sla_target_ms: float
    ) -> float:
        """Calculate SLA compliance score for a provider.

        Args:
            provider: Provider information
            sla_target_ms: SLA target response time in milliseconds

        Returns:
            SLA score (-20 to 20, higher = better SLA compliance)
        """
        # Try to get SLA compliance from latency monitoring
        try:
            # Get the first model as representative (could be enhanced to check all models)
            if provider.get("models"):
                model_name = provider["models"][0]["id"]
                sla_check = await self.latency_monitor.check_sla_compliance(
                    provider["name"], model_name, sla_target_ms
                )

                if sla_check.get("data_available"):
                    if sla_check["compliant"]:
                        return 20.0  # Full bonus for SLA compliance
                    else:
                        # Partial penalty based on how far off SLA we are
                        current_p95 = sla_check.get("current_p95", float("inf"))
                        if current_p95 > sla_target_ms:
                            overrun_ratio = current_p95 / sla_target_ms
                            return max(-20.0, 10.0 - (overrun_ratio - 1) * 15.0)
        except Exception as e:
            logger.warning(
                f"Failed to check SLA compliance for {provider['name']}: {e}"
            )

        # Fallback to basic health check
        try:
            health_score = await self._get_health_score(provider["id"])
            # Convert health score to SLA score (rough approximation)
            return health_score * 0.4
        except Exception:
            return 0.0

    async def _calculate_cost_penalty_with_budget(
        self,
        provider: Dict[str, Any],
        capability: str,
        cost_budget: Optional[float] = None,
    ) -> float:
        """Calculate cost penalty considering budget constraints.

        Args:
            provider: Provider info
            capability: Required capability
            cost_budget: Maximum cost per request in USD

        Returns:
            Cost penalty (0-30, higher = more expensive or over budget)
        """
        # Get base cost penalty
        base_penalty = await self._calculate_cost_penalty(provider, capability)

        # If no budget specified, return base penalty
        if cost_budget is None:
            return base_penalty

        # Find minimum cost for capability
        min_cost = float("inf")
        for model in provider["models"]:
            if capability in model["capabilities"]:
                # Use input token cost as proxy (rough estimate)
                cost = model["pricing"].get("input", 0.002)
                min_cost = min(min_cost, cost)

        if min_cost == float("inf"):
            return base_penalty + 10.0  # Penalty for no pricing info

        # Check if within budget
        if min_cost <= cost_budget:
            # Within budget, reduce penalty
            return base_penalty * 0.5
        else:
            # Over budget, significant penalty
            budget_overrun = min_cost / cost_budget
            return base_penalty + min(20.0, (budget_overrun - 1) * 10.0)

    def _get_latency_weight(self, latency_priority: str) -> float:
        """Get latency weight multiplier based on priority.

        Args:
            latency_priority: Latency priority ('ultra_low', 'low', 'medium', 'high')

        Returns:
            Weight multiplier for latency scoring
        """
        weights = {
            "ultra_low": 2.0,  # Double weight for ultra-low latency
            "low": 1.5,  # 50% bonus for low latency
            "medium": 1.0,  # Normal weight
            "high": 0.7,  # Reduced weight for high latency tolerance
        }
        return weights.get(latency_priority, 1.0)

    async def _should_use_fallback(
        self,
        providers: List[Dict[str, Any]],
        sla_target_ms: Optional[float] = None,
        latency_priority: Optional[str] = None,
    ) -> bool:
        """Check if we should use fallback to local models due to latency issues.

        Args:
            providers: Available providers
            sla_target_ms: SLA target response time
            latency_priority: Latency priority level

        Returns:
            True if fallback should be used
        """
        # If no SLA target or low latency priority, don't fallback
        if not sla_target_ms or latency_priority in ["medium", "high"]:
            return False

        # Check if any providers are meeting SLA targets
        sla_target = sla_target_ms or self.default_sla_targets.get(
            latency_priority, 2000
        )

        compliant_providers = 0
        total_checked = 0

        for provider in providers[:3]:  # Check top 3 providers
            if provider.get("models"):
                model_name = provider["models"][0]["id"]
                try:
                    sla_check = await self.latency_monitor.check_sla_compliance(
                        provider["name"], model_name, sla_target
                    )
                    total_checked += 1
                    if sla_check.get("compliant", False):
                        compliant_providers += 1
                except Exception as e:
                    logger.warning(f"Failed to check SLA for fallback: {e}")

        # If less than 50% of providers meet SLA, use fallback
        if total_checked > 0 and (compliant_providers / total_checked) < 0.5:
            logger.info(
                f"Using fallback: only {compliant_providers}/{total_checked} providers meet SLA target of {sla_target}ms"
            )
            return True

        return False

    async def _get_fallback_provider(self) -> Optional[Dict[str, Any]]:
        """Get fallback provider (local Mistral or Ollama 1b).

        Returns:
            Fallback provider info or None
        """

        # Try Mistral 3 small first (if available)
        def _sync_find_mistral():
            return (
                self.db.query(RoutingProvider)
                .filter(RoutingProvider.name == "ollama", RoutingProvider.is_active)
                .first()
            )

        mistral_provider = await asyncio.to_thread(_sync_find_mistral)

        if mistral_provider:
            # Check if Mistral models are available
            try:
                api_key = self.encryption_service.decrypt(
                    mistral_provider.api_key_encrypted
                )
                adapter = self.adapters["ollama"](api_key, mistral_provider.base_url)
                models = await adapter.list_models()

                # Look for Mistral 3 small or similar fast model
                fast_models = ["mistral:7b", "llama3.2:3b", "phi3:3.8b", "gemma:2b"]
                for model in models:
                    if any(fast_model in model["id"] for fast_model in fast_models):
                        return {
                            "id": mistral_provider.id,
                            "name": mistral_provider.name,
                            "display_name": f"{mistral_provider.display_name} (Fallback)",
                            "model": model["id"],
                            "capabilities": mistral_provider.capabilities,
                            "priority": mistral_provider.priority,
                            "is_fallback": True,
                        }
            except Exception as e:
                logger.warning(f"Failed to check Mistral fallback: {e}")

        # Fallback to basic Ollama 1b or any available model
        if mistral_provider:
            return {
                "id": mistral_provider.id,
                "name": mistral_provider.name,
                "display_name": f"{mistral_provider.display_name} (Fallback)",
                "model": "gemma:2b",  # Default fast fallback
                "capabilities": mistral_provider.capabilities,
                "priority": mistral_provider.priority,
                "is_fallback": True,
            }

        return None

    async def _check_autoscaling(
        self,
        client_ip: Optional[str],
        user_id: Optional[str],
        request_path: Optional[str],
        capability: str,
    ) -> Dict[str, Any]:
        """Check autoscaling conditions and rate limits."""
        try:
            await self.autoscaling_service.initialize()

            # Check if emergency mode
            if await self.autoscaling_service.is_emergency_mode():
                return {
                    "allowed": True,
                    "fallback_level": FallbackLevel.EMERGENCY,
                    "emergency_endpoint": True,
                    "retry_after": None,
                }

            # Check if emergency endpoint
            if request_path and await self.autoscaling_service.is_emergency_endpoint(
                request_path
            ):
                return {
                    "allowed": True,
                    "fallback_level": FallbackLevel.NORMAL,
                    "emergency_endpoint": True,
                    "retry_after": None,
                }

            # Check rate limiting
            (
                allowed,
                fallback_level,
                metadata,
            ) = await self.autoscaling_service.check_rate_limit(
                client_ip or "unknown", user_id
            )

            return {
                "allowed": allowed,
                "fallback_level": fallback_level,
                "emergency_endpoint": False,
                "retry_after": metadata.get("cooldown_until"),
            }

        except Exception as e:
            logger.error(f"Autoscaling check failed: {e}")
            # Allow request but log error
            return {
                "allowed": True,
                "fallback_level": FallbackLevel.NORMAL,
                "emergency_endpoint": False,
                "retry_after": None,
            }

    async def _route_emergency_request(
        self, capability: str, requirements: Optional[Dict[str, Any]], request_id: str
    ) -> Dict[str, Any]:
        """Route emergency requests with minimal functionality."""
        try:
            # For emergency mode, only allow basic health/auth endpoints
            if capability == "health":
                return {
                    "success": True,
                    "request_id": request_id,
                    "provider": {
                        "id": "emergency",
                        "name": "emergency",
                        "display_name": "Emergency Fallback",
                        "model": "basic",
                        "capabilities": ["health"],
                    },
                    "capability": capability,
                    "emergency_mode": True,
                }

            # For auth, try to find any available provider
            providers = await self.discover_providers()
            for provider in providers:
                if "auth" in provider.get("capabilities", []):
                    return {
                        "success": True,
                        "request_id": request_id,
                        "provider": provider,
                        "capability": capability,
                        "emergency_mode": True,
                    }

            # Fallback to cheap model for basic chat
            return {
                "success": True,
                "request_id": request_id,
                "provider": {
                    "id": "fallback",
                    "name": "ollama",
                    "display_name": "Cheap Fallback Model",
                    "model": self.autoscaling_service.cheap_fallback_model,
                    "capabilities": ["chat"],
                },
                "capability": capability,
                "emergency_mode": True,
                "fallback_model": True,
            }

        except Exception as e:
            logger.error(f"Emergency routing failed: {e}")
            return {
                "success": False,
                "error": "Emergency routing failed",
                "request_id": request_id,
            }

    async def _log_routing_request(
        self,
        request_id: str,
        capability: str,
        requirements: Optional[Dict[str, Any]] = None,
        selected_provider_id: Optional[int] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> None:
        """Log a routing request asynchronously.

        Args:
            request_id: Unique request ID
            capability: Requested capability
            requirements: Request requirements
            selected_provider_id: ID of selected provider
            success: Whether routing was successful
            error_message: Error message if failed
        """
        import asyncio

        # Run database logging in a thread pool to avoid blocking the event loop
        def _sync_log():
            try:
                routing_request = RoutingRequest(
                    request_id=request_id,
                    capability=capability,
                    requirements=requirements,
                    selected_provider_id=selected_provider_id,
                    success=success,
                    error_message=error_message,
                )
                self.db.add(routing_request)
                self.db.commit()
            except Exception as e:
                logger.error(f"Failed to log routing request: {e}")
                self.db.rollback()

        # Run in thread pool to avoid blocking async operations
        await asyncio.to_thread(_sync_log)
