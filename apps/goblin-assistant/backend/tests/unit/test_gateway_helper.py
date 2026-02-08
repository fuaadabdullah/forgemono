import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
import sys
from unittest.mock import MagicMock as MockMagicMock

# Mock the modules before importing
sys.modules["backend.config"] = MockMagicMock()
sys.modules["backend.errors"] = MockMagicMock()
sys.modules["backend.services"] = MockMagicMock()
sys.modules["gateway_service"] = MockMagicMock()

# Now import the function
from backend.chat_router import _check_gateway_and_prepare
from backend.services.request_validation import ChatCompletionRequest, ChatMessage


@pytest.mark.asyncio
async def test_check_gateway_and_prepare_valid_request():
    """Test successful gateway check and preparation."""
    # Mock request
    request = ChatCompletionRequest(
        messages=[ChatMessage(role="user", content="Hello")]
    )

    # Mock gateway service
    gateway_service = MagicMock()
    gateway_result = MagicMock()
    gateway_result.intent.value = "chat"
    gateway_result.estimated_tokens = 10
    gateway_result.risk_score = 0.1
    gateway_result.allowed = True
    gateway_service.process_request = AsyncMock(return_value=gateway_result)

    # Mock config_processor
    import backend.chat_router as chat_router

    chat_router.config_processor.prepare_messages = MagicMock(
        return_value=[{"role": "user", "content": "Hello"}]
    )
    chat_router.request_validation.validate_chat_request = MagicMock()

    # Call the function
    messages, result = await _check_gateway_and_prepare(request, gateway_service)

    # Assertions
    assert messages == [{"role": "user", "content": "Hello"}]
    assert result == gateway_result
    chat_router.request_validation.validate_chat_request.assert_called_once_with(
        request
    )
    chat_router.config_processor.prepare_messages.assert_called_once_with(request)
    gateway_service.process_request.assert_called_once()


@pytest.mark.asyncio
async def test_check_gateway_and_prepare_denied_request():
    """Test gateway check that denies the request."""
    # Mock request
    request = ChatCompletionRequest(
        messages=[ChatMessage(role="user", content="Hello")]
    )

    # Mock gateway service
    gateway_service = MagicMock()
    gateway_result = MagicMock()
    gateway_result.allowed = False
    gateway_service.process_request = AsyncMock(return_value=gateway_result)

    # Mock config_processor
    import backend.chat_router as chat_router

    chat_router.config_processor.prepare_messages = MagicMock(
        return_value=[{"role": "user", "content": "Hello"}]
    )
    chat_router.request_validation.validate_chat_request = MagicMock()

    # Call the function and expect exception
    with pytest.raises(HTTPException) as exc_info:
        await _check_gateway_and_prepare(request, gateway_service)

    assert exc_info.value.status_code == 400
    assert "high-risk" in exc_info.value.detail
