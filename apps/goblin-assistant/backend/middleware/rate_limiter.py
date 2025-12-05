"""Configurable rate limiting middleware with proper headers and error responses.

Provides tiered rate limits configurable via environment variables:
- Auth endpoints: configurable (default: 10/minute)
- Chat endpoints: configurable (default: 30/minute)
- Health endpoints: configurable (default: 60/minute)
- General API: configurable (default: 100/minute)

Supports proper HTTP rate limit headers (RFC 6585):
- X-RateLimit-Limit: Maximum requests per window
- X-RateLimit-Remaining: Remaining requests in current window
- X-RateLimit-Reset: Time when limit resets (Unix timestamp)
- Retry-After: Seconds to wait before retrying (when limit exceeded)

For production with multiple servers, consider using Redis-backed rate limiting.
"""

import time
import os
from collections import defaultdict
from typing import Dict, Tuple
from fastapi import Request, HTTPException, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimiter:
    """Configurable in-memory rate limiter using sliding window."""

    def __init__(self):
        # Store: {client_ip: {endpoint: [(timestamp, count)]}}
        self.requests: Dict[str, Dict[str, list]] = defaultdict(
            lambda: defaultdict(list)
        )

    def is_allowed(
        self, client_ip: str, endpoint: str, limit: int, window: int = 60
    ) -> Tuple[bool, int, int, int]:
        """Check if request is allowed under rate limit.

        Args:
            client_ip: Client IP address
            endpoint: API endpoint pattern
            limit: Maximum requests allowed
            window: Time window in seconds (default: 60)

        Returns:
            Tuple of (is_allowed, retry_after_seconds, remaining_requests, reset_timestamp)
        """
        now = time.time()
        window_start = now - window

        # Clean old requests
        self.requests[client_ip][endpoint] = [
            ts for ts in self.requests[client_ip][endpoint] if ts > window_start
        ]

        current_count = len(self.requests[client_ip][endpoint])
        remaining = max(0, limit - current_count)

        if current_count >= limit:
            # Calculate retry_after based on oldest request
            if self.requests[client_ip][endpoint]:
                oldest = self.requests[client_ip][endpoint][0]
                retry_after = int(window - (now - oldest)) + 1
                reset_timestamp = int(oldest + window)
                return False, retry_after, 0, reset_timestamp
            reset_timestamp = int(now + window)
            return False, window, 0, reset_timestamp

        # Allow request
        self.requests[client_ip][endpoint].append(now)
        reset_timestamp = int(now + window)
        return (
            True,
            0,
            remaining - 1,
            reset_timestamp,
        )  # remaining - 1 because we just added one

    def cleanup_old_entries(self, max_age: int = 300):
        """Cleanup entries older than max_age seconds to prevent memory bloat."""
        now = time.time()
        for client_ip in list(self.requests.keys()):
            for endpoint in list(self.requests[client_ip].keys()):
                self.requests[client_ip][endpoint] = [
                    ts
                    for ts in self.requests[client_ip][endpoint]
                    if now - ts < max_age
                ]
                if not self.requests[client_ip][endpoint]:
                    del self.requests[client_ip][endpoint]
            if not self.requests[client_ip]:
                del self.requests[client_ip]


# Global rate limiter instance
limiter = RateLimiter()


# Load configurable rate limits from environment
RATE_LIMITS = {
    "/auth": int(os.getenv("RATE_LIMIT_AUTH", "10")),  # Default: 10 requests per minute
    "/chat": int(os.getenv("RATE_LIMIT_CHAT", "30")),  # Default: 30 requests per minute
    "/health": int(
        os.getenv("RATE_LIMIT_HEALTH", "60")
    ),  # Default: 60 requests per minute
    "/api": int(
        os.getenv("RATE_LIMIT_API", "50")
    ),  # Default: 50 requests per minute for API endpoints
    "/settings": int(
        os.getenv("RATE_LIMIT_SETTINGS", "20")
    ),  # Default: 20 requests per minute
    "/routing": int(
        os.getenv("RATE_LIMIT_ROUTING", "40")
    ),  # Default: 40 requests per minute
}

DEFAULT_LIMIT = int(
    os.getenv("RATE_LIMIT_DEFAULT", "100")
)  # Default: 100 requests per minute
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # Default: 60 seconds

# Method-specific limits (optional override)
METHOD_LIMITS = {
    "POST": int(
        os.getenv("RATE_LIMIT_POST", "0")
    ),  # 0 means use endpoint-specific limits
    "PUT": int(os.getenv("RATE_LIMIT_PUT", "0")),
    "DELETE": int(os.getenv("RATE_LIMIT_DELETE", "0")),
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce rate limits on API endpoints with proper headers."""

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for metrics endpoint
        if request.url.path == "/metrics":
            return await call_next(request)

        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Determine rate limit for this endpoint
        limit = DEFAULT_LIMIT
        endpoint_pattern = "default"

        # Check method-specific limits first
        method_limit = METHOD_LIMITS.get(request.method)
        if method_limit and method_limit > 0:
            limit = method_limit
            endpoint_pattern = f"{request.method.lower()}_requests"

        # Then check endpoint-specific limits
        for pattern, pattern_limit in RATE_LIMITS.items():
            if request.url.path.startswith(pattern):
                limit = pattern_limit
                endpoint_pattern = pattern
                break

        # Check rate limit
        allowed, retry_after, remaining, reset_timestamp = limiter.is_allowed(
            client_ip, endpoint_pattern, limit, RATE_LIMIT_WINDOW
        )

        if not allowed:
            # Return proper rate limit exceeded response with headers
            response = Response(
                content=f'{{"error": "rate_limit_exceeded", "message": "Rate limit exceeded. Please try again later.", "retry_after": {retry_after}, "limit": {limit}, "window_seconds": {RATE_LIMIT_WINDOW}, "endpoint": "{endpoint_pattern}"}}',
                status_code=429,
                media_type="application/json",
            )
            response.headers["Retry-After"] = str(retry_after)
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = "0"
            response.headers["X-RateLimit-Reset"] = str(reset_timestamp)
            response.headers["X-RateLimit-Window-Seconds"] = str(RATE_LIMIT_WINDOW)
            response.headers["X-RateLimit-Endpoint"] = endpoint_pattern
            return response

        # Process request
        response = await call_next(request)

        # Add rate limit headers to successful responses
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_timestamp)

        return response


def rate_limit_exceeded_handler(request: Request, exc: HTTPException):
    """Handler for rate limit exceptions (not needed with middleware approach)."""
    pass
