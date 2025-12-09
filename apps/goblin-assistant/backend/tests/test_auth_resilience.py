"""
Comprehensive Auth Resilience Tests

Tests Redis fallback scenarios, recovery mechanisms, and multi-instance safety checks.
"""

import pytest
from unittest.mock import patch
from pydantic import ValidationError

from auth.challenge_store import RedisChallengeStore, MemoryChallengeStore
from auth.router import UserRegistration


class TestAuthResilience:
    """Test auth system resilience and fallback mechanisms"""

    @pytest.mark.asyncio
    async def test_redis_fallback_activates(self):
        """Test that memory fallback activates when Redis fails"""
        store = RedisChallengeStore()

        with patch.object(store.redis_client, "setex", side_effect=ConnectionError):
            success = await store.store_challenge("test_key", "test_value")
            assert success
            assert store.fallback_mode

    @pytest.mark.asyncio
    async def test_redis_recovery(self):
        """Test that system recovers when Redis comes back"""
        store = RedisChallengeStore()
        store.fallback_mode = True

        # Redis works again
        with patch.object(store.redis_client, "setex", return_value=True):
            await store.store_challenge("test_key", "test_value")
            assert not store.fallback_mode

    @pytest.mark.asyncio
    async def test_multi_instance_warning(self, caplog):
        """Test warning is logged in multi-instance production"""
        with (
            patch("config.settings.environment", "production"),
            patch("config.settings.instance_count", 3),
            patch("config.settings.is_multi_instance", True),
        ):
            store = RedisChallengeStore()

            with patch.object(store.redis_client, "setex", side_effect=ConnectionError):
                await store.store_challenge("key", "value")

                assert "CRITICAL" in caplog.text
                assert "Multi-instance" in caplog.text

    @pytest.mark.asyncio
    async def test_memory_store_always_available(self):
        """Test that memory store provides basic functionality"""
        store = MemoryChallengeStore()

        # Store and retrieve
        await store.store_challenge("email@test.com", "challenge123")
        retrieved = await store.get_challenge("email@test.com")

        assert retrieved == "challenge123"

    @pytest.mark.asyncio
    async def test_memory_store_expiration(self):
        """Test that memory store respects TTL"""
        store = MemoryChallengeStore()

        await store.store_challenge("email@test.com", "challenge123", ttl_minutes=0)
        retrieved = await store.get_challenge("email@test.com")

        assert retrieved is None  # Should have expired


class TestEmailValidation:
    """Test email validation and disposable domain blocking"""

    def test_pydantic_email_validation(self):
        """Test that pydantic[email] is available and working"""
        from pydantic import EmailStr, BaseModel

        class TestModel(BaseModel):
            email: EmailStr

        # Valid email
        valid = TestModel(email="test@example.com")
        assert valid.email == "test@example.com"

        # Invalid email should raise ValidationError
        with pytest.raises(ValidationError):
            TestModel(email="invalid-email")

    def test_disposable_email_rejection(self):
        """Test custom domain validation blocks disposable emails"""
        # Valid email
        user = UserRegistration(email="test@example.com", username="testuser")
        assert user.email

        # Disposable email should be rejected
        with pytest.raises(ValidationError, match="Disposable"):
            UserRegistration(email="test@tempmail.com", username="testuser")

        # Another disposable domain
        with pytest.raises(ValidationError, match="Disposable"):
            UserRegistration(email="test@10minutemail.com", username="testuser")

    def test_case_insensitive_domain_check(self):
        """Test that domain checking is case insensitive"""
        with pytest.raises(ValidationError, match="Disposable"):
            UserRegistration(email="test@TEMPMail.COM", username="testuser")


class TestConfigurationValidation:
    """Test configuration validation and environment checks"""

    def test_production_requires_database_url(self):
        """Test that production environment validates DATABASE_URL"""
        with (
            patch("config.settings.environment", "production"),
            patch("config.settings.database_url", ""),
        ):
            with pytest.raises(ValueError, match="DATABASE_URL is required"):
                # This should trigger validation
                from config import validate_environment_config

                validate_environment_config()

    def test_multi_instance_production_no_memory_fallback(self):
        """Test that multi-instance production doesn't allow memory fallback"""
        with (
            patch("config.settings.environment", "production"),
            patch("config.settings.instance_count", 3),
            patch("config.settings.allow_memory_fallback", True),
        ):
            with pytest.raises(ValueError, match="Memory fallback not allowed"):
                from config import validate_environment_config

                validate_environment_config()

    def test_development_allows_flexibility(self):
        """Test that development environment is more permissive"""
        with (
            patch("config.settings.environment", "development"),
            patch("config.settings.database_url", ""),
            patch("config.settings.allow_memory_fallback", True),
        ):
            # Should not raise any errors
            from config import validate_environment_config

            validate_environment_config()


class TestHealthCheckIntegration:
    """Test health check endpoints work correctly"""

    @pytest.mark.asyncio
    async def test_comprehensive_health_includes_components(self, client):
        """Test that comprehensive health check includes all components"""
        response = await client.get("/health/")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "environment" in data
        assert "components" in data

        # Check required components
        components = data["components"]
        assert "redis" in components
        assert "database" in components
        assert "auth_routes" in components
        assert "configuration" in components

    @pytest.mark.asyncio
    async def test_health_status_determination(self, client):
        """Test that overall health status is correctly determined"""
        response = await client.get("/health/")
        assert response.status_code == 200

        data = response.json()
        status = data["status"]

        # Status should be one of the expected values
        assert status in ["healthy", "degraded", "unhealthy"]

        # If any component is unhealthy, overall should be unhealthy
        components = data["components"]
        has_unhealthy = any(c.get("status") == "unhealthy" for c in components.values())

        if has_unhealthy:
            assert status == "unhealthy"
