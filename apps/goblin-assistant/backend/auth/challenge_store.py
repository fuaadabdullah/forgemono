"""
Challenge Store Service for WebAuthn Passkey Authentication

Provides an abstraction layer for challenge storage with support for:
- In-memory storage (development)
- Redis storage (production)
- Automatic TTL/expiration
- Thread-safe operations
"""

from typing import Optional, Dict
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import os
import time
import logging

# Import configuration
try:
    from config import settings

    config_available = True
except ImportError:
    config_available = False


class ChallengeStore(ABC):
    """Abstract base class for challenge storage"""

    @abstractmethod
    async def set_challenge(
        self, email: str, challenge: str, ttl_minutes: int = 5
    ) -> None:
        """
        Store a challenge for a user with expiration.

        Args:
            email: User's email address (key)
            challenge: Base64url-encoded challenge string
            ttl_minutes: Time-to-live in minutes
        """
        pass

    @abstractmethod
    async def get_challenge(self, email: str) -> Optional[str]:
        """
        Retrieve a challenge for a user.

        Args:
            email: User's email address

        Returns:
            Challenge string if exists and not expired, None otherwise
        """
        pass

    @abstractmethod
    async def delete_challenge(self, email: str) -> bool:
        """
        Delete a challenge (for one-time use).

        Args:
            email: User's email address

        Returns:
            True if challenge existed and was deleted, False otherwise
        """
        pass

    @abstractmethod
    async def cleanup_expired(self) -> int:
        """
        Remove expired challenges (for storage backends without auto-expiration).

        Returns:
            Number of expired challenges removed
        """
        pass


class InMemoryChallengeStore(ChallengeStore):
    """
    In-memory challenge storage for development.

    WARNING: Not suitable for production use:
    - Data lost on server restart
    - Not thread-safe without locks
    - Not scalable across multiple server instances
    """

    def __init__(self):
        self._store: Dict[str, Dict[str, any]] = {}

        # For resilience diagnostics when used as an automatic fallback
        self.fallback_mode = False
        self.memory_store = self._store

    async def set_challenge(
        self, email: str, challenge: str, ttl_minutes: int = 5
    ) -> None:
        expires = datetime.utcnow() + timedelta(minutes=ttl_minutes)
        self._store[email] = {"challenge": challenge, "expires": expires}

    async def get_challenge(self, email: str) -> Optional[str]:
        if email not in self._store:
            return None

        data = self._store[email]
        if datetime.utcnow() > data["expires"]:
            # Expired, remove it
            del self._store[email]
            return None

        return data["challenge"]

    async def delete_challenge(self, email: str) -> bool:
        if email in self._store:
            del self._store[email]
            return True
        return False

    async def cleanup_expired(self) -> int:
        """Remove expired challenges"""
        now = datetime.utcnow()
        expired_keys = [
            email for email, data in self._store.items() if now > data["expires"]
        ]
        for email in expired_keys:
            del self._store[email]
        return len(expired_keys)


class RedisChallengeStore(ChallengeStore):
    """
    Redis-based challenge storage for production.

    Benefits:
    - Automatic TTL expiration
    - Thread-safe operations
    - Scalable across multiple server instances
    - Persistent across server restarts
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        ssl: bool = False,
        key_prefix: str = "passkey:challenge:",
    ):
        """
        Initialize Redis connection.

        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password (if required)
            ssl: Use SSL connection
            key_prefix: Prefix for Redis keys
        """
        import redis

        self.key_prefix = key_prefix
        self.redis = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password if password else None,
            ssl=ssl,
            decode_responses=True,  # Decode bytes to strings
        )

        # Test connection
        try:
            self.redis.ping()
        except redis.ConnectionError as e:
            raise ConnectionError(f"Failed to connect to Redis: {e}")

    @classmethod
    def from_redis_client(cls, redis_client, key_prefix: str = "passkey:challenge:"):
        """
        Create RedisChallengeStore from an existing Redis client.

        Args:
            redis_client: Pre-configured Redis client instance
            key_prefix: Prefix for Redis keys

        Returns:
            RedisChallengeStore instance
        """
        instance = cls.__new__(cls)
        instance.key_prefix = key_prefix
        instance.redis = redis_client
        return instance

    def _make_key(self, email: str) -> str:
        """Generate Redis key for email"""
        return f"{self.key_prefix}{email}"

    async def set_challenge(
        self, email: str, challenge: str, ttl_minutes: int = 5
    ) -> None:
        key = self._make_key(email)
        # Store challenge with automatic expiration
        self.redis.setex(key, timedelta(minutes=ttl_minutes), challenge)

    async def get_challenge(self, email: str) -> Optional[str]:
        key = self._make_key(email)
        challenge = self.redis.get(key)
        return challenge if challenge else None

    async def delete_challenge(self, email: str) -> bool:
        key = self._make_key(email)
        result = self.redis.delete(key)
        return result > 0

    async def cleanup_expired(self) -> int:
        """
        Redis automatically removes expired keys, so this is a no-op.

        Returns:
            0 (Redis handles expiration automatically)
        """
        return 0


def get_challenge_store() -> ChallengeStore:
    """
    Factory function to get the appropriate challenge store based on environment.

    Returns:
        ChallengeStore instance (InMemory for dev, Redis for production)
    """
    use_redis = os.getenv("USE_REDIS_CHALLENGES", "false").lower() == "true"

    logger = logging.getLogger(__name__)

    if use_redis:
        # Wrap Redis-backed store with a resilient fallback that uses in-memory on errors.
        try:
            # Production: Try Redis first
            redis_url = os.getenv("REDIS_URL")
            import redis

            redis_client = None
            if redis_url:
                redis_client = redis.from_url(redis_url)
                # Test connection
                redis_client.ping()
            else:
                # Try individual env vars
                host = os.getenv("REDIS_HOST", "localhost")
                port = int(os.getenv("REDIS_PORT", "6379"))
                db = int(os.getenv("REDIS_DB", "0"))
                password = os.getenv("REDIS_PASSWORD", None)
                ssl = os.getenv("REDIS_SSL", "false").lower() == "true"
                redis_client = redis.Redis(
                    host=host, port=port, db=db, password=password, ssl=ssl
                )
                redis_client.ping()

            # If we get here, redis_client is valid; create a resilient wrapper around it
            return ResilientChallengeStore(redis_client=redis_client)

        except Exception as e:
            # Check if memory fallback is allowed
            if not settings.allow_memory_fallback:
                logger.error(
                    f"Redis not available ({e}) and memory fallback is disabled. "
                    f"Cannot create challenge store in {settings.environment} environment."
                )
                raise ConnectionError(
                    f"Redis connection failed and memory fallback is disabled: {e}"
                ) from e
            
            # Fall back to in-memory if Redis is not available and fallback is allowed
            logger.warning(
                f"Redis not available ({e}), falling back to in-memory challenge store"
            )
            store = ResilientChallengeStore(redis_client=None)
            store.fallback_mode = True
            return store
    else:
        # Development: Use in-memory
        return InMemoryChallengeStore()


# Singleton instance
_challenge_store: Optional[ChallengeStore] = None


def get_challenge_store_instance() -> ChallengeStore:
    """
    Get singleton challenge store instance.

    Returns:
        Shared ChallengeStore instance
    """
    global _challenge_store
    if _challenge_store is None:
        _challenge_store = get_challenge_store()
    return _challenge_store


class ResilientChallengeStore(ChallengeStore):
    """
    Wrapper store that prefers Redis but falls back to in-memory on connection errors.

    Exposes a small `health_check()` method that operators can use to determine
    whether the system is running in fallback mode (unsafe for multi-instance prod).
    """

    def __init__(self, redis_client=None, key_prefix: str = "passkey:challenge:"):
        self.redis = redis_client
        self.key_prefix = key_prefix
        self.memory_store: Dict[str, Dict[str, any]] = {}
        self.fallback_mode = False if redis_client is not None else True

        # Environment detection using config system
        if config_available:
            self.is_production = settings.is_production
            self.instance_count = settings.instance_count
            self.should_alert_on_fallback = settings.should_alert_on_fallback
            self.allow_memory_fallback = settings.allow_memory_fallback
        else:
            # Fallback to environment variables
            self.is_production = (
                os.getenv("ENV", os.getenv("ENVIRONMENT", "development"))
                == "production"
            )
            try:
                self.instance_count = int(os.getenv("INSTANCE_COUNT", "1"))
            except Exception:
                self.instance_count = 1
            self.should_alert_on_fallback = (
                self.is_production and self.instance_count > 1
            )
            self.allow_memory_fallback = os.getenv("ALLOW_MEMORY_FALLBACK", "false").lower() == "true"

        self.logger = logging.getLogger(__name__)

    def _make_key(self, email: str) -> str:
        return f"{self.key_prefix}{email}"

    async def set_challenge(
        self, email: str, challenge: str, ttl_minutes: int = 5
    ) -> None:
        key = self._make_key(email)
        ttl_seconds = int(ttl_minutes * 60)
        # Try Redis first
        if self.redis and not self.fallback_mode:
            try:
                # redis-py setex expects seconds or timedelta
                self.redis.setex(key, timedelta(minutes=ttl_minutes), challenge)
                return
            except Exception as e:
                # Check if memory fallback is allowed
                if not self.allow_memory_fallback:
                    raise ConnectionError(
                        f"Redis connection failed and memory fallback is disabled: {e}"
                    ) from e

                # Fall back to memory
                self.logger.warning(
                    f"Redis error during set_challenge: {e}; falling back to memory storage"
                )
                self.fallback_mode = True
                # alert ops if in multi-instance prod
                if self.should_alert_on_fallback:
                    try:
                        # best-effort alert hook (non-blocking)
                        import asyncio

                        asyncio.create_task(
                            self._alert_ops("Redis down with multi-instance deployment")
                        )
                    except Exception:
                        pass

        # Memory fallback - only if allowed
        if not self.allow_memory_fallback:
            raise ConnectionError("Redis unavailable and memory fallback is disabled")

        expires_at = time.time() + ttl_seconds
        self.memory_store[email] = {"challenge": challenge, "expires_at": expires_at}

    async def get_challenge(self, email: str) -> Optional[str]:
        key = self._make_key(email)
        if self.redis and not self.fallback_mode:
            try:
                value = self.redis.get(key)
                if value:
                    return value
            except Exception as e:
                # Check if memory fallback is allowed
                if not self.allow_memory_fallback:
                    raise ConnectionError(
                        f"Redis connection failed and memory fallback is disabled: {e}"
                    ) from e

                self.logger.warning(
                    f"Redis error during get_challenge: {e}; using memory fallback"
                )
                self.fallback_mode = True

        # Memory fallback - only if allowed
        if not self.allow_memory_fallback:
            raise ConnectionError("Redis unavailable and memory fallback is disabled")

        entry = self.memory_store.get(email)
        if not entry:
            return None
        if time.time() > entry["expires_at"]:
            del self.memory_store[email]
            return None
        return entry["challenge"]

    async def delete_challenge(self, email: str) -> bool:
        key = self._make_key(email)
        deleted = False
        if self.redis and not self.fallback_mode:
            try:
                res = self.redis.delete(key)
                deleted = res and res > 0
            except Exception as e:
                # Check if memory fallback is allowed
                if not self.allow_memory_fallback:
                    raise ConnectionError(
                        f"Redis connection failed and memory fallback is disabled: {e}"
                    ) from e

                self.logger.warning(
                    f"Redis error during delete_challenge: {e}; deleting from memory fallback"
                )
                self.fallback_mode = True

        # Memory fallback - only if allowed
        if not self.allow_memory_fallback:
            raise ConnectionError("Redis unavailable and memory fallback is disabled")

        if email in self.memory_store:
            del self.memory_store[email]
            deleted = True

        return deleted

    async def cleanup_expired(self) -> int:
        now = time.time()
        expired = [
            k for k, v in self.memory_store.items() if now > v.get("expires_at", 0)
        ]
        for k in expired:
            del self.memory_store[k]
        return len(expired)

    def health_check(self) -> dict:
        return {
            "redis_available": not self.fallback_mode,
            "fallback_mode": self.fallback_mode,
            "memory_fallback_allowed": self.allow_memory_fallback,
            "memory_keys": len(self.memory_store),
            "safe_for_production": not self.should_alert_on_fallback or not self.fallback_mode,
            "environment": "production" if self.is_production else "development",
            "instance_count": self.instance_count,
        }

    async def _alert_ops(self, message: str) -> None:
        """Placeholder for signaling operator/monitoring systems (Slack, PagerDuty, etc.)"""
        try:
            # Integrate with real alerting (Datadog, Sentry, PagerDuty) as needed
            self.logger.critical(f"ALERT: {message}")
        except Exception:
            pass
