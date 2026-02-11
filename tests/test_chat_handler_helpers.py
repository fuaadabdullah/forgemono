import sys
import os

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "apps", "goblin-assistant")
)

import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from backend.services.chat_handler_helpers import (
    resolve_provider_instance,
    validate_and_check_limits,
)


class TestResolveProviderInstance:
    """Test cases for resolve_provider_instance function."""

    def test_resolve_provider_instance_success(self):
        """Test successful provider resolution."""
        provider_config = {"provider_name": "test_provider", "api_key": "test_key"}

        mock_provider_class = MagicMock()
        mock_provider_instance = MagicMock()
        mock_provider_class.return_value = mock_provider_instance

        with patch(
            "apps.goblin_assistant.backend.services.chat_handler_helpers.get_provider_class"
        ) as mock_get_class:
            mock_get_class.return_value = mock_provider_class

            result = resolve_provider_instance(provider_config)

            mock_get_class.assert_called_once_with("test_provider")
            mock_provider_class.assert_called_once_with(provider_config)
            assert result == mock_provider_instance

    def test_resolve_provider_instance_missing_provider_name(self):
        """Test provider resolution with missing provider_name."""
        provider_config = {"api_key": "test_key"}

        with pytest.raises(
            ValueError, match="Invalid provider configuration: missing 'provider_name'"
        ):
            resolve_provider_instance(provider_config)

    def test_resolve_provider_instance_get_provider_class_failure(self):
        """Test provider resolution when get_provider_class fails."""
        provider_config = {"provider_name": "invalid_provider", "api_key": "test_key"}

        with patch(
            "apps.goblin_assistant.backend.services.chat_handler_helpers.get_provider_class"
        ) as mock_get_class:
            mock_get_class.side_effect = Exception("Provider not found")

            with pytest.raises(
                ValueError, match="Provider resolution failed: Provider not found"
            ):
                resolve_provider_instance(provider_config)

    def test_resolve_provider_instance_instantiation_failure(self):
        """Test provider resolution when provider instantiation fails."""
        provider_config = {"provider_name": "test_provider", "api_key": "test_key"}

        mock_provider_class = MagicMock()
        mock_provider_class.side_effect = Exception("Instantiation failed")

        with patch(
            "apps.goblin_assistant.backend.services.chat_handler_helpers.get_provider_class"
        ) as mock_get_class:
            mock_get_class.return_value = mock_provider_class

            with pytest.raises(
                ValueError, match="Provider resolution failed: Instantiation failed"
            ):
                resolve_provider_instance(provider_config)


class TestValidateAndCheckLimits:
    """Test cases for validate_and_check_limits function."""

    @pytest.mark.asyncio
    async def test_validate_and_check_limits_success(self):
        """Test successful validation and rate limit check."""
        mock_validator = MagicMock()
        mock_rate_limiter = MagicMock()
        mock_error_formatter = MagicMock()

        # Setup mocks
        mock_validation_result = MagicMock()
        mock_validation_result.is_valid = True
        mock_validator.validate_chat_request.return_value = mock_validation_result

        mock_rate_limit_result = MagicMock()
        mock_rate_limit_result.allowed = True
        mock_rate_limiter.check_rate_limit.return_value = mock_rate_limit_result

        # Test
        await validate_and_check_limits(
            mock_validator,
            mock_rate_limiter,
            mock_error_formatter,
            messages=[{"role": "user", "content": "test"}],
            model="test-model",
            temperature=0.7,
            max_tokens=100,
            stream=False,
            user_id="user123",
            client_ip="127.0.0.1",
            session_id="session123",
        )

        # Verify calls
        mock_validator.validate_chat_request.assert_called_once()
        mock_rate_limiter.check_rate_limit.assert_called_once_with(
            "user123", "127.0.0.1", "session123"
        )

    @pytest.mark.asyncio
    async def test_validate_and_check_limits_validation_failure(self):
        """Test validation failure raises HTTPException."""
        mock_validator = MagicMock()
        mock_rate_limiter = MagicMock()
        mock_error_formatter = MagicMock()

        # Setup mocks for validation failure
        mock_validation_result = MagicMock()
        mock_validation_result.is_valid = False
        mock_validation_result.errors = ["Invalid message format"]
        mock_validator.validate_chat_request.return_value = mock_validation_result

        mock_error_formatter.format_validation_error.return_value = "Validation error"

        # Test
        with pytest.raises(HTTPException) as exc_info:
            await validate_and_check_limits(
                mock_validator,
                mock_rate_limiter,
                mock_error_formatter,
                messages=[{"role": "user", "content": "test"}],
                model="test-model",
                temperature=0.7,
                max_tokens=100,
                stream=False,
            )

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Validation error"

    @pytest.mark.asyncio
    async def test_validate_and_check_limits_rate_limit_exceeded(self):
        """Test rate limit exceeded raises HTTPException."""
        mock_validator = MagicMock()
        mock_rate_limiter = MagicMock()
        mock_error_formatter = MagicMock()

        # Setup mocks for successful validation but rate limit failure
        mock_validation_result = MagicMock()
        mock_validation_result.is_valid = True
        mock_validator.validate_chat_request.return_value = mock_validation_result

        mock_rate_limit_result = MagicMock()
        mock_rate_limit_result.allowed = False
        mock_rate_limit_result.retry_after = 60
        mock_rate_limiter.check_rate_limit.return_value = mock_rate_limit_result

        mock_error_formatter.format_rate_limit_error.return_value = (
            "Rate limit exceeded"
        )

        # Test
        with pytest.raises(HTTPException) as exc_info:
            await validate_and_check_limits(
                mock_validator,
                mock_rate_limiter,
                mock_error_formatter,
                messages=[{"role": "user", "content": "test"}],
                model="test-model",
                temperature=0.7,
                max_tokens=100,
                stream=False,
            )

        assert exc_info.value.status_code == 429
        assert exc_info.value.detail == "Rate limit exceeded"
