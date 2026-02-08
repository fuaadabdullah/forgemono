"""
StreamProcessor Service for handling streaming responses.

This service manages the complex streaming logic that was previously
contained in the stream_router.py file, separating it into focused components.
"""

import asyncio
import json
import logging
import time
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple
from fastapi import HTTPException
from sqlalchemy.orm import Session

from config import settings
from .models import ChatMessage, ChatSession, Provider
from .utils import get_provider_config, get_provider_class, get_provider_model_config
from .stream_utils import (
    StreamEvent,
    StreamEventType,
    StreamMessage,
    StreamMetadata,
    StreamResponse,
    StreamState,
    StreamStats,
    StreamTokenUsage,
    StreamError,
    StreamCompletion,
    StreamChunk,
    StreamChoice,
    StreamUsage,
    StreamDelta,
    StreamFinishReason,
    StreamResponseBuilder,
    StreamErrorHandler,
    StreamValidator,
    StreamRateLimiter,
    StreamTimeoutHandler,
    StreamRetryHandler,
    StreamCompressionHandler,
    StreamMetricsCollector,
    StreamCacheManager,
    StreamSessionManager,
    StreamProviderManager,
    StreamResponseFormatter,
    StreamErrorFormatter,
    StreamValidator,
    StreamRateLimiter,
    StreamTimeoutHandler,
    StreamRetryHandler,
    StreamCompressionHandler,
    StreamMetricsCollector,
    StreamCacheManager,
    StreamSessionManager,
    StreamProviderManager,
    StreamResponseFormatter,
    StreamErrorFormatter,
)

logger = logging.getLogger(__name__)


class StreamProcessor:
    """Service for processing streaming responses from providers."""

    def __init__(self, db: Session):
        """Initialize the StreamProcessor."""
        self.db = db
        self.response_builder = StreamResponseBuilder()
        self.error_handler = StreamErrorHandler()
        self.validator = StreamValidator()
        self.rate_limiter = StreamRateLimiter()
        self.timeout_handler = StreamTimeoutHandler()
        self.retry_handler = StreamRetryHandler()
        self.compression_handler = StreamCompressionHandler()
        self.metrics_collector = StreamMetricsCollector()
        self.cache_manager = StreamCacheManager()
        self.session_manager = StreamSessionManager()
        self.provider_manager = StreamProviderManager()
        self.response_formatter = StreamResponseFormatter()
        self.error_formatter = StreamErrorFormatter()

    async def process_streaming_request(
        self,
        session_id: str,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = True,
        user_id: Optional[str] = None,
        client_ip: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process a streaming request with comprehensive error handling and validation.
        
        Args:
            session_id: Chat session ID
            messages: List of chat messages
            model: Model to use for generation
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            stream: Whether to stream responses
            user_id: User ID for rate limiting
            client_ip: Client IP for rate limiting
            request_id: Request ID for tracking
            
        Yields:
            Streaming response chunks
        """
        # Initialize stream state
        stream_state = StreamState(
            session_id=session_id,
            request_id=request_id or self._generate_request_id(),
            user_id=user_id,
            client_ip=client_ip,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            start_time=time.time(),
        )

        try:
            # Validate request
            validation_result = await self.validator.validate_stream_request(
                messages, model, temperature, max_tokens, stream
            )
            if not validation_result.is_valid:
                raise HTTPException(
                    status_code=400,
                    detail=self.error_formatter.format_validation_error(
                        validation_result.errors
                    ),
                )

            # Check rate limits
            rate_limit_result = await self.rate_limiter.check_rate_limit(
                user_id, client_ip, session_id
            )
            if not rate_limit_result.allowed:
                raise HTTPException(
                    status_code=429,
                    detail=self.error_formatter.format_rate_limit_error(
                        rate_limit_result.retry_after
                    ),
                )

            # Get or create chat session
            chat_session = await self.session_manager.get_or_create_session(
                session_id, user_id
            )

            # Get provider configuration
            provider_config = await self.provider_manager.get_provider_for_model(
                model, messages
            )

            if not provider_config:
                raise HTTPException(
                    status_code=503,
                    detail=self.error_formatter.format_provider_error(
                        "No suitable provider available"
                    ),
                )

            # Initialize metrics
            self.metrics_collector.start_request(stream_state.request_id)

            # Process streaming response
            async for chunk in self._process_streaming_response(
                stream_state, provider_config, messages
            ):
                yield chunk

        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            logger.error(f"Stream processing error: {e}")
            error_response = self.error_handler.handle_stream_error(
                e, stream_state.request_id
            )
            yield error_response
        finally:
            # Cleanup resources
            await self._cleanup_stream_resources(stream_state)

    async def _process_streaming_response(
        self,
        stream_state: StreamState,
        provider_config: Dict[str, Any],
        messages: List[Dict[str, Any]],
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process streaming response from provider."""
        provider_class = get_provider_class(provider_config["provider_name"])
        provider_instance = provider_class(provider_config)

        # Prepare request
        request_data = {
            "messages": messages,
            "model": stream_state.model,
            "temperature": stream_state.temperature,
            "max_tokens": stream_state.max_tokens,
            "stream": True,
        }

        try:
            # Make streaming request
            async for chunk in provider_instance.stream_chat_completion(request_data):
                # Process chunk
                processed_chunk = await self._process_stream_chunk(
                    chunk, stream_state
                )
                
                if processed_chunk:
                    yield processed_chunk

        except Exception as e:
            logger.error(f"Provider streaming error: {e}")
            raise

    async def _process_stream_chunk(
        self, chunk: Dict[str, Any], stream_state: StreamState
    ) -> Optional[Dict[str, Any]]:
        """Process individual stream chunk."""
        try:
            # Validate chunk
            if not self.validator.validate_stream_chunk(chunk):
                logger.warning(f"Invalid stream chunk: {chunk}")
                return None

            # Update metrics
            self.metrics_collector.update_chunk_metrics(
                stream_state.request_id, chunk
            )

            # Format response
            formatted_response = self.response_formatter.format_stream_chunk(
                chunk, stream_state
            )

            # Apply compression if enabled
            if settings.enable_stream_compression:
                formatted_response = self.compression_handler.compress_chunk(
                    formatted_response
                )

            return formatted_response

        except Exception as e:
            logger.error(f"Error processing stream chunk: {e}")
            return None

    async def _cleanup_stream_resources(self, stream_state: StreamState) -> None:
        """Clean up stream resources."""
        try:
            # Update session metrics
            await self.session_manager.update_session_metrics(
                stream_state.session_id,
                self.metrics_collector.get_request_metrics(stream_state.request_id),
            )

            # Clean up cache
            await self.cache_manager.cleanup_session_cache(stream_state.session_id)

            # Record metrics
            self.metrics_collector.end_request(stream_state.request_id)

        except Exception as e:
            logger.error(f"Error cleaning up stream resources: {e}")

    def _generate_request_id(self) -> str:
        """Generate a unique request ID."""
        import uuid
        return f"stream_{uuid.uuid4().hex[:16]}"


class StreamResponseBuilder:
    """Builder for streaming responses."""

    def build_stream_chunk(
        self,
        chunk_data: Dict[str, Any],
        stream_state: StreamState,
        chunk_index: int,
    ) -> StreamChunk:
        """Build a stream chunk from provider data."""
        return StreamChunk(
            id=stream_state.request_id,
            object="chat.completion.chunk",
            created=int(time.time()),
            model=stream_state.model,
            choices=[
                StreamChoice(
                    index=chunk_index,
                    delta=StreamDelta(
                        content=chunk_data.get("content", ""),
                        role=chunk_data.get("role", "assistant"),
                    ),
                    finish_reason=None,
                )
            ],
            usage=None,  # Usage is only in final chunk
        )

    def build_stream_completion(
        self,
        final_data: Dict[str, Any],
        stream_state: StreamState,
        total_chunks: int,
    ) -> StreamCompletion:
        """Build the final stream completion."""
        return StreamCompletion(
            id=stream_state.request_id,
            object="chat.completion",
            created=int(time.time()),
            model=stream_state.model,
            choices=[
                StreamChoice(
                    index=0,
                    message=StreamMessage(
                        role="assistant",
                        content=final_data.get("content", ""),
                    ),
                    finish_reason=StreamFinishReason.STOP,
                )
            ],
            usage=StreamUsage(
                prompt_tokens=final_data.get("prompt_tokens", 0),
                completion_tokens=final_data.get("completion_tokens", 0),
                total_tokens=final_data.get("total_tokens", 0),
            ),
        )


class StreamErrorHandler:
    """Handler for streaming errors."""

    def handle_stream_error(
        self, error: Exception, request_id: str
    ) -> StreamError:
        """Handle streaming errors and return error response."""
        error_type = type(error).__name__
        error_message = str(error)

        return StreamError(
            id=request_id,
            object="error",
            error={
                "type": error_type,
                "message": error_message,
                "code": 500,
            },
        )


class StreamValidator:
    """Validator for streaming requests and responses."""

    async def validate_stream_request(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float,
        max_tokens: Optional[int],
        stream: bool,
    ) -> StreamValidationResult:
        """Validate streaming request parameters."""
        errors = []

        # Validate messages
        if not messages:
            errors.append("Messages cannot be empty")

        # Validate model
        if not model:
            errors.append("Model is required")

        # Validate temperature
        if not (0.0 <= temperature <= 2.0):
            errors.append("Temperature must be between 0.0 and 2.0")

        # Validate max_tokens
        if max_tokens is not None and max_tokens <= 0:
            errors.append("Max tokens must be positive")

        # Validate stream flag
        if not stream:
            errors.append("Stream must be True for streaming requests")

        return StreamValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
        )

    def validate_stream_chunk(self, chunk: Dict[str, Any]) -> bool:
        """Validate individual stream chunk."""
        required_fields = ["content"]
        return all(field in chunk for field in required_fields)


class StreamRateLimiter:
    """Rate limiter for streaming requests."""

    async def check_rate_limit(
        self, user_id: Optional[str], client_ip: Optional[str], session_id: str
    ) -> RateLimitResult:
        """Check rate limits for streaming requests."""
        # Implementation would depend on rate limiting strategy
        # This is a placeholder for the actual rate limiting logic
        return RateLimitResult(
            allowed=True,
            retry_after=None,
        )


class StreamTimeoutHandler:
    """Handler for streaming timeouts."""

    def __init__(self, timeout_seconds: int = 300):
        """Initialize with timeout configuration."""
        self.timeout_seconds = timeout_seconds

    async def check_timeout(self, start_time: float) -> bool:
        """Check if request has timed out."""
        return time.time() - start_time > self.timeout_seconds


class StreamRetryHandler:
    """Handler for retrying failed streaming requests."""

    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        """Initialize with retry configuration."""
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    async def retry_with_backoff(self, func, *args, **kwargs):
        """Retry function with exponential backoff."""
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise e
                await asyncio.sleep(self.retry_delay * (2**attempt))


class StreamCompressionHandler:
    """Handler for compressing streaming responses."""

    def __init__(self, compression_enabled: bool = False):
        """Initialize with compression configuration."""
        self.compression_enabled = compression_enabled

    def compress_chunk(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """Compress a stream chunk if compression is enabled."""
        if not self.compression_enabled:
            return chunk

        # Implementation would depend on compression algorithm
        # This is a placeholder for the actual compression logic
        return chunk


class StreamMetricsCollector:
    """Collector for streaming metrics."""

    def __init__(self):
        """Initialize metrics collection."""
        self.request_metrics: Dict[str, StreamStats] = {}

    def start_request(self, request_id: str) -> None:
        """Start collecting metrics for a request."""
        self.request_metrics[request_id] = StreamStats(
            request_id=request_id,
            start_time=time.time(),
            chunks_processed=0,
            total_tokens=0,
            response_time=0.0,
        )

    def update_chunk_metrics(self, request_id: str, chunk: Dict[str, Any]) -> None:
        """Update metrics with chunk data."""
        if request_id in self.request_metrics:
            stats = self.request_metrics[request_id]
            stats.chunks_processed += 1
            stats.total_tokens += len(chunk.get("content", "").split())
            stats.response_time = time.time() - stats.start_time

    def get_request_metrics(self, request_id: str) -> Optional[StreamStats]:
        """Get metrics for a request."""
        return self.request_metrics.get(request_id)

    def end_request(self, request_id: str) -> None:
        """End metrics collection for a request."""
        if request_id in self.request_metrics:
            stats = self.request_metrics[request_id]
            stats.response_time = time.time() - stats.start_time


class StreamCacheManager:
    """Manager for caching streaming responses."""

    def __init__(self, cache_ttl: int = 300):
        """Initialize cache manager."""
        self.cache_ttl = cache_ttl
        self.cache: Dict[str, Tuple[Any, float]] = {}

    async def get_cached_response(self, cache_key: str) -> Optional[Any]:
        """Get cached response if not expired."""
        if cache_key in self.cache:
            response, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return response
        return None

    async def cache_response(self, cache_key: str, response: Any) -> None:
        """Cache a response."""
        self.cache[cache_key] = (response, time.time())

    async def cleanup_session_cache(self, session_id: str) -> None:
        """Clean up cache for a session."""
        keys_to_remove = [
            key for key in self.cache.keys() if key.startswith(session_id)
        ]
        for key in keys_to_remove:
            del self.cache[key]


class StreamSessionManager:
    """Manager for chat sessions."""

    async def get_or_create_session(
        self, session_id: str, user_id: Optional[str]
    ) -> ChatSession:
        """Get or create a chat session."""
        # This would interact with the database
        # Placeholder implementation
        return ChatSession(
            id=session_id,
            user_id=user_id,
            created_at=time.time(),
            updated_at=time.time(),
        )

    async def update_session_metrics(
        self, session_id: str, metrics: StreamStats
    ) -> None:
        """Update session metrics."""
        # This would update the database
        # Placeholder implementation
        pass


class StreamProviderManager:
    """Manager for selecting and configuring providers."""

    async def get_provider_for_model(
        self, model: str, messages: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Get the best provider for a model and messages."""
        # This would implement provider selection logic
        # Placeholder implementation
        return {
            "provider_name": "openai",
            "model": model,
            "config": {},
        }


class StreamResponseFormatter:
    """Formatter for streaming responses."""

    def format_stream_chunk(
        self, chunk_data: Dict[str, Any], stream_state: StreamState
    ) -> Dict[str, Any]:
        """Format a stream chunk for the client."""
        return {
            "id": stream_state.request_id,
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": stream_state.model,
            "choices": [
                {
                    "index": 0,
                    "delta": {
                        "content": chunk_data.get("content", ""),
                        "role": chunk_data.get("role", "assistant"),
                    },
                    "finish_reason": None,
                }
            ],
        }


class StreamErrorFormatter:
    """Formatter for streaming errors."""

    def format_validation_error(self, errors: List[str]) -> Dict[str, Any]:
        """Format validation errors."""
        return {
            "type": "validation_error",
            "message": "Request validation failed",
            "errors": errors,
        }

    def format_rate_limit_error(self, retry_after: Optional[float]) -> Dict[str, Any]:
        """Format rate limit errors."""
        error_msg = {"type": "rate_limit_exceeded", "message": "Rate limit exceeded"}
        if retry_after:
            error_msg["retry_after"] = retry_after
        return error_msg

    def format_provider_error(self, error_msg: str) -> Dict[str, Any]:
        """Format provider errors."""
        return {
            "type": "provider_error",
            "message": error_msg,
        }


# Type definitions for stream components
class StreamValidationResult:
    """Result of stream validation."""
    
    def __init__(self, is_valid: bool, errors: List[str]):
        self.is_valid = is_valid
        self.errors = errors


class RateLimitResult:
    """Result of rate limit check."""
    
    def __init__(self, allowed: bool, retry_after: Optional[float]):
        self.allowed = allowed
        self.retry_after = retry_after
