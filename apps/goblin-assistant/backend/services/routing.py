"""
Routing service for provider discovery, health monitoring, and intelligent task routing.
"""

import uuid
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session

from models.provider import Provider, ProviderMetric, RoutingRequest

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
    VertexAdapter,
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
from . import routing_helpers

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
            "goblin-ollama-server": OllamaAdapter,
            "ollama_gcp": OllamaAdapter,  # GCP-hosted Ollama uses same adapter
            "goblin-llamacpp-server": LlamaCppAdapter,
            "llamacpp_gcp": LlamaCppAdapter,  # GCP-hosted llama.cpp uses same adapter
            "silliconflow": SilliconflowAdapter,
            "moonshot": MoonshotAdapter,
            "elevenlabs": ElevenLabsAdapter,
            "vertex": VertexAdapter,
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
            return self.db.query(Provider).filter(Provider.is_active).all()

        providers = await asyncio.to_thread(_sync_query)

        result = []
        for provider in providers:
            # Get API key - try encrypted first, fall back to plain text
            api_key = None
            if provider.api_key_encrypted:
                try:
                    api_key = self.encryption_service.decrypt(
                        provider.api_key_encrypted
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to decrypt API key for provider {provider.name}: {e}"
                    )

            # Fall back to plain API key if encrypted not available
            if not api_key and provider.api_key:
                api_key = provider.api_key

            if not api_key:
                logger.warning(f"No API key available for provider {provider.name}")
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
                    "base_url": provider.base_url,
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
            # Handle autoscaling checks and emergency routing
            autoscaling_result = (
                await routing_helpers.handle_autoscaling_and_emergency_routing(
                    self.autoscaling_service,
                    capability,
                    requirements,
                    request_id,
                    client_ip,
                    user_id,
                    request_path,
                )
            )

            # If rate limit exceeded, return immediately
            if not autoscaling_result.get("success", True):
                return autoscaling_result

            # If emergency routing needed, handle it
            if autoscaling_result.get("emergency_routing"):
                return await self._route_emergency_request(
                    autoscaling_result["capability"],
                    autoscaling_result["requirements"],
                    autoscaling_result["request_id"],
                )

            # Continue with normal routing
            requirements = autoscaling_result.get("requirements", requirements)

            # Check if this is a chat request that can be handled by local LLMs
            if capability == "chat" and requirements:
                local_routing = await routing_helpers.handle_local_llm_routing(
                    self.autoscaling_service,
                    self.db,
                    capability,
                    requirements,
                    request_id,
                )
                if local_routing:
                    return await routing_helpers.process_local_llm_routing_result(
                        local_routing,
                        request_id,
                        capability,
                        requirements,
                        self._log_routing_request,
                    )

            # Handle provider selection and fallback logic
            provider_result = (
                await routing_helpers.handle_provider_selection_and_fallback(
                    self,
                    capability,
                    requirements,
                    request_id,
                    sla_target_ms,
                    cost_budget,
                    latency_priority,
                )
            )

            return provider_result

        except Exception as e:
            return await routing_helpers.handle_routing_error(
                e, request_id, capability, requirements, self._log_routing_request
            )

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
        return routing_helpers.check_provider_requirements(provider, requirements)

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
        cost_penalty = self._calculate_cost_penalty_with_budget(
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
            Health score (-50 to 75)
        """
        return await routing_helpers.calculate_provider_health_score(
            self.db, provider_id
        )

    def _calculate_cost_penalty(
        self, provider: Dict[str, Any], capability: str
    ) -> float:
        """Calculate cost penalty for provider.

        Args:
            provider: Provider info
            capability: Required capability

        Returns:
            Cost penalty (0-20, higher = more expensive)
        """
        from .routing_helpers import calculate_cost_penalty

        return calculate_cost_penalty(provider, capability)

    async def _get_performance_bonus(self, provider_id: int) -> float:
        """Get performance bonus based on recent metrics.

        Args:
            provider_id: Provider ID

        Returns:
            Performance bonus (0-15)
        """
        return await routing_helpers.calculate_provider_performance_bonus(
            self.db, provider_id
        )

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
        from .routing_helpers import calculate_capability_bonus

        return calculate_capability_bonus(provider, capability, requirements)

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
        return await routing_helpers.calculate_provider_sla_score(
            self.latency_monitor, self.db, provider, sla_target_ms
        )

    def _calculate_cost_penalty_with_budget(
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
        from .routing_helpers import calculate_cost_penalty_with_budget

        return calculate_cost_penalty_with_budget(provider, capability, cost_budget)

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
        return await routing_helpers.should_use_latency_fallback(
            self.latency_monitor,
            providers,
            sla_target_ms,
            latency_priority,
            self.default_sla_targets,
        )

    async def _get_fallback_provider(self) -> Optional[Dict[str, Any]]:
        """Get fallback provider (local Mistral or Ollama 1b).

        Returns:
            Fallback provider info or None
        """
        return await routing_helpers.get_fallback_provider_info(
            self.db, self.encryption_service, self.adapters
        )

    async def _check_autoscaling(
        self,
        client_ip: Optional[str],
        user_id: Optional[str],
        request_path: Optional[str],
        capability: str,
    ) -> Dict[str, Any]:
        """Check autoscaling conditions and rate limits."""
        from .routing_helpers import check_autoscaling_conditions

        return await check_autoscaling_conditions(
            self.autoscaling_service, client_ip, user_id, request_path, capability
        )

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
                    "name": "goblin-ollama-server",
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
