"""
Unit tests for the refactored chat services.

This test suite validates the functionality of all extracted services
and ensures they work correctly in isolation.
"""

import pytest
import asyncio
import time
import json
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, AsyncMock, patch

# Import the services
from backend.services.chat_validator import (
    ChatValidator,
    ValidationConfig,
    ValidationResult,
)
from backend.services.chat_response_builder import (
    ChatResponseBuilder,
    ResponseBuilderConfig,
)
from backend.services.chat_error_handler import ChatErrorHandler, ErrorHandlerConfig
from backend.services.chat_rate_limiter import (
    ChatRateLimiter,
    RateLimitConfig,
    RateLimitResult,
)
from backend.services.chat_session_manager import (
    ChatSessionManager,
    SessionConfig,
    SessionState,
)
from backend.services.chat_provider_selector import (
    ChatProviderSelector,
    ProviderConfig,
    ProviderPriority,
)
from backend.services.chat_metrics_collector import (
    ChatMetricsCollector,
    RequestMetrics,
    SessionMetrics,
)
from backend.services.chat_cache_manager import ChatCacheManager, CacheType, CacheEntry
from backend.services.chat_timeout_handler import (
    ChatTimeoutHandler,
    TimeoutConfig,
    TimeoutType,
)
from backend.services.chat_retry_handler import (
    ChatRetryHandler,
    RetryConfig,
    RetryStrategy,
)
from backend.services.chat_compression_handler import (
    ChatCompressionHandler,
    CompressionConfig,
    CompressionType,
)
from backend.services.chat_response_formatter import (
    ChatResponseFormatter,
    ResponseFormatConfig,
    ResponseFormat,
)
from backend.services.chat_error_formatter import (
    ChatErrorFormatter,
    ErrorFormatConfig,
    ErrorSeverity,
    ErrorCategory,
)
from backend.services.chat_controller_refactored import (
    ChatController,
    ChatRequest,
    ChatResponse,
    ChatState,
)


class TestChatValidator:
    """Test cases for ChatValidator service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = ChatValidator()

    @pytest.mark.asyncio
    async def test_validate_request_valid(self):
        """Test validation of a valid request."""
        request = ChatRequest(
            session_id="test_session",
            messages=[{"role": "user", "content": "Hello"}],
            model="gpt-4",
            temperature=0.7,
            max_tokens=100,
            stream=False,
        )

        result = await self.validator.validate_request(request)

        assert result.is_valid is True
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_validate_request_invalid_messages(self):
        """Test validation of request with invalid messages."""
        request = ChatRequest(
            session_id="test_session",
            messages=[{"role": "invalid", "content": "Hello"}],
            model="gpt-4",
        )

        result = await self.validator.validate_request(request)

        assert result.is_valid is False
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_validate_request_missing_session_id(self):
        """Test validation of request with missing session ID."""
        request = ChatRequest(
            session_id="",
            messages=[{"role": "user", "content": "Hello"}],
            model="gpt-4",
        )

        result = await self.validator.validate_request(request)

        assert result.is_valid is False
        assert any("session_id" in error["field"] for error in result.errors)

    def test_get_stats(self):
        """Test getting validation statistics."""
        stats = self.validator.get_stats()

        assert "total_validations" in stats
        assert "valid_requests" in stats
        assert "invalid_requests" in stats
        assert "validation_errors" in stats


class TestChatResponseBuilder:
    """Test cases for ChatResponseBuilder service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.builder = ChatResponseBuilder()

    @pytest.mark.asyncio
    async def test_build_provider_request(self):
        """Test building a provider request."""
        request = ChatRequest(
            session_id="test_session",
            messages=[{"role": "user", "content": "Hello"}],
            model="gpt-4",
            temperature=0.7,
            max_tokens=100,
        )

        session = Mock()
        session.context = {"key": "value"}
        session.history = []

        provider = Mock()
        provider.name = "test_provider"

        provider_request = await self.builder.build_provider_request(
            request, session, provider
        )

        assert "messages" in provider_request
        assert "model" in provider_request
        assert "temperature" in provider_request
        assert "max_tokens" in provider_request

    @pytest.mark.asyncio
    async def test_build_response_data(self):
        """Test building response data."""
        response_data = await self.builder.build_response_data(
            request_id="test_request",
            provider_info={"name": "test_provider"},
            model="gpt-4",
            response_text="Hello world",
            routing_result={"provider": {"name": "test_provider"}},
            response_time_ms=100,
            tokens_used=50,
            success=True,
        )

        assert "request_id" in response_data
        assert "provider" in response_data
        assert "model" in response_data
        assert "response_text" in response_data
        assert "response_time_ms" in response_data
        assert "tokens_used" in response_data
        assert "success" in response_data

    def test_get_stats(self):
        """Test getting response builder statistics."""
        stats = self.builder.get_stats()

        assert "total_builds" in stats
        assert "successful_builds" in stats
        assert "failed_builds" in stats


class TestChatErrorHandler:
    """Test cases for ChatErrorHandler service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = ChatErrorHandler()

    @pytest.mark.asyncio
    async def test_handle_validation_error(self):
        """Test handling validation errors."""
        error = ValueError("Validation failed")
        request_id = "test_request"
        session_id = "test_session"

        result = await self.handler.handle_validation_error(
            error, request_id, session_id
        )

        assert "error" in result
        assert "error_type" in result
        assert "timestamp" in result
        assert result["request_id"] == request_id
        assert result["session_id"] == session_id

    @pytest.mark.asyncio
    async def test_handle_provider_error(self):
        """Test handling provider errors."""
        error = ConnectionError("Provider unavailable")
        request_id = "test_request"
        provider_name = "test_provider"

        result = await self.handler.handle_provider_error(
            error, request_id, provider_name
        )

        assert "error" in result
        assert "provider_name" in result
        assert result["provider_name"] == provider_name

    def test_get_stats(self):
        """Test getting error handler statistics."""
        stats = self.handler.get_stats()

        assert "total_errors" in stats
        assert "validation_errors" in stats
        assert "provider_errors" in stats
        assert "system_errors" in stats


class TestChatRateLimiter:
    """Test cases for ChatRateLimiter service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.limiter = ChatRateLimiter()

    @pytest.mark.asyncio
    async def test_check_rate_limit_allowed(self):
        """Test rate limit check that allows request."""
        result = await self.limiter.check_rate_limit("user123", "gpt-4", "request123")

        assert isinstance(result, RateLimitResult)
        assert result.allowed is True

    @pytest.mark.asyncio
    async def test_check_rate_limit_denied(self):
        """Test rate limit check that denies request."""
        # Mock the rate limiting logic to return False
        with patch.object(self.limiter, "_check_user_rate_limit", return_value=False):
            result = await self.limiter.check_rate_limit(
                "user123", "gpt-4", "request123"
            )

            assert isinstance(result, RateLimitResult)
            assert result.allowed is False

    def test_get_stats(self):
        """Test getting rate limiter statistics."""
        stats = self.limiter.get_stats()

        assert "total_checks" in stats
        assert "allowed_requests" in stats
        assert "denied_requests" in stats
        assert "blocked_users" in stats


class TestChatSessionManager:
    """Test cases for ChatSessionManager service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = ChatSessionManager()

    @pytest.mark.asyncio
    async def test_get_or_create_session(self):
        """Test getting or creating a session."""
        session = await self.manager.get_or_create_session(
            "test_session", "user123", "127.0.0.1"
        )

        assert session is not None
        assert session.session_id == "test_session"
        assert session.user_id == "user123"
        assert session.client_ip == "127.0.0.1"

    @pytest.mark.asyncio
    async def test_update_session_with_request(self):
        """Test updating session with request data."""
        messages = [{"role": "user", "content": "Hello"}]

        await self.manager.update_session_with_request(
            "test_session", messages, "gpt-4", 0.7, 100
        )

        session = await self.manager.get_session("test_session")
        assert session is not None
        assert len(session.history) == 1
        assert session.last_model == "gpt-4"

    def test_get_stats(self):
        """Test getting session manager statistics."""
        stats = self.manager.get_stats()

        assert "total_sessions" in stats
        assert "active_sessions" in stats
        assert "expired_sessions" in stats
        assert "session_operations" in stats


class TestChatProviderSelector:
    """Test cases for ChatProviderSelector service."""

    def setup_method(self):
        """Set up test fixtures."""
        providers = [
            ProviderConfig(
                name="provider1",
                model="gpt-4",
                priority=ProviderPriority.HIGH,
                enabled=True,
                weight=1.0,
            ),
            ProviderConfig(
                name="provider2",
                model="gpt-3.5-turbo",
                priority=ProviderPriority.MEDIUM,
                enabled=True,
                weight=1.0,
            ),
        ]
        self.selector = ChatProviderSelector(providers)

    @pytest.mark.asyncio
    async def test_select_provider(self):
        """Test provider selection."""
        messages = [{"role": "user", "content": "Hello"}]
        session = Mock()

        provider = await self.selector.select_provider("gpt-4", messages, session)

        assert provider is not None
        assert provider.name in ["provider1", "provider2"]

    def test_get_stats(self):
        """Test getting provider selector statistics."""
        stats = self.selector.get_stats()

        assert "provider_scores" in stats
        assert "provider_usage" in stats
        assert "provider_errors" in stats
        assert "provider_response_times" in stats


class TestChatMetricsCollector:
    """Test cases for ChatMetricsCollector service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.collector = ChatMetricsCollector()

    @pytest.mark.asyncio
    async def test_start_request(self):
        """Test starting metrics collection for a request."""
        request_data = {
            "session_id": "test_session",
            "user_id": "user123",
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 100,
            "stream": False,
        }

        self.collector.start_request("test_request", request_data)

        request_metrics = self.collector.get_request_metrics("test_request")
        assert request_metrics is not None
        assert request_metrics.request_id == "test_request"
        assert request_metrics.session_id == "test_session"

    @pytest.mark.asyncio
    async def test_update_response_metrics(self):
        """Test updating metrics with response data."""
        response = {
            "choices": [{"message": {"content": "Hello world"}}],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15,
            },
        }

        self.collector.update_response_metrics("test_request", response, "provider1")

        request_metrics = self.collector.get_request_metrics("test_request")
        assert request_metrics.success is True
        assert request_metrics.tokens_processed == 10
        assert request_metrics.tokens_generated == 5
        assert request_metrics.total_tokens == 15

    def test_get_system_metrics(self):
        """Test getting system-wide metrics."""
        metrics = self.collector.get_system_metrics()

        assert "total_requests" in metrics
        assert "total_tokens" in metrics
        assert "success_rate" in metrics
        assert "error_rate" in metrics


class TestChatCacheManager:
    """Test cases for ChatCacheManager service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.cache = ChatCacheManager()

    def test_set_and_get(self):
        """Test setting and getting cache entries."""
        key = "test_key"
        value = {"response": "Hello world"}

        result = self.cache.set(key, value, CacheType.RESPONSE)
        assert result is True

        retrieved_value = self.cache.get(key, CacheType.RESPONSE)
        assert retrieved_value == value

    def test_cache_expiration(self):
        """Test cache entry expiration."""
        key = "test_key"
        value = {"response": "Hello world"}

        # Set with short TTL
        self.cache.set(key, value, CacheType.RESPONSE, ttl_seconds=1)

        # Should be available immediately
        retrieved_value = self.cache.get(key, CacheType.RESPONSE)
        assert retrieved_value == value

        # Wait for expiration
        time.sleep(2)

        # Should be expired
        retrieved_value = self.cache.get(key, CacheType.RESPONSE)
        assert retrieved_value is None

    def test_get_stats(self):
        """Test getting cache statistics."""
        stats = self.cache.get_stats()

        assert "entries" in stats
        assert "total_size" in stats
        assert "hit_rate" in stats
        assert "hits" in stats
        assert "misses" in stats


class TestChatTimeoutHandler:
    """Test cases for ChatTimeoutHandler service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = ChatTimeoutHandler()

    @pytest.mark.asyncio
    async def test_timeout_context(self):
        """Test timeout context manager."""

        async def long_running_task():
            await asyncio.sleep(0.1)
            return "completed"

        async with self.handler.timeout_context(
            "test_request", TimeoutType.REQUEST, 1.0
        ):
            result = await long_running_task()
            assert result == "completed"

    @pytest.mark.asyncio
    async def test_timeout_expiration(self):
        """Test timeout expiration."""

        async def long_running_task():
            await asyncio.sleep(2.0)
            return "completed"

        with pytest.raises(asyncio.TimeoutError):
            async with self.handler.timeout_context(
                "test_request", TimeoutType.REQUEST, 0.1
            ):
                await long_running_task()

    def test_get_stats(self):
        """Test getting timeout statistics."""
        stats = self.handler.get_stats()

        assert "total_requests" in stats
        assert "timeouts_triggered" in stats
        assert "timeouts_cancelled" in stats
        assert "timeout_rate" in stats


class TestChatRetryHandler:
    """Test cases for ChatRetryHandler service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = ChatRetryHandler()

    @pytest.mark.asyncio
    async def test_retry_with_success(self):
        """Test retry that succeeds on first attempt."""

        async def successful_task():
            return "success"

        result = await self.handler.retry_with_strategy(
            successful_task, request_id="test_request"
        )
        assert result == "success"

    @pytest.mark.asyncio
    async def test_retry_with_failure(self):
        """Test retry that eventually fails."""
        attempt_count = 0

        async def failing_task():
            nonlocal attempt_count
            attempt_count += 1
            raise ValueError("Task failed")

        with pytest.raises(ValueError):
            await self.handler.retry_with_strategy(
                failing_task, request_id="test_request"
            )

        assert attempt_count > 1  # Should have retried

    def test_get_stats(self):
        """Test getting retry statistics."""
        stats = self.handler.get_stats()

        assert "total_retries" in stats
        assert "successful_retries" in stats
        assert "failed_retries" in stats
        assert "success_rate" in stats


class TestChatCompressionHandler:
    """Test cases for ChatCompressionHandler service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = ChatCompressionHandler()

    def test_compress_and_decompress(self):
        """Test compression and decompression."""
        data = {"message": "Hello world" * 100}  # Make it large enough to compress

        compressed = self.handler.compress_response(data)
        assert isinstance(compressed, bytes)

        decompressed = self.handler.decompress_response(compressed)
        assert isinstance(decompressed, bytes)

    def test_should_compress(self):
        """Test compression decision logic."""
        small_data = b"small"
        large_data = b"large" * 1000

        assert self.handler.should_compress(len(small_data)) is False
        assert self.handler.should_compress(len(large_data)) is True

    def test_get_stats(self):
        """Test getting compression statistics."""
        stats = self.handler.get_stats()

        assert "total_compressed" in stats
        assert "total_uncompressed" in stats
        assert "compression_ratio" in stats
        assert "compression_time" in stats


class TestChatResponseFormatter:
    """Test cases for ChatResponseFormatter service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = ChatResponseFormatter()

    def test_format_json_response(self):
        """Test formatting JSON response."""
        response_data = {"message": "Hello world"}

        formatted = self.formatter.format_response(
            response_data,
            ResponseFormat.JSON,
            "test_request",
            "test_session",
            "provider1",
        )

        assert formatted.format_type == ResponseFormat.JSON
        assert "message" in formatted.content

    def test_format_stream_response(self):
        """Test formatting stream response."""
        chunk_data = {"content": "Hello"}

        formatted = self.formatter.format_stream_response(
            chunk_data, 1, 5, "test_request", "test_session"
        )

        assert isinstance(formatted, str)
        assert "chunk_index" in formatted

    def test_get_headers(self):
        """Test getting response headers."""
        headers = self.formatter.get_response_headers(ResponseFormat.JSON)
        assert "Content-Type" in headers
        assert headers["Content-Type"] == "application/json"


class TestChatErrorFormatter:
    """Test cases for ChatErrorFormatter service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = ChatErrorFormatter()

    def test_format_validation_error(self):
        """Test formatting validation error."""
        validation_errors = [{"field": "model", "message": "Invalid model"}]

        formatted = self.formatter.format_validation_error(
            validation_errors, "test_request", "test_session"
        )

        assert formatted.error_type == "ValueError"
        assert formatted.category == ErrorCategory.VALIDATION
        assert "Validation failed" in formatted.error_message

    def test_format_provider_error(self):
        """Test formatting provider error."""
        provider_error = ConnectionError("Provider unavailable")

        formatted = self.formatter.format_provider_error(
            "provider1", provider_error, "test_request", "test_session"
        )

        assert formatted.error_type == "ConnectionError"
        assert formatted.category == ErrorCategory.PROVIDER
        assert "Provider unavailable" in formatted.error_message

    def test_get_stats(self):
        """Test getting error formatter statistics."""
        stats = self.formatter.get_stats()

        assert "config" in stats
        assert "timestamp" in stats


class TestChatController:
    """Test cases for ChatController service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.controller = ChatController()

    @pytest.mark.asyncio
    async def test_handle_chat_request_valid(self):
        """Test handling a valid chat request."""
        request = ChatRequest(
            session_id="test_session",
            messages=[{"role": "user", "content": "Hello"}],
            model="gpt-4",
            temperature=0.7,
            max_tokens=100,
            stream=False,
        )

        # Mock the services to return successful results
        with (
            patch.object(
                self.controller.validator, "validate_request"
            ) as mock_validate,
            patch.object(
                self.controller.rate_limiter, "check_rate_limit"
            ) as mock_rate_limit,
            patch.object(
                self.controller.session_manager, "get_or_create_session"
            ) as mock_session,
            patch.object(
                self.controller.provider_selector, "select_provider"
            ) as mock_provider,
            patch.object(
                self.controller.response_builder, "build_provider_request"
            ) as mock_build,
            patch.object(
                self.controller.metrics_collector, "update_response_metrics"
            ) as mock_metrics,
            patch.object(
                self.controller.response_formatter, "format_response"
            ) as mock_format,
        ):
            # Setup mocks
            mock_validate.return_value = Mock(is_valid=True, errors=[])
            mock_rate_limit.return_value = Mock(allowed=True)
            mock_session.return_value = Mock()
            provider_mock = Mock(name="test_provider")
            provider_mock.chat_completion = AsyncMock(
                return_value={"content": "Hello world", "usage": {"total_tokens": 50}}
            )
            mock_provider.return_value = provider_mock
            mock_build.return_value = {"messages": [], "model": "gpt-4"}
            mock_format.return_value = Mock(
                content="Hello world", format_type=ResponseFormat.JSON
            )

            # Execute
            result = await self.controller.handle_chat_request(request, "test_request")

            # Verify
            assert isinstance(result, ChatResponse)
            assert result.content == "Hello world"

    @pytest.mark.asyncio
    async def test_handle_chat_request_validation_error(self):
        """Test handling a chat request with validation error."""
        request = ChatRequest(
            session_id="",
            messages=[{"role": "user", "content": "Hello"}],
            model="gpt-4",
        )

        # Mock validation to fail
        with patch.object(
            self.controller.validator, "validate_request"
        ) as mock_validate:
            mock_validate.return_value = Mock(
                is_valid=False, errors=[{"field": "session_id", "message": "Required"}]
            )

            result = await self.controller.handle_chat_request(request, "test_request")

            assert isinstance(result, ChatResponse)
            assert "error" in result.content

    def test_get_request_state(self):
        """Test getting request state."""
        self.controller.active_requests["test_request"] = ChatState.PROCESSING

        state = self.controller.get_request_state("test_request")
        assert state == ChatState.PROCESSING

        state = self.controller.get_request_state("nonexistent_request")
        assert state is None

    def test_cancel_request(self):
        """Test cancelling a request."""
        self.controller.active_requests["test_request"] = ChatState.PROCESSING

        result = self.controller.cancel_request("test_request")
        assert result is True
        assert self.controller.active_requests["test_request"] == ChatState.ERROR

        result = self.controller.cancel_request("nonexistent_request")
        assert result is False

    def test_get_controller_stats(self):
        """Test getting controller statistics."""
        stats = self.controller.get_controller_stats()

        assert "active_requests" in stats
        assert "request_states" in stats
        assert "validator_stats" in stats
        assert "rate_limiter_stats" in stats
        assert "session_manager_stats" in stats
        assert "provider_selector_stats" in stats
        assert "response_builder_stats" in stats
        assert "error_handler_stats" in stats
        assert "metrics_collector_stats" in stats
        assert "cache_manager_stats" in stats
        assert "timeout_handler_stats" in stats
        assert "retry_handler_stats" in stats
        assert "compression_handler_stats" in stats
        assert "response_formatter_stats" in stats
        assert "error_formatter_stats" in stats
        assert "timestamp" in stats


# Integration tests
class TestServiceIntegration:
    """Integration tests for service interactions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = ChatValidator()
        self.rate_limiter = ChatRateLimiter()
        self.session_manager = ChatSessionManager()
        self.provider_selector = ChatProviderSelector([])
        self.response_builder = ChatResponseBuilder()
        self.error_handler = ChatErrorHandler()
        self.metrics_collector = ChatMetricsCollector()
        self.cache_manager = ChatCacheManager()
        self.timeout_handler = ChatTimeoutHandler()
        self.retry_handler = ChatRetryHandler()
        self.compression_handler = ChatCompressionHandler()
        self.response_formatter = ChatResponseFormatter()
        self.error_formatter = ChatErrorFormatter()

    @pytest.mark.asyncio
    async def test_full_request_flow(self):
        """Test the complete request flow through all services."""
        request = ChatRequest(
            session_id="test_session",
            messages=[{"role": "user", "content": "Hello"}],
            model="gpt-4",
            temperature=0.7,
            max_tokens=100,
            stream=False,
        )

        # Test validation
        validation_result = await self.validator.validate_request(request)
        assert validation_result.is_valid is True

        # Test rate limiting
        rate_limit_result = await self.rate_limiter.check_rate_limit(
            "user123", "gpt-4", "test_request"
        )
        assert rate_limit_result.allowed is True

        # Test session management
        session = await self.session_manager.get_or_create_session(
            request.session_id, "user123", "127.0.0.1"
        )
        assert session is not None

        # Test metrics collection
        self.metrics_collector.start_request(
            "test_request",
            {
                "session_id": request.session_id,
                "user_id": "user123",
                "model": request.model,
            },
        )

        request_metrics = self.metrics_collector.get_request_metrics("test_request")
        assert request_metrics is not None

        # Test response formatting
        response_data = {"choices": [{"message": {"content": "Hello world"}}]}
        formatted = self.response_formatter.format_response(
            response_data,
            ResponseFormat.JSON,
            "test_request",
            request.session_id,
            "provider1",
        )
        assert formatted is not None

        # Test error formatting
        error = ValueError("Test error")
        formatted_error = self.error_formatter.format_error(
            error, "test_request", request.session_id
        )
        assert formatted_error is not None

        # Test compression
        compressed = self.compression_handler.compress_response(response_data)
        assert isinstance(compressed, bytes)

        # Test cache
        cache_key = "test_key"
        cache_result = self.cache_manager.set(
            cache_key, response_data, CacheType.RESPONSE
        )
        assert cache_result is True

        cached_value = self.cache_manager.get(cache_key, CacheType.RESPONSE)
        assert cached_value is not None

    def test_service_statistics_consistency(self):
        """Test that all services provide consistent statistics."""
        services = [
            self.validator,
            self.rate_limiter,
            self.session_manager,
            self.provider_selector,
            self.response_builder,
            self.error_handler,
            self.metrics_collector,
            self.cache_manager,
            self.timeout_handler,
            self.retry_handler,
            self.compression_handler,
            self.response_formatter,
            self.error_formatter,
        ]

        for service in services:
            stats = service.get_stats()
            assert isinstance(stats, dict)
            assert "timestamp" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
