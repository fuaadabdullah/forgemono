"""
Prometheus Metrics for Goblin DocQA
Provides comprehensive observability for the documentation quality analysis system.
"""

import time
import psutil
import os
from typing import Optional, Dict, Any
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    CollectorRegistry,
    generate_latest,
)
import redis
from dotenv import load_dotenv

load_dotenv()

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
METRICS_PREFIX = os.getenv("METRICS_PREFIX", "goblin_docqa")

# Create registry for metrics
registry = CollectorRegistry()

# === PROCESS METRICS ===
process_memory_bytes = Gauge(
    f"{METRICS_PREFIX}_process_memory_bytes",
    "Process memory usage in bytes",
    ["type"],
    registry=registry,
)

process_cpu_seconds_total = Counter(
    f"{METRICS_PREFIX}_process_cpu_seconds_total",
    "Total CPU time used by process in seconds",
    registry=registry,
)

# === INFERENCE METRICS ===
inference_queue_length = Gauge(
    f"{METRICS_PREFIX}_inference_queue_length",
    "Current length of inference queue",
    registry=registry,
)

inference_latency_seconds = Histogram(
    f"{METRICS_PREFIX}_inference_latency_seconds",
    "Inference request latency in seconds",
    ["model", "method"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
    registry=registry,
)

# === REQUEST METRICS ===
requests_total = Counter(
    f"{METRICS_PREFIX}_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status_code"],
    registry=registry,
)

requests_429_total = Counter(
    f"{METRICS_PREFIX}_requests_429_total",
    "Total number of HTTP 429 responses",
    ["method", "endpoint"],
    registry=registry,
)

# === QUEUE METRICS ===
queue_length = Gauge(
    f"{METRICS_PREFIX}_queue_length",
    "Current length of job queues",
    ["queue_type"],
    registry=registry,
)

queue_max_size = Gauge(
    f"{METRICS_PREFIX}_queue_max_size",
    "Maximum size of job queues",
    ["queue_type"],
    registry=registry,
)

# === LEGACY INFERENCE METRICS (keeping for compatibility) ===
inference_requests_total = Counter(
    f"{METRICS_PREFIX}_inference_requests_total",
    "Total number of inference requests",
    ["model", "method", "status"],
    registry=registry,
)

inference_errors_total = Counter(
    f"{METRICS_PREFIX}_inference_errors_total",
    "Total number of inference errors",
    ["model", "method", "error_type"],
    registry=registry,
)

# === API METRICS ===
api_requests_total = Counter(
    f"{METRICS_PREFIX}_api_requests_total",
    "Total number of API requests",
    ["method", "endpoint", "status_code"],
    registry=registry,
)

api_request_duration_seconds = Histogram(
    f"{METRICS_PREFIX}_api_request_duration_seconds",
    "API request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0),
    registry=registry,
)

# === RESOURCE METRICS ===
memory_bytes = Gauge(
    f"{METRICS_PREFIX}_memory_bytes",
    "Memory usage in bytes",
    ["type"],
    registry=registry,
)

cpu_usage_percent = Gauge(
    f"{METRICS_PREFIX}_cpu_usage_percent", "CPU usage percentage", registry=registry
)

cpu_seconds_total = Counter(
    f"{METRICS_PREFIX}_cpu_seconds_total",
    "Total CPU time used in seconds",
    registry=registry,
)

# === RATE LIMITING METRICS ===
rate_limit_hits_total = Counter(
    f"{METRICS_PREFIX}_rate_limit_hits_total",
    "Total number of rate limit hits",
    ["client_ip", "endpoint"],
    registry=registry,
)

# === COPILOT PROXY METRICS ===
copilot_tokens_used_total = Counter(
    f"{METRICS_PREFIX}_copilot_tokens_used_total",
    "Total number of Copilot API tokens used",
    ["model", "endpoint"],
    registry=registry,
)

copilot_requests_total = Counter(
    f"{METRICS_PREFIX}_copilot_requests_total",
    "Total number of Copilot API requests",
    ["model", "status"],
    registry=registry,
)

copilot_request_duration_seconds = Histogram(
    f"{METRICS_PREFIX}_copilot_request_duration_seconds",
    "Copilot API request duration in seconds",
    ["model"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0),
    registry=registry,
)

# === MODEL METRICS ===
model_loaded = Gauge(
    f"{METRICS_PREFIX}_model_loaded",
    "Whether a model is currently loaded (1=yes, 0=no)",
    ["model_name"],
    registry=registry,
)

model_memory_bytes = Gauge(
    f"{METRICS_PREFIX}_model_memory_bytes",
    "Memory used by loaded models",
    ["model_name"],
    registry=registry,
)

# === SYSTEM METRICS ===
uptime_seconds = Gauge(
    f"{METRICS_PREFIX}_uptime_seconds", "Service uptime in seconds", registry=registry
)

# Track startup time for uptime calculation
_start_time = time.time()

# Redis client for metrics storage
_redis_client = None


def get_redis_client():
    """Get Redis client for metrics storage."""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        except Exception:
            _redis_client = None
    return _redis_client


def update_inference_queue_metrics(queue_length: int):
    """Update inference queue length metrics."""
    inference_queue_length.set(queue_length)


def record_inference_request(
    model: str, method: str, status: str, duration: Optional[float] = None
):
    """Record an inference request."""
    inference_requests_total.labels(model=model, method=method, status=status).inc()

    if duration is not None:
        inference_latency_seconds.labels(model=model, method=method).observe(duration)


def record_inference_error(model: str, method: str, error_type: str):
    """Record an inference error."""
    inference_errors_total.labels(
        model=model, method=method, error_type=error_type
    ).inc()


def record_api_request(
    method: str, endpoint: str, status_code: int, duration: Optional[float] = None
):
    """Record an API request."""
    api_requests_total.labels(
        method=method, endpoint=endpoint, status_code=str(status_code)
    ).inc()

    # Also record in the general requests_total metric
    requests_total.labels(
        method=method, endpoint=endpoint, status_code=str(status_code)
    ).inc()

    # Record 429 responses separately
    if status_code == 429:
        requests_429_total.labels(method=method, endpoint=endpoint).inc()

    if duration is not None:
        api_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(
            duration
        )


def record_rate_limit_hit(client_ip: str, endpoint: str):
    """Record a rate limit hit."""
    rate_limit_hits_total.labels(client_ip=client_ip, endpoint=endpoint).inc()


def record_copilot_usage(
    model: str, tokens_used: int, endpoint: str = "", duration: Optional[float] = None
):
    """Record Copilot API usage."""
    if tokens_used > 0:
        copilot_tokens_used_total.labels(model=model, endpoint=endpoint).inc(
            tokens_used
        )

    copilot_requests_total.labels(model=model, status="success").inc()

    if duration is not None:
        copilot_request_duration_seconds.labels(model=model).observe(duration)


def record_copilot_error(model: str, error_type: str):
    """Record a Copilot API error."""
    copilot_requests_total.labels(model=model, status=f"error_{error_type}").inc()


def update_model_metrics(
    model_name: str, loaded: bool, memory_usage: Optional[int] = None
):
    """Update model loading metrics."""
    model_loaded.labels(model_name=model_name).set(1 if loaded else 0)

    if memory_usage is not None:
        model_memory_bytes.labels(model_name=model_name).set(memory_usage)


def update_system_metrics():
    """Update system resource metrics."""
    try:
        # Memory usage
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_bytes.labels(type="rss").set(memory_info.rss)
        memory_bytes.labels(type="vms").set(memory_info.vms)
        process_memory_bytes.labels(type="rss").set(memory_info.rss)
        process_memory_bytes.labels(type="vms").set(memory_info.vms)

        # CPU usage
        cpu_percent = process.cpu_percent(interval=None)
        cpu_usage_percent.set(cpu_percent)

        # CPU time
        cpu_times = process.cpu_times()
        total_cpu_seconds = cpu_times.user + cpu_times.system
        cpu_seconds_total.inc(total_cpu_seconds - cpu_seconds_total._value)
        process_cpu_seconds_total.inc(
            total_cpu_seconds - process_cpu_seconds_total._value
        )

        # Uptime
        uptime_seconds.set(time.time() - _start_time)

    except Exception:
        # Don't fail if we can't get system metrics
        pass


def get_metrics() -> str:
    """Get all metrics in Prometheus format."""
    update_system_metrics()
    return generate_latest(registry).decode("utf-8")


def get_metrics_dict() -> Dict[str, Any]:
    """Get metrics as a dictionary for health checks."""
    return {
        "queue_length": {
            "job_queue": queue_length.labels(queue_type="job")._value,
            "inference_queue": queue_length.labels(queue_type="inference")._value,
        },
        "inference_errors": {
            "total": sum(
                metric._value for metric in inference_errors_total._metrics.values()
            )
        },
        "memory_mb": {
            "rss": 0.0,  # Placeholder - will be updated by update_system_metrics
            "vms": 0.0,
        },
        "cpu_percent": 0.0,
        "uptime_seconds": 0.0,
    }


# Initialize metrics on import
update_system_metrics()
