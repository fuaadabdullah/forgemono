"""
Tests for unified provider interface.
"""

import pytest

from ..base import ProviderBase, HealthStatus, InferenceRequest, InferenceResult
from ..registry import ProviderRegistry


class MockProvider(ProviderBase):
    """Mock provider for testing the interface."""

    def __init__(self, provider_id="mock", healthy=True):
        self._provider_id = provider_id
        self._healthy = healthy
        self._capabilities = {
            "models": ["mock-model"],
            "max_tokens": {"mock-model": 4096},
            "supports_streaming": True,
            "supports_vision": False,
            "cost_per_token_input": 0.001,
            "cost_per_token_output": 0.002,
        }

    @property
    def provider_id(self) -> str:
        return self._provider_id

    @property
    def capabilities(self):
        return self._capabilities

    def health_check(self) -> HealthStatus:
        return HealthStatus.HEALTHY if self._healthy else HealthStatus.UNHEALTHY

    def infer(self, request: InferenceRequest) -> InferenceResult:
        return InferenceResult(
            content="Mock response",
            usage={"input_tokens": 10, "output_tokens": 20, "total_tokens": 30},
            model=request.model,
            finish_reason="stop",
            latency_ms=100,
            success=True,
        )

    def estimate_cost(self, request: InferenceRequest) -> float:
        input_cost = 10 * self._capabilities["cost_per_token_input"]
        output_cost = 20 * self._capabilities["cost_per_token_output"]
        return input_cost + output_cost


class TestProviderBase:
    """Test the ProviderBase interface contract."""

    def test_mock_provider_implements_interface(self):
        """Test that MockProvider correctly implements ProviderBase."""
        provider = MockProvider()

        assert provider.provider_id == "mock"
        assert isinstance(provider.capabilities, dict)
        assert provider.capabilities["models"] == ["mock-model"]

        health = provider.health_check()
        assert isinstance(health, HealthStatus)

        request = InferenceRequest(
            messages=[{"role": "user", "content": "Hello"}], model="mock-model"
        )

        result = provider.infer(request)
        assert isinstance(result, InferenceResult)
        assert result.content == "Mock response"
        assert result.success is True

        cost = provider.estimate_cost(request)
        assert isinstance(cost, float)
        assert cost > 0

    def test_health_status_enum(self):
        """Test HealthStatus enum values."""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"

    def test_inference_request_creation(self):
        """Test InferenceRequest dataclass."""
        request = InferenceRequest(
            messages=[{"role": "user", "content": "Test"}],
            model="test-model",
            temperature=0.7,
            max_tokens=100,
            stream=True,
        )

        assert request.messages == [{"role": "user", "content": "Test"}]
        assert request.model == "test-model"
        assert request.temperature == 0.7
        assert request.max_tokens == 100
        assert request.stream is True

    def test_inference_result_creation(self):
        """Test InferenceResult dataclass."""
        result = InferenceResult(
            content="Response",
            usage={"input_tokens": 5, "output_tokens": 10, "total_tokens": 15},
            model="test-model",
            finish_reason="stop",
            latency_ms=50,
            success=True,
        )

        assert result.content == "Response"
        assert result.usage["total_tokens"] == 15
        assert result.model == "test-model"
        assert result.finish_reason == "stop"
        assert result.latency_ms == 50
        assert result.success is True


class TestProviderRegistry:
    """Test the ProviderRegistry functionality."""

    def test_registry_initialization(self):
        """Test that registry initializes without errors."""
        # This will test with default config since we don't have actual providers
        registry = ProviderRegistry()

        # Should not crash
        providers = registry.get_available_providers()
        assert isinstance(providers, list)

    def test_get_provider(self):
        """Test getting a specific provider."""
        registry = ProviderRegistry()

        # Mock provider won't be loaded since it's not in config
        provider = registry.get_provider("nonexistent")
        assert provider is None

    def test_get_providers_by_capability(self):
        """Test filtering providers by capability."""
        registry = ProviderRegistry()

        providers = registry.get_providers_by_capability("streaming")
        assert isinstance(providers, list)

    def test_get_providers_for_model(self):
        """Test finding providers for a specific model."""
        registry = ProviderRegistry()

        providers = registry.get_providers_for_model("gpt-4")
        assert isinstance(providers, list)


if __name__ == "__main__":
    pytest.main([__file__])
