"""
Raptor Model Adapter Base Interface
Unified interface for AI model backends in GoblinOS Assistant mini
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum


class ModelProvider(Enum):
    """Supported AI model providers"""

    LOCAL_LLAMA = "local_llama"
    RAPTOR_API = "raptor_api"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROQ = "groq"
    FALLBACK = "fallback"


class ModelCapability(Enum):
    """Model capabilities"""

    TEXT_GENERATION = "text_generation"
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    DOCUMENTATION = "documentation"
    CHAT = "chat"


@dataclass
class ModelConfig:
    """Configuration for a model adapter"""

    provider: ModelProvider
    model_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout: int = 30
    capabilities: List[ModelCapability] = None

    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = [ModelCapability.TEXT_GENERATION]


@dataclass
class ModelResponse:
    """Response from a model adapter"""

    content: str
    provider: ModelProvider
    model_name: str
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ModelMetrics:
    """Performance metrics for model operations"""

    request_count: int = 0
    total_tokens: int = 0
    total_latency: float = 0.0
    error_count: int = 0
    last_error: Optional[str] = None

    @property
    def average_latency(self) -> float:
        """Calculate average latency per request"""
        return self.total_latency / max(self.request_count, 1)

    @property
    def error_rate(self) -> float:
        """Calculate error rate"""
        return self.error_count / max(self.request_count, 1)


class ModelAdapterError(Exception):
    """Base exception for model adapter errors"""

    def __init__(self, message: str, provider: ModelProvider, recoverable: bool = True):
        super().__init__(message)
        self.provider = provider
        self.recoverable = recoverable


class ModelAdapter(ABC):
    """
    Abstract base class for AI model adapters.
    All model backends must implement this interface.
    """

    def __init__(self, config: ModelConfig):
        self.config = config
        self.metrics = ModelMetrics()
        self._initialized = False

    @property
    def provider(self) -> ModelProvider:
        """Get the model provider type"""
        return self.config.provider

    @property
    def is_initialized(self) -> bool:
        """Check if adapter is properly initialized"""
        return self._initialized

    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the model adapter.
        Must be called before using the adapter.

        Returns:
            bool: True if initialization successful
        """
        pass

    @abstractmethod
    async def generate(
        self, prompt: str, context: Optional[Dict[str, Any]] = None, **kwargs
    ) -> ModelResponse:
        """
        Generate text using the model.

        Args:
            prompt: The input prompt
            context: Additional context for generation
            **kwargs: Additional model-specific parameters

        Returns:
            ModelResponse: The generated response

        Raises:
            ModelAdapterError: If generation fails
        """
        pass

    @abstractmethod
    async def generate_code(
        self,
        task: str,
        language: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> ModelResponse:
        """
        Generate code for a specific task.

        Args:
            task: Description of the coding task
            language: Programming language
            context: Additional context
            **kwargs: Additional parameters

        Returns:
            ModelResponse: Code generation response
        """
        pass

    @abstractmethod
    async def review_code(
        self,
        code: str,
        language: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> ModelResponse:
        """
        Review code and provide feedback.

        Args:
            code: Code to review
            language: Programming language
            context: Additional context
            **kwargs: Additional parameters

        Returns:
            ModelResponse: Code review response
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the model adapter is healthy and operational.

        Returns:
            bool: True if healthy
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """
        Clean up resources used by the adapter.
        Should be called when shutting down.
        """
        pass

    def supports_capability(self, capability: ModelCapability) -> bool:
        """Check if adapter supports a specific capability"""
        return capability in self.config.capabilities

    def get_metrics(self) -> ModelMetrics:
        """Get current performance metrics"""
        return self.metrics

    def reset_metrics(self) -> None:
        """Reset performance metrics"""
        self.metrics = ModelMetrics()

    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.cleanup()
