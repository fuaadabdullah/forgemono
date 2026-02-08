"""
Backpressure and Rate Limiting Middleware for Goblin DocQA
"""

import os
from fastapi import Request, HTTPException, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
from limits import RateLimitItemPerMinute, RateLimitItemPerHour
from limits.aio.storage import RedisStorage
from limits.aio.strategies import MovingWindowRateLimiter
import redis.asyncio as redis
import logging
from dotenv import load_dotenv
from .metrics import record_rate_limit_hit

load_dotenv()

# Configuration from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
RATE_LIMIT_REQUESTS_PER_MINUTE = int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "10"))
RATE_LIMIT_REQUESTS_PER_HOUR = int(os.getenv("RATE_LIMIT_REQUESTS_PER_HOUR", "100"))
MAX_REQUEST_SIZE_MB = int(os.getenv("MAX_REQUEST_SIZE_MB", "50"))  # 50MB default
QUEUE_BACKPRESSURE_TIMEOUT = float(os.getenv("QUEUE_BACKPRESSURE_TIMEOUT", "0.5"))

# Initialize Redis for rate limiting
redis_client = None
rate_limiter = None


async def init_rate_limiter():
    """Initialize Redis-based rate limiter."""
    global redis_client, rate_limiter
    try:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        storage = RedisStorage(redis_client)
        rate_limiter = MovingWindowRateLimiter(storage)
        logging.getLogger(__name__).info("✅ Rate limiter initialized with Redis")
    except Exception as e:
        logging.getLogger(__name__).warning(
            f"⚠️  Failed to initialize Redis rate limiter: {e}"
        )
        logging.getLogger(__name__).warning("   Falling back to no Redis rate limiter")
        rate_limiter = None

    # Determine storage for slowapi limiter: Redis if available, otherwise memory
    storage_uri = REDIS_URL if rate_limiter else "memory://"
    # Initialize slowapi limiter instance based on chosen storage backend
    global limiter
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[
            f"{RATE_LIMIT_REQUESTS_PER_MINUTE}/minute",
            f"{RATE_LIMIT_REQUESTS_PER_HOUR}/hour",
        ],
        storage_uri=storage_uri,
    )


async def check_advanced_rate_limit(client_ip: str, endpoint: str) -> bool:
    """
    Check advanced rate limiting using limits library.
    Returns True if request should be allowed, False if rate limited.
    """
    if not rate_limiter:
        return True  # Allow if rate limiter not initialized

    # Create rate limit keys
    per_minute_key = f"ratelimit:{client_ip}:{endpoint}:minute"
    per_hour_key = f"ratelimit:{client_ip}:{endpoint}:hour"

    # Check rate limits
    minute_limit = RateLimitItemPerMinute(RATE_LIMIT_REQUESTS_PER_MINUTE)
    hour_limit = RateLimitItemPerHour(RATE_LIMIT_REQUESTS_PER_HOUR)

    minute_ok = await rate_limiter.hit(minute_limit, per_minute_key)
    hour_ok = await rate_limiter.hit(hour_limit, per_hour_key)

    return minute_ok and hour_ok


async def request_size_middleware(request: Request, call_next):
    """
    Middleware to enforce request size limits.
    Rejects requests that are too large to prevent memory exhaustion.
    """
    # Skip size check for health endpoint
    if request.url.path == "/health":
        return await call_next(request)

    # Check Content-Length header first
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            size_mb = int(content_length) / (1024 * 1024)
            if size_mb > MAX_REQUEST_SIZE_MB:
                return JSONResponse(
                    status_code=413,
                    content={
                        "error": "Request too large",
                        "detail": (
                            f"Request size {size_mb:.1f}MB exceeds limit of "
                            f"{MAX_REQUEST_SIZE_MB}MB"
                        ),
                        "max_size_mb": MAX_REQUEST_SIZE_MB,
                    },
                )
        except ValueError:
            pass  # Invalid content-length, continue with body check

    # For requests with body, we need to be careful about memory usage
    # FastAPI will handle this, but we can add additional checks here if needed

    response = await call_next(request)
    return response


async def backpressure_middleware(request: Request, call_next):
    """
    Middleware to implement backpressure when queues are full.
    Returns 429 Too Many Requests when the system is overloaded.
    """
    from .server import job_queue, inference_queue

    # Skip backpressure check for health and status endpoints
    if request.url.path in [
        "/health",
        "/docs",
        "/openapi.json",
    ] or request.url.path.startswith("/job/"):
        return await call_next(request)

    # Check job queue backpressure
    if job_queue:
        try:
            # Try to submit a test job with very short timeout to check queue capacity
            # This is a lightweight way to check if the queue can accept work
            queue_status = job_queue.get_queue_stats()
            if (
                queue_status.get("queued", 0) > queue_status.get("max_queued", 10) * 0.8
            ):  # 80% capacity
                retry_after = 30  # seconds
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Server busy",
                        "detail": "Job queue is at capacity. Please try again later.",
                        "retry_after": retry_after,
                        "queue_stats": queue_status,
                    },
                    headers={"Retry-After": str(retry_after)},
                )
        except Exception:
            # If we can't check queue status, continue (fail open)
            pass

    # Check inference queue backpressure
    if inference_queue and hasattr(inference_queue, "queue"):
        try:
            queue_size = inference_queue.queue.qsize()
            max_queue = getattr(inference_queue.queue, "maxsize", 4)
            if max_queue and queue_size >= max_queue * 0.9:  # 90% capacity
                retry_after = 10  # seconds
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Inference queue full",
                        "detail": (
                            "Model inference queue is at capacity. "
                            "Please try again later."
                        ),
                        "retry_after": retry_after,
                        "queue_size": queue_size,
                        "max_queue": max_queue,
                    },
                    headers={"Retry-After": str(retry_after)},
                )
        except Exception:
            # If we can't check inference queue, continue (fail open)
            pass

    response = await call_next(request)
    return response


async def advanced_rate_limit_middleware(request: Request, call_next):
    """
    Advanced rate limiting middleware using Redis sliding windows.
    Applied per IP address and endpoint.
    """
    # Skip rate limiting for health endpoint
    if request.url.path == "/health":
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"
    endpoint = request.url.path

    # Check advanced rate limits
    if not await check_advanced_rate_limit(client_ip, endpoint):
        # Record rate limit hit metrics
        record_rate_limit_hit(client_ip, endpoint)

        retry_after = 60  # seconds
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "detail": f"Too many requests from {client_ip} to {endpoint}",
                "retry_after": retry_after,
                "limits": {
                    "requests_per_minute": RATE_LIMIT_REQUESTS_PER_MINUTE,
                    "requests_per_hour": RATE_LIMIT_REQUESTS_PER_HOUR,
                },
            },
            headers={"Retry-After": str(retry_after)},
        )

    response = await call_next(request)
    return response


# Custom rate limit exceeded handler for SlowAPI
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for SlowAPI rate limit exceeded."""
    retry_after = 60  # Default retry time
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "detail": str(exc),
            "retry_after": retry_after,
        },
        headers={"Retry-After": str(retry_after)},
    )


# Override the default SlowAPI handler
_rate_limit_exceeded_handler.default_exception_handler = custom_rate_limit_handler
