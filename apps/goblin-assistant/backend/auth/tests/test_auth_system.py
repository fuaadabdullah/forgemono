"""
Tests for the simplified auth system.

Tests JWT token creation/validation and API key management.
"""

import pytest
from datetime import datetime, timedelta
from auth.policies import AuthScope, UserRole, get_scopes_for_role
from auth.api_key_store import APIKeyStore
from auth_service import JWTAuthService


class TestAuthPolicies:
    """Test authentication policies and scopes."""

    def test_user_role_scopes(self):
        """Test that user roles have correct default scopes."""
        user_scopes = get_scopes_for_role(UserRole.USER)
        assert AuthScope.READ_USER in user_scopes
        assert AuthScope.WRITE_CONVERSATIONS in user_scopes
        assert AuthScope.ADMIN_SYSTEM not in user_scopes

        admin_scopes = get_scopes_for_role(UserRole.ADMIN)
        assert AuthScope.ADMIN_SYSTEM in admin_scopes
        assert len(admin_scopes) > len(user_scopes)

    def test_service_role_scopes(self):
        """Test that service role has limited scopes."""
        service_scopes = get_scopes_for_role(UserRole.SERVICE)
        assert AuthScope.SERVICE_INFERENCE in service_scopes
        assert AuthScope.READ_USER not in service_scopes


class TestJWTAuthService:
    """Test JWT token operations."""

    @pytest.fixture
    def auth_service(self):
        """Create a test auth service."""
        return JWTAuthService()

    def test_create_access_token(self, auth_service):
        """Test access token creation."""
        user_id = "test-user-123"
        email = "test@example.com"
        role = UserRole.USER

        token = auth_service.create_access_token(user_id, email, role)

        assert isinstance(token, str)
        assert len(token) > 0

        # Validate the token
        claims = auth_service.validate_access_token(token)
        assert claims is not None
        assert claims["sub"] == user_id
        assert claims["email"] == email
        assert claims["role"] == role.value
        assert claims["type"] == "access"
        assert "scopes" in claims

    def test_create_refresh_token(self, auth_service):
        """Test refresh token creation."""
        user_id = "test-user-123"

        token = auth_service.create_refresh_token(user_id)

        assert isinstance(token, str)
        assert len(token) > 0

        # Validate the token
        user_id_from_token = auth_service.validate_refresh_token(token)
        assert user_id_from_token == user_id

    def test_token_validation(self, auth_service):
        """Test token validation."""
        # Create valid token
        user_id = "test-user-123"
        email = "test@example.com"
        role = UserRole.USER

        valid_token = auth_service.create_access_token(user_id, email, role)

        # Test valid token
        claims = auth_service.validate_access_token(valid_token)
        assert claims is not None
        assert claims["sub"] == user_id

        # Test invalid token
        invalid_claims = auth_service.validate_access_token("invalid.token.here")
        assert invalid_claims is None

    def test_scope_checking(self, auth_service):
        """Test scope checking methods."""
        user_id = "test-user-123"
        email = "test@example.com"
        role = UserRole.USER

        token = auth_service.create_access_token(user_id, email, role)
        claims = auth_service.validate_access_token(token)

        # User should have read user scope
        assert auth_service.has_scope(claims, AuthScope.READ_USER)

        # User should not have admin scope
        assert not auth_service.has_scope(claims, AuthScope.ADMIN_SYSTEM)

        # Test has_any_scope
        required_scopes = {AuthScope.READ_USER, AuthScope.ADMIN_SYSTEM}
        assert auth_service.has_any_scope(claims, required_scopes)

        # Test has_all_scopes
        assert not auth_service.has_all_scopes(claims, required_scopes)


class TestAPIKeyStore:
    """Test API key storage and management."""

    @pytest.fixture
    def key_store(self, tmp_path):
        """Create a test API key store."""
        storage_path = tmp_path / "api_keys.enc"
        return APIKeyStore(str(storage_path))

    def test_create_and_verify_key(self, key_store):
        """Test API key creation and verification."""
        name = "test-key"
        scopes = ["read:user", "write:conversations"]

        key_id, actual_key = key_store.create_key(name, scopes)

        assert isinstance(key_id, str)
        assert isinstance(actual_key, str)
        assert len(actual_key) > 0

        # Verify the key
        key_obj = key_store.verify_key(actual_key)
        assert key_obj is not None
        assert key_obj.key_id == key_id
        assert key_obj.name == name
        assert key_obj.scopes == scopes
        assert key_obj.active

    def test_key_revocation(self, key_store):
        """Test API key revocation."""
        name = "test-key"
        scopes = ["read:user"]

        key_id, actual_key = key_store.create_key(name, scopes)

        # Verify key works initially
        key_obj = key_store.verify_key(actual_key)
        assert key_obj is not None

        # Revoke the key
        success = key_store.revoke_key(key_id)
        assert success

        # Verify key no longer works
        key_obj = key_store.verify_key(actual_key)
        assert key_obj is None

    def test_key_expiration(self, key_store):
        """Test API key expiration."""
        name = "test-key"
        scopes = ["read:user"]

        # Create key that expires in 1 day
        key_id, actual_key = key_store.create_key(name, scopes, expires_in_days=1)

        # Verify key works initially
        key_obj = key_store.verify_key(actual_key)
        assert key_obj is not None
        assert not key_obj.is_expired()

        # Simulate expiration by modifying the key
        keys = key_store._load_keys()
        keys[key_id].expires_at = datetime.utcnow() - timedelta(days=1)
        key_store._save_keys(keys)

        # Verify key is now expired
        key_obj = key_store.verify_key(actual_key)
        assert key_obj is None

    def test_list_keys(self, key_store):
        """Test listing API keys."""
        # Create a few keys
        key_store.create_key("key1", ["read:user"])
        key_store.create_key("key2", ["write:conversations"])
        key_store.create_key("key3", ["admin:system"], expires_in_days=1)

        # List active keys
        keys = key_store.list_keys()
        assert len(keys) == 3

        # List all keys including inactive
        all_keys = key_store.list_keys(include_inactive=True)
        assert len(all_keys) == 3

    def test_key_rotation(self, key_store):
        """Test API key rotation."""
        name = "test-key"
        scopes = ["read:user"]

        key_id, old_key = key_store.create_key(name, scopes)

        # Rotate the key
        new_key_id, new_key = key_store.rotate_key(key_id)

        assert new_key_id == key_id
        assert new_key != old_key

        # Old key should no longer work
        old_key_obj = key_store.verify_key(old_key)
        assert old_key_obj is None

        # New key should work
        new_key_obj = key_store.verify_key(new_key)
        assert new_key_obj is not None
        assert new_key_obj.key_id == key_id
