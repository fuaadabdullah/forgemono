"""
Unit tests for model routing logic.

Tests routing decisions without external API calls.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from services.routing_compat import RoutingServiceCompat as RoutingService


class TestRoutingService:
    """Test routing service logic."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()

    @pytest.fixture
    def routing_service(self, mock_db):
        """Create routing service with mocked dependencies."""
        # Use a valid Fernet key for testing
        test_key = "zK5sJCSNGUiCNBmYzvmzUDVemPOUZYKUdZFpJPH2hbk="
        service = RoutingService(mock_db, test_key)
        return service

    @pytest.mark.asyncio
    async def test_route_request_simple_chat(self, routing_service):
        """Test routing for simple chat requests."""
        # Mock the database query
        mock_provider = Mock()
        mock_provider.id = 1
        mock_provider.name = "openai"
        mock_provider.display_name = "OpenAI"
        mock_provider.capabilities = ["chat"]
        mock_provider.is_active = True
        mock_provider.priority = 1
        mock_provider.api_key_encrypted = "encrypted_key"
        mock_provider.base_url = "https://api.openai.com"

        routing_service.db.query.return_value.filter.return_value.all.return_value = [
            mock_provider
        ]

        # Mock encryption service
        routing_service.encryption_service.decrypt = Mock(return_value="api_key")

        # Mock adapter
        mock_adapter = AsyncMock()
        mock_adapter.list_models.return_value = ["gpt-3.5-turbo"]
        routing_service.adapters = {"openai": Mock(return_value=mock_adapter)}

        # Mock local LLM routing to return None (use cloud providers)
        routing_service._try_local_llm_routing = AsyncMock(return_value=None)

        # Mock provider scoring
        routing_service._find_suitable_providers = AsyncMock(
            return_value=[
                {
                    "id": 1,
                    "name": "openai",
                    "capabilities": ["chat"],
                    "models": ["gpt-3.5-turbo"],
                }
            ]
        )
        routing_service._score_and_rank_providers = AsyncMock(
            return_value=[
                {"id": 1, "name": "openai", "score": 100, "models": ["gpt-3.5-turbo"]}
            ]
        )

        # Test routing
        result = await routing_service.route_request("chat", {"message": "Hello world"})

        assert result["success"] is True
        assert "provider" in result
        assert result["capability"] == "chat"

    @pytest.mark.asyncio
    async def test_route_request_with_local_routing(self, routing_service):
        """Test routing that prefers local LLMs when available."""
        # Mock local LLM routing to return a result
        local_result = {
            "provider": "ollama",
            "provider_id": 2,
            "explanation": "Using local LLM for efficiency",
            "params": {"model": "llama2"},
            "system_prompt": "You are a helpful assistant",
        }
        routing_service._try_local_llm_routing = AsyncMock(return_value=local_result)

        result = await routing_service.route_request(
            "chat", {"message": "Simple question"}
        )

        assert result["success"] is True
        assert result["provider"] == "ollama"
        assert result["routing_explanation"] == "Using local LLM for efficiency"

    @pytest.mark.asyncio
    async def test_route_request_no_providers(self, routing_service):
        """Test routing when no suitable providers are available."""
        # Mock no local routing and no suitable providers
        routing_service._try_local_llm_routing = AsyncMock(return_value=None)
        routing_service._find_suitable_providers = AsyncMock(return_value=[])

        result = await routing_service.route_request("chat", {"message": "Test"})

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_discover_providers(self, routing_service):
        """Test provider discovery functionality."""
        # Mock database query
        mock_provider = Mock()
        mock_provider.id = 1
        mock_provider.name = "openai"
        mock_provider.display_name = "OpenAI"
        mock_provider.capabilities = ["chat", "vision"]
        mock_provider.is_active = True
        mock_provider.priority = 1
        mock_provider.api_key_encrypted = "encrypted_key"
        mock_provider.base_url = "https://api.openai.com"

        routing_service.db.query.return_value.filter.return_value.all.return_value = [
            mock_provider
        ]

        # Mock encryption and adapter
        routing_service.encryption_service.decrypt = Mock(return_value="api_key")
        mock_adapter = AsyncMock()
        mock_adapter.list_models.return_value = ["gpt-4", "gpt-3.5-turbo"]
        routing_service.adapters = {"openai": Mock(return_value=mock_adapter)}

        result = await routing_service.discover_providers()

        assert len(result) == 1
        assert result[0]["name"] == "openai"
        assert result[0]["models"] == ["gpt-4", "gpt-3.5-turbo"]
        assert result[0]["capabilities"] == ["chat", "vision"]
