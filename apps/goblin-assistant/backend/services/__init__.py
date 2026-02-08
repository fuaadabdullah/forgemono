"""
Service container for dependency injection.

This module provides a simple dependency injection container for managing
service instances and their dependencies.
"""

from typing import Dict, Type, Any, Optional
from sqlalchemy.orm import Session

# Import all service classes
from .request_validator import RequestValidator
from .response_builder import ResponseBuilder
from .chat_orchestrator import ChatOrchestrator
from .routing_manager import RoutingManager
from .provider_discovery import ProviderDiscoveryService
from .provider_scorer import ProviderScorer
from .provider_selector import ProviderSelector
from .fallback_handler import FallbackHandler
from .autoscaling_service import AutoscalingService
from backend.gateway_service import GatewayService
from .config_processor import ConfigProcessor
from .provider_factory import ProviderFactory

try:
    from .rag_processor import RAGProcessor
except Exception:
    # Provide a lightweight stub so the services package can be imported
    class RAGProcessor:
        def __init__(self, *a, **k):
            pass


# Cloud infrastructure services (optional)
try:
    from .model_storage import ModelStorageService
except ImportError:
    ModelStorageService = None

try:
    from .model_registry import ModelRegistry
except ImportError:
    ModelRegistry = None

try:
    from .inference_orchestrator import MultiProviderOrchestrator, RoutingStrategy
except ImportError:
    MultiProviderOrchestrator = None
    RoutingStrategy = None


from .scaling_processor import ScalingProcessor
from .verification_processor import VerificationProcessor
from .utils import Utils

# Import new refactored services
from .chat_validator import ChatValidator
from .chat_response_builder import ChatResponseBuilder
from .chat_error_handler import ChatErrorHandler
from .chat_rate_limiter import ChatRateLimiter
from .chat_session_manager import ChatSessionManager
from .chat_provider_selector import ChatProviderSelector
from .chat_metrics_collector import ChatMetricsCollector
from .chat_cache_manager import ChatCacheManager
from .chat_timeout_handler import ChatTimeoutHandler
from .chat_retry_handler import ChatRetryHandler
from .chat_compression_handler import ChatCompressionHandler
from .chat_response_formatter import ChatResponseFormatter
from .chat_error_formatter import ChatErrorFormatter
from .chat_controller_refactored import ChatController

logger = __import__("logging").getLogger(__name__)


class ServiceContainer:
    """Simple dependency injection container for services."""

    def __init__(self):
        """Initialize the service container."""
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, callable] = {}

    def register(self, service_name: str, service_instance: Any) -> None:
        """Register a service instance."""
        self._services[service_name] = service_instance
        logger.debug(f"Registered service: {service_name}")

    def register_factory(self, service_name: str, factory_func: callable) -> None:
        """Register a service factory function."""
        self._factories[service_name] = factory_func
        logger.debug(f"Registered factory: {service_name}")

    def get(self, service_name: str) -> Any:
        """Get a service instance."""
        if service_name in self._services:
            return self._services[service_name]

        if service_name in self._factories:
            # Create service instance using factory
            service_instance = self._factories[service_name]()
            self._services[service_name] = service_instance
            return service_instance

        raise ValueError(f"Service not found: {service_name}")

    def has(self, service_name: str) -> bool:
        """Check if a service is registered."""
        return service_name in self._services or service_name in self._factories

    def create_chat_orchestrator(self, db: Session) -> ChatOrchestrator:
        """Create a ChatOrchestrator with all dependencies."""
        # Get or create dependencies
        request_validator = self.get_or_create("request_validator")
        routing_service = self.get_or_create("routing_manager")
        gateway_service = self.get_or_create("gateway_service")
        scaling_processor = self.get_or_create("scaling_processor")
        verification_processor = self.get_or_create("verification_processor")
        response_builder = self.get_or_create("response_builder")
        config_processor = self.get_or_create("config_processor")
        provider_factory = self.get_or_create("provider_factory")
        rag_processor = self.get_or_create("rag_processor")

        return ChatOrchestrator(
            db=db,
            request_validator=request_validator,
            routing_service=routing_service,
            gateway_service=gateway_service,
            scaling_processor=scaling_processor,
            verification_processor=verification_processor,
            response_builder=response_builder,
            config_processor=config_processor,
            provider_factory=provider_factory,
            rag_processor=rag_processor,
        )

    def create_routing_manager(self, db: Session) -> RoutingManager:
        """Create a RoutingManager with all dependencies."""
        # Get or create dependencies
        provider_discovery = self.get_or_create("provider_discovery")
        provider_scorer = self.get_or_create("provider_scorer")
        provider_selector = self.get_or_create("provider_selector")
        fallback_handler = self.get_or_create("fallback_handler")
        autoscaling_service = self.get_or_create("autoscaling_service")
        gateway_service = self.get_or_create("gateway_service")

        return RoutingManager(
            db=db,
            provider_discovery=provider_discovery,
            provider_scorer=provider_scorer,
            provider_selector=provider_selector,
            fallback_handler=fallback_handler,
            autoscaling_service=autoscaling_service,
            gateway_service=gateway_service,
        )

    def get_or_create(self, service_name: str) -> Any:
        """Get a service or create it if it doesn't exist."""
        if self.has(service_name):
            return self.get(service_name)

        # Auto-create common services
        if service_name == "request_validator":
            service = RequestValidator()
            self.register(service_name, service)
            return service
        elif service_name == "response_builder":
            service = ResponseBuilder()
            self.register(service_name, service)
            return service
        elif service_name == "config_processor":
            service = ConfigProcessor()
            self.register(service_name, service)
            return service
        elif service_name == "provider_factory":
            service = ProviderFactory()
            self.register(service_name, service)
            return service
        elif service_name == "rag_processor":
            service = RAGProcessor()
            self.register(service_name, service)
            return service
        elif service_name == "scaling_processor":
            service = ScalingProcessor()
            self.register(service_name, service)
            return service
        elif service_name == "verification_processor":
            service = VerificationProcessor()
            self.register(service_name, service)
            return service
        elif service_name == "utils":
            service = Utils()
            self.register(service_name, service)
            return service

        raise ValueError(f"Unknown service: {service_name}")

    def initialize_all(self, db: Session) -> None:
        """Initialize all services with database session."""
        # Initialize core services that need database access
        self.create_routing_manager(db)
        self.create_chat_orchestrator(db)

        # Initialize other services that might need setup
        autoscaling_service = self.get_or_create("autoscaling_service")
        if hasattr(autoscaling_service, "initialize"):
            import asyncio

            asyncio.create_task(autoscaling_service.initialize())

        gateway_service = self.get_or_create("gateway_service")
        if hasattr(gateway_service, "initialize"):
            import asyncio

            asyncio.create_task(gateway_service.initialize())

        logger.info("All services initialized")


# Global service container instance
container = ServiceContainer()


def get_service(service_name: str) -> Any:
    """Get a service from the global container."""
    return container.get(service_name)


def get_or_create_service(service_name: str) -> Any:
    """Get a service or create it if it doesn't exist."""
    return container.get_or_create(service_name)


def register_service(service_name: str, service_instance: Any) -> None:
    """Register a service with the global container."""
    container.register(service_name, service_instance)


def register_factory(service_name: str, factory_func: callable) -> None:
    """Register a service factory with the global container."""
    container.register_factory(service_name, factory_func)


def initialize_services(db: Session) -> None:
    """Initialize all services with database session."""
    container.initialize_all(db)
