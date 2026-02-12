"""
Unit tests for routing helper functions.

Tests the extracted helper functions from RoutingService to ensure
they work correctly and maintain the same behavior.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from services.routing_helpers import (
    handle_autoscaling_and_emergency_routing,
    handle_local_llm_routing,
    handle_provider_selection_and_fallback,
)


class TestRoutingHelpers:
    """Test routing helper functions."""

    @pytest.fixture
    def mock_autoscaling_service(self):
        """Mock autoscaling service."""
        service = Mock()
        service.check_rate_limit = AsyncMock()
        service.cheap_fallback_model = "gpt-3.5-turbo"
        return service

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return Mock()

    @pytest.mark.asyncio
    async def test_handle_autoscaling_rate_limit_exceeded(
        self, mock_autoscaling_service
    ):
        """Test autoscaling helper when rate limit is exceeded."""
        from services.autoscaling_service import FallbackLevel

        # Mock rate limit exceeded
        mock_autoscaling_service._check_autoscaling = AsyncMock(
            return_value={
                "allowed": False,
                "fallback_level": FallbackLevel.CHEAP_MODEL,
                "retry_after": 60,
                "emergency_endpoint": False,
            }
        )

        result = await handle_autoscaling_and_emergency_routing(
            mock_autoscaling_service,
            "chat",
            {"messages": []},
            "test-request-id",
            client_ip="127.0.0.1",
        )

        assert result["success"] is False
        assert result["error"] == "Rate limit exceeded"
        assert result["retry_after"] == 60
        assert result["request_id"] == "test-request-id"

    @pytest.mark.asyncio
    async def test_handle_autoscaling_emergency_routing(self, mock_autoscaling_service):
        """Test autoscaling helper triggers emergency routing."""
        from services.autoscaling_service import FallbackLevel

        # Mock emergency mode
        mock_autoscaling_service._check_autoscaling = AsyncMock(
            return_value={
                "allowed": True,
                "fallback_level": FallbackLevel.EMERGENCY,
                "retry_after": 0,
                "emergency_endpoint": False,
            }
        )

        result = await handle_autoscaling_and_emergency_routing(
            mock_autoscaling_service, "chat", {"messages": []}, "test-request-id"
        )

        assert result["emergency_routing"] is True
        assert result["capability"] == "chat"
        assert result["request_id"] == "test-request-id"

    @pytest.mark.asyncio
    async def test_handle_autoscaling_cheap_fallback(self, mock_autoscaling_service):
        """Test autoscaling helper applies cheap model fallback."""
        from services.autoscaling_service import FallbackLevel

        # Mock cheap model fallback
        mock_autoscaling_service._check_autoscaling = AsyncMock(
            return_value={
                "allowed": True,
                "fallback_level": FallbackLevel.CHEAP_MODEL,
                "retry_after": 0,
                "emergency_endpoint": False,
            }
        )

        result = await handle_autoscaling_and_emergency_routing(
            mock_autoscaling_service, "chat", {"messages": []}, "test-request-id"
        )

        assert result["continue_normal_routing"] is True
        assert result["requirements"]["model"] == "gpt-3.5-turbo"
        assert result["requirements"]["fallback_mode"] is True

    @pytest.mark.asyncio
    async def test_handle_local_llm_routing_non_chat(
        self, mock_autoscaling_service, mock_db_session
    ):
        """Test local LLM routing helper rejects non-chat requests."""
        result = await handle_local_llm_routing(
            mock_autoscaling_service,
            mock_db_session,
            "vision",  # Not chat
            {"messages": []},
            "test-request-id",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_handle_local_llm_routing_no_messages(
        self, mock_autoscaling_service, mock_db_session
    ):
        """Test local LLM routing helper rejects requests without messages."""
        result = await handle_local_llm_routing(
            mock_autoscaling_service,
            mock_db_session,
            "chat",
            {},  # No messages
            "test-request-id",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_handle_local_llm_routing_rate_limited(
        self, mock_autoscaling_service, mock_db_session
    ):
        """Test local LLM routing helper handles rate limiting."""
        from services.autoscaling_service import FallbackLevel

        # Mock rate limiting
        mock_autoscaling_service.check_rate_limit = AsyncMock(
            return_value=(
                False,  # allowed
                FallbackLevel.CHEAP_MODEL,  # fallback_level
                {"reason": "too_many_requests"},  # metadata
            )
        )

        result = await handle_local_llm_routing(
            mock_autoscaling_service,
            mock_db_session,
            "chat",
            {"messages": [{"role": "user", "content": "Hello"}]},
            "test-request-id",
        )

        assert result["error"] == "Rate limit exceeded"
        assert result["fallback_level"] == "CHEAP_MODEL"
        assert result["retry_after"] == 60

    @pytest.mark.asyncio
    @patch("services.routing_helpers.select_model")
    @patch("services.routing_helpers.detect_intent")
    @patch("services.routing_helpers.get_system_prompt")
    @patch("services.routing_helpers.get_routing_explanation")
    @patch("services.routing_helpers.get_context_length")
    async def test_handle_local_llm_routing_success(
        self,
        mock_get_context_length,
        mock_get_routing_explanation,
        mock_get_system_prompt,
        mock_detect_intent,
        mock_select_model,
        mock_autoscaling_service,
        mock_db_session,
    ):
        """Test successful local LLM routing."""
        from services.autoscaling_service import FallbackLevel

        # Mock dependencies
        mock_autoscaling_service.check_rate_limit = AsyncMock(
            return_value=(True, FallbackLevel.NORMAL, {})
        )
        mock_select_model.return_value = ("llama2:7b", {"temperature": 0.7})
        mock_detect_intent.return_value = Mock(value="general")
        mock_get_system_prompt.return_value = "You are a helpful assistant."
        mock_get_routing_explanation.return_value = "Using local LLM for efficiency"
        mock_get_context_length.return_value = 100

        # Mock Ollama provider
        mock_provider = Mock()
        mock_provider.id = 1
        mock_provider.name = "goblin-ollama-server"
        mock_provider.display_name = "Ollama Server"
        mock_provider.base_url = "http://localhost:11434"
        mock_provider.capabilities = ["chat"]
        mock_provider.priority = 1
        mock_provider.is_active = True

        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_provider
        )

        result = await handle_local_llm_routing(
            mock_autoscaling_service,
            mock_db_session,
            "chat",
            {"messages": [{"role": "user", "content": "Hello"}]},
            "test-request-id",
        )

        assert result is not None
        assert result["provider"]["id"] == 1
        assert result["provider"]["model"] == "llama2:7b"
        assert result["params"]["temperature"] == 0.7
        assert result["system_prompt"] == "You are a helpful assistant."
        assert result["explanation"] == "Using local LLM for efficiency"

    @pytest.mark.asyncio
    async def test_handle_provider_selection_no_candidates(self):
        """Test provider selection when no candidates are available."""
        mock_routing_service = Mock()
        mock_routing_service._find_suitable_providers = AsyncMock(return_value=[])

        result = await handle_provider_selection_and_fallback(
            mock_routing_service, "chat", {}, "test-request-id"
        )

        assert result["success"] is False
        assert "No providers available" in result["error"]

    @pytest.mark.asyncio
    async def test_handle_provider_selection_with_fallback(self):
        """Test provider selection uses fallback when needed."""
        mock_routing_service = Mock()
        mock_routing_service._find_suitable_providers = AsyncMock(
            return_value=[{"id": 1}]
        )
        mock_routing_service._should_use_fallback = AsyncMock(return_value=True)
        mock_routing_service._get_fallback_provider = AsyncMock(
            return_value={"id": 2, "display_name": "Fallback Provider"}
        )
        mock_routing_service._log_routing_request = AsyncMock()

        result = await handle_provider_selection_and_fallback(
            mock_routing_service, "chat", {}, "test-request-id"
        )

        assert result["success"] is True
        assert result["provider"]["id"] == 2
        assert result["is_fallback"] is True
        assert result["fallback_reason"] == "latency_sla_violation"

    @pytest.mark.asyncio
    async def test_handle_provider_selection_normal_selection(self):
        """Test normal provider selection without fallback."""
        mock_routing_service = Mock()
        mock_routing_service._find_suitable_providers = AsyncMock(
            return_value=[{"id": 1}]
        )
        mock_routing_service._should_use_fallback = AsyncMock(return_value=False)
        mock_routing_service._score_providers = AsyncMock(
            return_value=[{"id": 1, "name": "test-provider"}]
        )
        mock_routing_service._log_routing_request = AsyncMock()

        result = await handle_provider_selection_and_fallback(
            mock_routing_service, "chat", {}, "test-request-id"
        )

        assert result["success"] is True
        assert result["provider"]["id"] == 1
        assert result["is_fallback"] is False
