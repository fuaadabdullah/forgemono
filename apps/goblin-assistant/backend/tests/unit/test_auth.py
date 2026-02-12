"""
Unit tests for authentication functions.

Tests auth logic without external dependencies.
"""

import pytest
from unittest.mock import Mock, patch
from auth.challenge_store import RedisChallengeStore, InMemoryChallengeStore


class TestInMemoryChallengeStore:
    """Test in-memory challenge store."""

    @pytest.mark.asyncio
    async def test_store_and_verify_challenge(self):
        """Test storing and verifying a challenge."""
        store = InMemoryChallengeStore()

        email = "test@example.com"
        challenge = "test-challenge-data"

        # Store challenge
        await store.set_challenge(email, challenge, ttl_minutes=5)

        # Verify challenge exists
        retrieved = await store.get_challenge(email)
        assert retrieved == challenge

        # Verify challenge is removed after deletion
        deleted = await store.delete_challenge(email)
        assert deleted is True
        assert await store.get_challenge(email) is None

    @pytest.mark.asyncio
    async def test_challenge_expiration(self):
        """Test that challenges expire."""
        store = InMemoryChallengeStore()

        email = "test@example.com"
        challenge = "test-challenge-data"

        # Store with very short TTL
        await store.set_challenge(email, challenge, ttl_minutes=0)

        # Wait for expiration (TTL=0 means immediate expiration)
        import asyncio

        await asyncio.sleep(0.01)

        # Challenge should be expired
        assert await store.get_challenge(email) is None


class TestRedisChallengeStore:
    """Test Redis-backed challenge store."""

    @pytest.mark.asyncio
    async def test_redis_basic_operations(self, mock_redis):
        """Test basic Redis store operations."""
        with patch("auth.challenge_store.aioredis") as mock_aioredis:
            mock_aioredis.from_url.return_value = mock_redis
            store = RedisChallengeStore()

            email = "test@example.com"
            challenge = "test-challenge-data"

            # Store challenge
            await store.set_challenge(email, challenge, ttl_minutes=5)

            # Verify challenge exists
            retrieved = await store.get_challenge(email)
            assert retrieved == challenge

            # Verify challenge is removed after deletion
            deleted = await store.delete_challenge(email)
            assert deleted is True
            assert await store.get_challenge(email) is None

    @pytest.mark.asyncio
    async def test_redis_health_check(self, mock_redis):
        """Test Redis health check functionality."""
        # Add info method to mock
        mock_redis.info = lambda section: {
            "used_memory_human": "1MB",
            "clients": {"connected_clients": 5},
            "server": {"uptime_in_seconds": 3600},
        }

        with patch("auth.challenge_store.aioredis") as mock_aioredis:
            mock_aioredis.from_url.return_value = mock_redis
            store = RedisChallengeStore()

            health = await store.health_check()
            print(f"Health check result: {health}")  # Debug print

            assert health["redis_available"] is True
            assert "memory_used" in health
            assert "memory_peak" in health
            assert "uptime_seconds" in health
