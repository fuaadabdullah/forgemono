"""
Raptor Model Adapter Layer
Unified interface for AI model backends in GoblinOS Assistant mini
"""

from .base import (
    ModelAdapter,
    ModelConfig,
    ModelResponse,
    ModelProvider,
    ModelCapability,
    ModelAdapterError,
    ModelMetrics,
)
from .local_model_adapter import LocalModelAdapter
from .raptor_api_adapter import RaptorApiAdapter
from .fallback_adapter import FallbackAdapter
from .dual_model_adapter import DualModelAdapter

__all__ = [
    # Base classes and types
    "ModelAdapter",
    "ModelConfig",
    "ModelResponse",
    "ModelProvider",
    "ModelCapability",
    "ModelAdapterError",
    "ModelMetrics",
    # Adapter implementations
    "LocalModelAdapter",
    "RaptorApiAdapter",
    "FallbackAdapter",
    "DualModelAdapter",
]
