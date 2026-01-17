"""
Datadog integration for monitoring, metrics, and APM
"""

import os
import time
from typing import Any, Dict, List
from functools import wraps

# Initialize Datadog
DATADOG_ENABLED = False
statsd = None
tracer = None

try:
    from ddtrace import tracer, patch_all
    from datadog import statsd

    # Auto-instrumentation
    patch_all()

    # Note: ddtrace tracer is already configured automatically
    # No need for manual tracer.configure() call

    DATADOG_ENABLED = True
except Exception as e:
    print(f"Datadog initialization failed: {e}")


def datadog_trace(operation_name: str, service: str = "goblin-assistant"):
    """Decorator to trace function calls with Datadog APM"""

    def decorator(func):
        if not DATADOG_ENABLED:
            return func

        @wraps(func)
        async def wrapper(*args, **kwargs):
            with tracer.trace(operation_name, service=service):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)

                    # Record success metrics
                    duration = time.time() - start_time
                    statsd.increment(
                        "api.request.success", tags=[f"endpoint:{operation_name}"]
                    )
                    statsd.histogram(
                        "api.request.duration",
                        duration,
                        tags=[f"endpoint:{operation_name}"],
                    )

                    return result
                except Exception as e:
                    # Record error metrics
                    duration = time.time() - start_time
                    statsd.increment(
                        "api.request.error",
                        tags=[
                            f"endpoint:{operation_name}",
                            f"error_type:{type(e).__name__}",
                        ],
                    )

                    # Trace the error
                    with tracer.trace("error", service=service) as span:
                        span.set_tag("error", True)
                        span.set_tag("error.message", str(e))
                        span.set_tag("error.type", type(e).__name__)

                    raise

        return wrapper

    return decorator


def datadog_gauge(metric_name: str, tags: List[str] = None):
    """Decorator to track function duration as a Datadog gauge"""

    def decorator(func):
        if not DATADOG_ENABLED:
            return func

        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                statsd.gauge(metric_name, duration, tags=tags or [])
                return result
            except Exception:
                statsd.increment(f"{metric_name}.error", tags=tags or [])
                raise

        return wrapper

    return decorator


class DatadogProviderMonitor:
    """Enhanced provider monitoring with Datadog metrics.

    Centralized metrics collection for provider operations.
    Metrics are tagged by provider for easy filtering and aggregation.
    Success/error ratios help identify problematic providers.
    """

    def __init__(self):
        self.enabled = DATADOG_ENABLED

    def track_provider_request(
        self, provider: str, success: bool, duration: float, error: str = None
    ):
        """Track provider request metrics"""
        if not self.enabled:
            return

        tags = [f"provider:{provider}"]

        if success:
            statsd.increment("provider.request.success", tags=tags)
        else:
            statsd.increment("provider.request.error", tags=tags)
            if error:
                statsd.increment(
                    "provider.request.error", tags=tags + [f"error:{error}"]
                )

        statsd.histogram("provider.request.duration", duration, tags=tags)

    def track_conversation_metrics(self, action: str, user_id: str = None):
        """Track conversation metrics"""
        if not self.enabled:
            return

        tags = [f"action:{action}"]
        if user_id:
            tags.append(f"user:{user_id}")

        statsd.increment("conversation.operations", tags=tags)

    def track_cache_metrics(self, operation: str, hit: bool):
        """Track cache performance metrics"""
        if not self.enabled:
            return

        statsd.increment(
            "cache.operations",
            tags=[f"operation:{operation}", f"result:{'hit' if hit else 'miss'}"],
        )

    def track_system_health(self, component: str, status: str):
        """Track system health metrics"""
        if not self.enabled:
            return

        tags = [f"component:{component}", f"status:{status}"]
        statsd.increment("system.health.checks", tags=tags)


# Global instance
datadog_monitor = DatadogProviderMonitor()


def get_datadog_service_info() -> Dict[str, Any]:
    """Get Datadog service configuration"""
    return {
        "enabled": DATADOG_ENABLED,
        "agent_host": os.getenv("DATADOG_AGENT_HOST", "localhost"),
        "agent_port": os.getenv("DATADOG_AGENT_PORT", "8126"),
        "statsd_port": os.getenv("DATADOG_PORT", "8125"),
        "service": "goblin-assistant",
        "version": "1.0.0",
    }
