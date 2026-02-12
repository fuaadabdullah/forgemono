import importlib
import sys
import types
from enum import Enum


def _stub_module(name: str, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    return module


def test_chat_router_import_without_routing_key(monkeypatch):
    monkeypatch.delenv("ROUTING_ENCRYPTION_KEY", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "development")

    services_pkg = _stub_module("services")
    services_pkg.__path__ = []
    sys.modules["services"] = services_pkg
    sys.modules["services.routing"] = _stub_module(
        "services.routing", RoutingService=object
    )
    sys.modules["services.output_verification"] = _stub_module(
        "services.output_verification", VerificationPipeline=object
    )
    sys.modules["services.rag_service"] = _stub_module(
        "services.rag_service", RAGService=object
    )
    sys.modules["services.inference_scaling_service"] = _stub_module(
        "services.inference_scaling_service", InferenceScalingService=object
    )
    sys.modules["services.latency_monitoring_service"] = _stub_module(
        "services.latency_monitoring_service", LatencyMonitoringService=object
    )
    sys.modules["services.routing_compat"] = _stub_module(
        "services.routing_compat",
        get_routing_service_compat=lambda: None,
    )
    sys.modules["services.config_processor"] = _stub_module(
        "services.config_processor",
        get_routing_encryption_key=lambda: None,
    )

    sys.modules["gateway_service"] = _stub_module(
        "gateway_service",
        get_gateway_service=lambda: None,
        TokenBudgetExceeded=RuntimeError,
        MaxTokensExceeded=RuntimeError,
    )

    class _AuthScope(Enum):
        WRITE_CONVERSATIONS = "write:conversations"

    auth_pkg = _stub_module("auth")
    auth_pkg.__path__ = []
    sys.modules["auth"] = auth_pkg
    sys.modules["auth.policies"] = _stub_module("auth.policies", AuthScope=_AuthScope)
    sys.modules["auth_service"] = _stub_module(
        "auth_service", get_auth_service=lambda: None
    )

    sys.modules["providers"] = _stub_module(
        "providers",
        OllamaAdapter=object,
        LlamaCppAdapter=object,
        GrokAdapter=object,
        OpenAIAdapter=object,
        AnthropicAdapter=object,
        DeepSeekAdapter=object,
    )
    sys.modules["errors"] = _stub_module(
        "errors",
        raise_validation_error=lambda *args, **kwargs: None,
        raise_internal_error=lambda *args, **kwargs: None,
        raise_service_unavailable=lambda *args, **kwargs: None,
        raise_problem=lambda *args, **kwargs: None,
    )

    sys.modules.pop("chat_router", None)
    module = importlib.import_module("chat_router")

    assert hasattr(module, "router")
