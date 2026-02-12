"""
Base adapter class for provider consolidation and normalization.

All provider adapters should subclass this base class to ensure consistent
interfaces, centralized retries, telemetry, cost logging, and circuit breaker protection.
"""

import time
import logging
from typing import Any, Dict, Optional, List
from abc import ABC, abstractmethod

from .circuit_breaker import get_circuit_breaker, CircuitBreakerOpen
from .bulkhead import get_bulkhead, BulkheadExceeded
import asyncio

logger = logging.getLogger("providers")


class ProviderError(Exception):
    """Base exception for provider-related errors."""

    def __init__(
        self, provider: str, message: str, details: Optional[Dict[str, Any]] = None
    ):
        self.provider = provider
        self.message = message
        self.details = details or {}
        super().__init__(f"{provider}: {message}")


class AdapterBase(ABC):
    """Thin base class for all provider adapters.

    Provides circuit breaker protection, telemetry, and cost logging.
    Subclasses handle provider-specific logic.
    """

    def __init__(self, name: str, config: Dict[str, Any]):
        """Initialize the adapter.

        Args:
            name: Provider name (e.g., 'openai', 'anthropic')
            config: Configuration dictionary from ProviderRegistry
        """
        self.name = name
        self.config = config
        self.api_key = config.get("api_key", "")
        self.base_url = config.get("base_url", "")
        self.timeout = config.get("timeout", 30)
        self.max_retries = config.get("retries", 2)
        self.cost_per_token_input = config.get("cost_per_token_input", 0.0)
        self.cost_per_token_output = config.get("cost_per_token_output", 0.0)
        self.latency_threshold_ms = config.get("latency_threshold_ms", 5000)

        # Initialize circuit breaker
        self.circuit_breaker = get_circuit_breaker(
            name=name,
            failure_threshold=5,
            recovery_timeout=60,
            success_threshold=3,
            timeout=self.timeout,
        )

        # Initialize bulkhead for concurrent request limiting
        self.bulkhead = get_bulkhead(
            name=name,
            max_concurrent=10,  # Allow 10 concurrent requests per provider
        )

    def _log_cost(self, input_tokens: int, output_tokens: int):
        """Log cost information for telemetry.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
        """
        total_cost = (
            input_tokens * self.cost_per_token_input
            + output_tokens * self.cost_per_token_output
        )

        if total_cost > 0:
            logger.info(
                "Provider cost logged",
                extra={
                    "provider": self.name,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens,
                    "cost_usd": total_cost,
                    "timestamp": time.time(),
                },
            )

    async def _call_with_circuit_breaker(self, func, *args, **kwargs) -> Any:
        """Execute a provider call with circuit breaker + bulkhead protection.

        Notes:
            Most provider SDKs used here are synchronous. To avoid blocking the
            FastAPI event loop, synchronous callables are executed in a thread.
        """
        try:
            # Fail fast if the circuit is open.
            self.circuit_breaker.before_call()
        except CircuitBreakerOpen as e:
            raise ProviderError(
                self.name, f"Circuit breaker is open: {e}", {"circuit_state": "open"}
            ) from e

        try:
            async with self.bulkhead.guard():
                try:
                    if asyncio.iscoroutinefunction(func):
                        result = await func(*args, **kwargs)
                    else:
                        result = await asyncio.to_thread(func, *args, **kwargs)

                    self.circuit_breaker.record_success()
                    return result
                except Exception:
                    self.circuit_breaker.record_failure()
                    raise
        except BulkheadExceeded as e:
            raise ProviderError(
                self.name,
                f"Bulkhead limit exceeded: {e}",
                {"bulkhead": "exceeded"},
            ) from e
        except ProviderError:
            raise
        except Exception as e:
            raise ProviderError(
                self.name, str(e), {"original_exception": type(e).__name__}
            ) from e

    async def _acall_with_circuit_breaker(self, func, *args, **kwargs) -> Any:
        """Backward-compatible alias for async provider calls."""
        return await self._call_with_circuit_breaker(func, *args, **kwargs)

    def get_status(self) -> Dict[str, Any]:
        """Get adapter status including circuit breaker and bulkhead state.

        Returns:
            Dict with adapter status information
        """
        circuit_status = self.circuit_breaker.get_status()
        bulkhead_status = self.bulkhead.get_status()

        return {
            "provider": self.name,
            "circuit_breaker": circuit_status,
            "bulkhead": bulkhead_status,
            "config": {
                "timeout": self.timeout,
                "max_retries": self.max_retries,
                "cost_per_token_input": self.cost_per_token_input,
                "cost_per_token_output": self.cost_per_token_output,
                "latency_threshold_ms": self.latency_threshold_ms,
            },
            "healthy": circuit_status["state"] != "open"
            and bulkhead_status["available_slots"] > 0,
        }

    @abstractmethod
    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Generate text response from the provider.

        Args:
            messages: List of message dictionaries with role/content
            **kwargs: Additional parameters (model, temperature, max_tokens, etc.)

        Returns:
            Dict containing response data with keys:
            - 'content': Generated text content
            - 'usage': Token usage info (input_tokens, output_tokens, total_tokens)
            - 'model': Model used (optional)
            - 'finish_reason': Completion reason (optional)
        """
        pass

    @abstractmethod
    async def a_generate(
        self, messages: List[Dict[str, str]], **kwargs
    ) -> Dict[str, Any]:
        """Async version of generate method.

        Args:
            messages: List of message dictionaries
            **kwargs: Additional parameters

        Returns:
            Dict containing response data (same format as generate)
        """
        pass

    async def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        **kwargs: Any,
    ) -> str:
        """Default chat implementation backed by `a_generate`.

        Providers that implement a more efficient native chat method may
        override this.
        """
        result = await self.a_generate(messages, model=model, **kwargs)
        if isinstance(result, dict):
            return (result.get("content") or "").strip()
        return str(result).strip()
