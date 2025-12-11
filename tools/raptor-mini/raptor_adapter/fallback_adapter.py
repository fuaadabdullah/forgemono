"""
Fallback Adapter for GoblinOS Assistant mini
Provides automatic failover between multiple model backends
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List

from .base import (
    ModelAdapter,
    ModelConfig,
    ModelResponse,
    ModelProvider,
    ModelAdapterError,
    ModelCapability,
)

logger = logging.getLogger(__name__)


class FallbackAdapter(ModelAdapter):
    """
    Adapter that provides automatic failover between multiple model backends.
    Tries adapters in priority order and falls back to the next available one.
    """

    def __init__(self, config: ModelConfig, adapters: List[ModelAdapter]):
        super().__init__(config)
        self.adapters = adapters
        self.current_adapter: Optional[ModelAdapter] = None
        self.failover_history: List[Dict[str, Any]] = []

        # Fallback-specific config
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds
        self.health_check_interval = 30  # seconds

        # Start health monitoring
        self._health_monitor_task: Optional[asyncio.Task] = None

    async def initialize(self) -> bool:
        """
        Initialize the fallback adapter.
        Tests all adapters and sets up health monitoring.
        """
        try:
            # Try to initialize all adapters
            initialized_adapters = []
            for adapter in self.adapters:
                try:
                    if await adapter.initialize():
                        initialized_adapters.append(adapter)
                        logger.info(
                            f"Adapter {adapter.provider.value} initialized successfully"
                        )
                    else:
                        logger.warning(
                            f"Adapter {adapter.provider.value} failed to initialize"
                        )
                except Exception as e:
                    logger.warning(
                        f"Adapter {adapter.provider.value} initialization error: {e}"
                    )

            if not initialized_adapters:
                logger.error("No adapters could be initialized")
                self._initialized = False
                return False

            self.adapters = initialized_adapters

            # Select initial adapter (first healthy one)
            await self._select_best_adapter()

            # Start health monitoring
            self._health_monitor_task = asyncio.create_task(self._health_monitor())

            self._initialized = True
            logger.info(
                f"Fallback adapter initialized with {len(self.adapters)} adapters"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to initialize fallback adapter: {e}")
            self._initialized = False
            return False

    async def _select_best_adapter(self) -> None:
        """Select the best available adapter based on health and priority"""
        for adapter in self.adapters:
            try:
                if await adapter.health_check():
                    if self.current_adapter != adapter:
                        logger.info(f"Switching to adapter: {adapter.provider.value}")
                        self.current_adapter = adapter
                    return
            except Exception as e:
                logger.warning(f"Health check failed for {adapter.provider.value}: {e}")

        # If no adapter is healthy, use the first one anyway
        if self.adapters and self.current_adapter != self.adapters[0]:
            logger.warning("No healthy adapters found, using first available")
            self.current_adapter = self.adapters[0]

    async def _health_monitor(self) -> None:
        """Background task to monitor adapter health"""
        while self._initialized:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self._select_best_adapter()
            except Exception as e:
                logger.error(f"Health monitor error: {e}")

    async def _try_with_failover(
        self, operation: str, *args, **kwargs
    ) -> ModelResponse:
        """
        Try an operation with automatic failover.
        Attempts the operation on the current adapter, and falls back to others if it fails.
        """
        last_error = None

        for attempt in range(self.max_retries):
            if not self.current_adapter:
                raise ModelAdapterError("No adapter available", self.provider)

            try:
                # Try the operation
                method = getattr(self.current_adapter, operation)
                result = await method(*args, **kwargs)

                # Record successful operation
                self._record_success(self.current_adapter)
                return result

            except ModelAdapterError as e:
                last_error = e
                self._record_failure(self.current_adapter, str(e))

                # Try next adapter
                await self._switch_to_next_adapter()

                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    # Final attempt failed
                    break

        # All attempts failed
        raise ModelAdapterError(
            f"All adapters failed after {self.max_retries} attempts. Last error: {last_error}",
            self.provider,
            recoverable=True,
        )

    async def _switch_to_next_adapter(self) -> None:
        """Switch to the next available adapter"""
        if not self.adapters:
            return

        current_index = (
            self.adapters.index(self.current_adapter) if self.current_adapter else -1
        )
        next_index = (current_index + 1) % len(self.adapters)

        self.current_adapter = self.adapters[next_index]
        logger.info(f"Switched to adapter: {self.current_adapter.provider.value}")

    def _record_success(self, adapter: ModelAdapter) -> None:
        """Record a successful operation"""
        self.failover_history.append(
            {
                "timestamp": asyncio.get_event_loop().time(),
                "adapter": adapter.provider.value,
                "status": "success",
            }
        )

    def _record_failure(self, adapter: ModelAdapter, error: str) -> None:
        """Record a failed operation"""
        self.failover_history.append(
            {
                "timestamp": asyncio.get_event_loop().time(),
                "adapter": adapter.provider.value,
                "status": "failure",
                "error": error,
            }
        )

    async def generate(
        self, prompt: str, context: Optional[Dict[str, Any]] = None, **kwargs
    ) -> ModelResponse:
        """Generate text with automatic failover"""
        return await self._try_with_failover("generate", prompt, context, **kwargs)

    async def generate_code(
        self,
        task: str,
        language: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> ModelResponse:
        """Generate code with automatic failover"""
        return await self._try_with_failover(
            "generate_code", task, language, context, **kwargs
        )

    async def review_code(
        self,
        code: str,
        language: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> ModelResponse:
        """Review code with automatic failover"""
        return await self._try_with_failover(
            "review_code", code, language, context, **kwargs
        )

    async def health_check(self) -> bool:
        """Check if any adapter is healthy"""
        for adapter in self.adapters:
            try:
                if await adapter.health_check():
                    return True
            except Exception:
                continue
        return False

    async def cleanup(self) -> None:
        """Clean up all adapters and monitoring"""
        if self._health_monitor_task:
            self._health_monitor_task.cancel()
            try:
                await self._health_monitor_task
            except asyncio.CancelledError:
                pass

        # Clean up all adapters
        cleanup_tasks = [adapter.cleanup() for adapter in self.adapters]
        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)

        self.current_adapter = None
        self._initialized = False

    def get_fallback_info(self) -> Dict[str, Any]:
        """Get information about the fallback configuration"""
        return {
            "provider": self.provider.value,
            "total_adapters": len(self.adapters),
            "current_adapter": self.current_adapter.provider.value
            if self.current_adapter
            else None,
            "adapter_status": [
                {
                    "provider": adapter.provider.value,
                    "healthy": adapter.is_initialized,
                    "metrics": {
                        "requests": adapter.metrics.request_count,
                        "errors": adapter.metrics.error_count,
                        "avg_latency": adapter.metrics.average_latency,
                    },
                }
                for adapter in self.adapters
            ],
            "failover_history": self.failover_history[-10:],  # Last 10 events
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "health_check_interval": self.health_check_interval,
        }
