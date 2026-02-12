"""
Autoscaling Service for Goblin AI System
Handles rate limiting, spike detection, and graceful fallback routing.

Features:
- Rate limiting with sliding window
- Spike detection and automatic fallback
- Cheap model fallback (goblin-simple-llama-1b)
- Emergency auth/health fallback
- Circuit breaker pattern for provider failures
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import redis.asyncio as redis
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class FallbackLevel(Enum):
    """Fallback levels for graceful degradation"""

    NORMAL = "normal"  # Full service
    CHEAP_MODEL = "cheap_model"  # Use goblin-simple-llama-1b
    DENY_REQUEST = "deny"  # Return 429 Too Many Requests
    EMERGENCY = "emergency"  # Auth/health only


@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""

    requests_per_minute: int = 100
    burst_limit: int = 20
    spike_threshold: int = 50  # Requests per 10 seconds considered a spike
    cooldown_minutes: int = 5  # Minutes to stay in fallback after spike


@dataclass
class AutoscalingMetrics:
    """Current autoscaling metrics"""

    current_rpm: float
    spike_detected: bool
    fallback_level: FallbackLevel
    active_connections: int
    queue_depth: int
    last_spike_time: Optional[float]


class AutoscalingService:
    """Service for handling autoscaling, rate limiting, and fallback routing"""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        config: Optional[RateLimitConfig] = None,
    ):
        self.redis_url = redis_url
        self.config = config or RateLimitConfig()
        self.redis: Optional[redis.Redis] = None
        self._lock = asyncio.Lock()

        # Fallback model configuration
        self.cheap_fallback_model = "goblin-simple-llama-1b"
        self.emergency_endpoints = ["/health", "/auth/", "/api/status"]

        # Circuit breaker state
        self.circuit_breaker_failures = {}
        self.circuit_breaker_threshold = 5  # Failures before opening circuit
        self.circuit_breaker_timeout = 60  # Seconds to wait before retry

    async def initialize(self):
        """Initialize Redis connection"""
        if not self.redis:
            self.redis = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()
            logger.info("Autoscaling service initialized with Redis")

    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            self.redis = None

    @asynccontextmanager
    async def redis_connection(self):
        """Context manager for Redis operations"""
        if not self.redis:
            await self.initialize()
        try:
            yield self.redis
        except Exception as e:
            logger.error(f"Redis operation failed: {e}")
            raise

    async def check_rate_limit(
        self, client_ip: str, user_id: Optional[str] = None
    ) -> Tuple[bool, FallbackLevel, Dict[str, Any]]:
        """
        Check if request should be rate limited and determine fallback level.

        Returns:
            (allowed, fallback_level, metadata)
        """
        async with self._lock:
            async with self.redis_connection() as r:
                # Use user_id if available, otherwise client_ip
                identifier = user_id or client_ip
                now = time.time()

                # Clean up old entries (older than 1 minute)
                await r.zremrangebyscore(f"requests:{identifier}", 0, now - 60)

                # Count requests in current window
                request_count = await r.zcard(f"requests:{identifier}")

                # Check for spikes (requests in last 10 seconds)
                spike_count = await r.zcount(f"requests:{identifier}", now - 10, now)

                # Determine fallback level
                fallback_level = FallbackLevel.NORMAL
                allowed = True
                metadata = {
                    "request_count": request_count,
                    "spike_count": spike_count,
                    "cooldown_until": None,
                }

                # Check if in cooldown from previous spike
                cooldown_key = f"cooldown:{identifier}"
                cooldown_until = await r.get(cooldown_key)

                if cooldown_until and float(cooldown_until) > now:
                    # Still in cooldown
                    fallback_level = FallbackLevel.CHEAP_MODEL
                    metadata["cooldown_until"] = float(cooldown_until)
                    logger.warning(
                        f"Client {identifier} in cooldown until {cooldown_until}"
                    )
                elif spike_count >= self.config.spike_threshold:
                    # Spike detected - enter cooldown
                    cooldown_until = now + (self.config.cooldown_minutes * 60)
                    await r.setex(
                        cooldown_key,
                        self.config.cooldown_minutes * 60,
                        str(cooldown_until),
                    )
                    fallback_level = FallbackLevel.CHEAP_MODEL
                    metadata["cooldown_until"] = cooldown_until
                    logger.warning(
                        f"Spike detected for {identifier}: {spike_count} requests in 10s, cooldown until {cooldown_until}"
                    )
                elif request_count >= self.config.requests_per_minute:
                    # Rate limit exceeded
                    allowed = False
                    fallback_level = FallbackLevel.DENY_REQUEST
                    logger.warning(
                        f"Rate limit exceeded for {identifier}: {request_count} requests/minute"
                    )

                # Record this request if allowed
                if allowed:
                    await r.zadd(f"requests:{identifier}", {str(now): now})
                    # Expire the set after 2 minutes to prevent unbounded growth
                    await r.expire(f"requests:{identifier}", 120)

                return allowed, fallback_level, metadata

    async def get_fallback_model(
        self, original_model: str, fallback_level: FallbackLevel
    ) -> str:
        """Get the appropriate fallback model based on level"""
        if fallback_level == FallbackLevel.CHEAP_MODEL:
            return self.cheap_fallback_model
        elif fallback_level == FallbackLevel.EMERGENCY:
            return self.cheap_fallback_model
        else:
            return original_model

    async def is_emergency_endpoint(self, path: str) -> bool:
        """Check if endpoint should always be available (emergency fallback)"""
        return any(path.startswith(endpoint) for endpoint in self.emergency_endpoints)

    async def check_circuit_breaker(self, provider_name: str) -> bool:
        """
        Check circuit breaker state for a provider.
        Returns True if circuit is closed (requests allowed), False if open.
        """
        async with self.redis_connection() as r:
            failure_key = f"circuit:{provider_name}:failures"
            state_key = f"circuit:{provider_name}:state"

            # Check if circuit is open
            state = await r.get(state_key)
            if state == "open":
                # Check if timeout has expired
                opened_at = await r.get(f"circuit:{provider_name}:opened_at")
                if (
                    opened_at
                    and time.time() - float(opened_at) > self.circuit_breaker_timeout
                ):
                    # Reset circuit breaker
                    await r.delete(
                        failure_key, state_key, f"circuit:{provider_name}:opened_at"
                    )
                    logger.info(f"Circuit breaker reset for {provider_name}")
                    return True
                else:
                    logger.warning(f"Circuit breaker open for {provider_name}")
                    return False

            return True

    async def record_provider_failure(self, provider_name: str):
        """Record a provider failure for circuit breaker"""
        async with self.redis_connection() as r:
            failure_key = f"circuit:{provider_name}:failures"
            state_key = f"circuit:{provider_name}:state"

            # Increment failure count
            failures = await r.incr(failure_key)
            await r.expire(failure_key, 300)  # Expire after 5 minutes

            # Check if threshold exceeded
            if failures >= self.circuit_breaker_threshold:
                # Open circuit breaker
                await r.setex(state_key, self.circuit_breaker_timeout, "open")
                await r.setex(
                    f"circuit:{provider_name}:opened_at",
                    self.circuit_breaker_timeout,
                    str(time.time()),
                )
                logger.error(
                    f"Circuit breaker opened for {provider_name} after {failures} failures"
                )

    async def record_provider_success(self, provider_name: str):
        """Record a provider success (resets failure count)"""
        async with self.redis_connection() as r:
            failure_key = f"circuit:{provider_name}:failures"
            await r.delete(failure_key)

    async def get_metrics(self) -> AutoscalingMetrics:
        """Get current autoscaling metrics"""
        async with self.redis_connection() as r:
            now = time.time()

            # Get global request rate (approximate)
            all_keys = await r.keys("requests:*")
            total_requests = 0
            for key in all_keys[
                :10
            ]:  # Sample first 10 keys to avoid too many operations
                count = await r.zcount(key, now - 60, now)
                total_requests += count

            current_rpm = (total_requests / len(all_keys)) * 6 if all_keys else 0

            # Check for recent spikes
            spike_detected = False
            last_spike_time = None
            cooldown_keys = await r.keys("cooldown:*")
            if cooldown_keys:
                # Check if any cooldown is active
                for key in cooldown_keys[:5]:  # Sample first 5
                    cooldown_until = await r.get(key)
                    if cooldown_until and float(cooldown_until) > now:
                        spike_detected = True
                        # Get last spike time from zset
                        client_id = key.replace("cooldown:", "")
                        spike_times = await r.zrange(
                            f"requests:{client_id}", -1, -1, withscores=True
                        )
                        if spike_times:
                            last_spike_time = spike_times[0][1]

            # Determine current fallback level
            fallback_level = FallbackLevel.NORMAL
            if spike_detected:
                fallback_level = FallbackLevel.CHEAP_MODEL

            return AutoscalingMetrics(
                current_rpm=current_rpm,
                spike_detected=spike_detected,
                fallback_level=fallback_level,
                active_connections=len(all_keys),
                queue_depth=0,  # Would need queue system integration
                last_spike_time=last_spike_time,
            )

    async def graceful_shutdown(self):
        """Graceful shutdown - allow emergency endpoints only"""
        async with self.redis_connection() as r:
            await r.setex("system:shutdown", 3600, "true")  # 1 hour emergency mode
            logger.warning(
                "System entering emergency mode - only auth/health endpoints available"
            )

    async def is_emergency_mode(self) -> bool:
        """Check if system is in emergency mode"""
        async with self.redis_connection() as r:
            return bool(await r.exists("system:shutdown"))
