"""
Compatibility layer for the new routing subsystem.

Provides backward compatibility with the existing RoutingService interface
while delegating to the new unified routing subsystem.
"""

import logging
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from services.routing_subsystem import get_routing_manager, RoutingManager
from services.encryption import EncryptionService
from providers.base import InferenceRequest, InferenceResult

logger = logging.getLogger(__name__)


class RoutingServiceCompat:
    """Compatibility wrapper for the new routing subsystem.

    Maintains the same interface as the old RoutingService while using
    the new unified routing subsystem internally.
    """

    def __init__(self, db: Session, encryption_key: str):
        """Initialize compatibility wrapper.

        Args:
            db: Database session (kept for compatibility, may not be used)
            encryption_key: Encryption key (kept for compatibility)
        """
        self.db = db
        self.encryption_key = encryption_key
        self.encryption_service = EncryptionService(encryption_key)
        self.routing_manager: Optional[RoutingManager] = None

    async def initialize(self):
        """Initialize the routing subsystem."""
        if self.routing_manager is None:
            self.routing_manager = get_routing_manager()
            await self.routing_manager.start()
        logger.info("Routing service compatibility layer initialized")

    async def discover_providers(self) -> List[Dict[str, Any]]:
        """Discover all active providers and their capabilities.

        Returns:
            List of provider information dictionaries
        """
        if not self.routing_manager:
            await self.initialize()

        # Get system status from the new routing manager
        status = self.routing_manager.get_system_status()

        providers = []
        for provider_id, provider_info in status["providers"].items():
            # Convert new format to old format
            providers.append(
                {
                    "id": provider_id,  # Use provider_id as id for compatibility
                    "name": provider_id,
                    "display_name": provider_id.replace("_", " ").title(),
                    "capabilities": ["chat"],  # Default capability
                    "models": [],  # Would need to be populated from provider
                    "priority": 1,  # Default priority
                    "is_active": provider_info["health"] == "healthy",
                    "health_status": provider_info["health"],
                    "metrics": provider_info["metrics"],
                }
            )

        return providers

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
        """Route a request to the best available provider.

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
        if not self.routing_manager:
            await self.initialize()

        import uuid

        request_id = str(uuid.uuid4())

        try:
            # Determine routing policy based on parameters
            policy_name = self._determine_policy(
                latency_priority, cost_budget, sla_target_ms
            )

            # Convert old format to new InferenceRequest
            inference_request = self._convert_to_inference_request(
                capability, requirements
            )

            # Use client_ip as client_key for rate limiting
            client_key = client_ip or user_id or "anonymous"

            # Route the request
            result = await self.routing_manager.route_request(
                request=inference_request,
                policy_name=policy_name,
                client_key=client_key,
            )

            # Convert result back to old format
            return self._convert_from_inference_result(result, request_id)

        except Exception as e:
            logger.error(f"Routing request failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "request_id": request_id,
            }

    def _determine_policy(
        self,
        latency_priority: Optional[str],
        cost_budget: Optional[float],
        sla_target_ms: Optional[float],
    ) -> str:
        """Determine routing policy based on request parameters.

        Args:
            latency_priority: Latency priority level
            cost_budget: Cost budget constraint
            sla_target_ms: SLA target

        Returns:
            Policy name to use
        """
        if latency_priority in ["ultra_low", "low"] or (
            sla_target_ms and sla_target_ms < 2000
        ):
            return "latency_first"
        elif cost_budget is not None and cost_budget < 0.01:
            return "cost_first"
        else:
            return "latency_first"  # Default policy

    def _convert_to_inference_request(
        self, capability: str, requirements: Optional[Dict[str, Any]]
    ) -> InferenceRequest:
        """Convert old request format to new InferenceRequest.

        Args:
            capability: Required capability
            requirements: Additional requirements

        Returns:
            InferenceRequest instance
        """
        reqs = requirements or {}

        # Extract messages from requirements - handle both old and new formats
        messages = reqs.get("messages", [])
        if not messages:
            # Handle old format where "message" is passed instead of "messages"
            message_content = reqs.get("message", "")
            if message_content:
                messages = [{"role": "user", "content": message_content}]
            else:
                # Create a default message if none provided
                messages = [{"role": "user", "content": "Hello"}]

        # Determine model and model family
        model = reqs.get("model", "")
        if not model:
            # Default model based on capability
            if capability == "chat":
                model = "gpt-3.5-turbo"
            else:
                model = "gpt-4"

        # Determine model family
        if "gpt" in model.lower():
            model_family = "openai"
        elif "claude" in model.lower():
            model_family = "anthropic"
        elif "llama" in model.lower() or "ollama" in model.lower():
            model_family = "ollama"
        else:
            model_family = "general"

        return InferenceRequest(
            messages=messages,
            model=model,
            model_family=model_family,
            max_tokens=reqs.get("max_tokens", 1000),
            temperature=reqs.get("temperature", 0.7),
            stream=reqs.get("stream", False),
        )

    def _convert_from_inference_result(
        self, result: InferenceResult, request_id: str
    ) -> Dict[str, Any]:
        """Convert InferenceResult back to old response format.

        Args:
            result: InferenceResult from new subsystem
            request_id: Request ID

        Returns:
            Dict in old response format
        """
        if hasattr(result, "success") and not result.success:
            return {
                "success": False,
                "error": getattr(result, "error", "Unknown error"),
                "request_id": request_id,
            }

        # Extract provider info
        provider_id = getattr(result, "provider_id", "unknown")
        latency_ms = getattr(result, "latency_ms", 0)
        cost_usd = getattr(result, "cost_usd", 0.0)

        return {
            "success": True,
            "provider": {
                "id": provider_id,
                "name": provider_id,
                "latency_ms": latency_ms,
                "cost_usd": cost_usd,
            },
            "content": getattr(result, "content", ""),
            "usage": getattr(result, "usage", {}),
            "request_id": request_id,
        }


# Create a global instance for backward compatibility
_routing_service_compat: Optional[RoutingServiceCompat] = None


def get_routing_service_compat(
    db: Session, encryption_key: str
) -> RoutingServiceCompat:
    """Get the compatibility routing service instance."""
    global _routing_service_compat
    if _routing_service_compat is None:
        _routing_service_compat = RoutingServiceCompat(db, encryption_key)
    return _routing_service_compat


# Alias for backward compatibility
RoutingService = RoutingServiceCompat
