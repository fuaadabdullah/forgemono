"""
Tests for chat router validation functions.
"""

import pytest
from fastapi import HTTPException
from chat_router import validate_chat_request, ChatCompletionRequest, ChatMessage


class TestChatValidation:
    """Test chat request validation."""

    def test_validate_chat_request_valid(self):
        """Test validation of valid chat request."""
        request = ChatCompletionRequest(
            messages=[
                ChatMessage(role="user", content="Hello"),
                ChatMessage(role="assistant", content="Hi there"),
            ]
        )

        # Should not raise any exception
        validate_chat_request(request)

    def test_validate_chat_request_no_messages(self):
        """Test validation fails with no messages."""
        request = ChatCompletionRequest(messages=[])

        with pytest.raises(HTTPException) as exc_info:
            validate_chat_request(request)

        assert exc_info.value.status_code == 400
        problem = exc_info.value.detail
        assert "messages" in problem["errors"]

    def test_validate_chat_request_empty_content(self):
        """Test validation fails with empty message content."""
        request = ChatCompletionRequest(
            messages=[
                ChatMessage(role="user", content=""),
                ChatMessage(role="user", content="   "),
            ]
        )

        with pytest.raises(HTTPException) as exc_info:
            validate_chat_request(request)

        assert exc_info.value.status_code == 400
        problem = exc_info.value.detail
        assert "messages" in problem["errors"]

    def test_validate_chat_request_too_many_messages(self):
        """Test validation fails with too many messages."""
        messages = [ChatMessage(role="user", content=f"Message {i}") for i in range(51)]
        request = ChatCompletionRequest(messages=messages)

        with pytest.raises(HTTPException) as exc_info:
            validate_chat_request(request)

        assert exc_info.value.status_code == 400
        problem = exc_info.value.detail
        assert "messages" in problem["errors"]

    def test_validate_chat_request_message_too_long(self):
        """Test validation fails with message too long."""
        long_content = "x" * 10001  # 10KB + 1
        request = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content=long_content)]
        )

        with pytest.raises(HTTPException) as exc_info:
            validate_chat_request(request)

        assert exc_info.value.status_code == 400
        problem = exc_info.value.detail
        assert "messages" in problem["errors"]

    def test_validate_chat_request_total_content_too_long(self):
        """Test validation fails with total content too long."""
        # Create messages that total more than 50KB
        messages = [ChatMessage(role="user", content="x" * 15000) for _ in range(4)]
        request = ChatCompletionRequest(messages=messages)

        with pytest.raises(HTTPException) as exc_info:
            validate_chat_request(request)

        assert exc_info.value.status_code == 400
        problem = exc_info.value.detail
        assert "messages" in problem["errors"]

    def test_validate_chat_request_invalid_temperature(self):
        """Test validation fails with invalid temperature."""
        request = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="Hello")],
            temperature=3.0,  # Invalid: > 2
        )

        with pytest.raises(HTTPException) as exc_info:
            validate_chat_request(request)

        assert exc_info.value.status_code == 400
        problem = exc_info.value.detail
        assert "temperature" in problem["errors"]

    def test_validate_chat_request_invalid_max_tokens(self):
        """Test validation fails with invalid max_tokens."""
        request = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="Hello")],
            max_tokens=5000,  # Invalid: > 4096
        )

        with pytest.raises(HTTPException) as exc_info:
            validate_chat_request(request)

        assert exc_info.value.status_code == 400
        problem = exc_info.value.detail
        assert "max_tokens" in problem["errors"]

    def test_validate_chat_request_invalid_top_p(self):
        """Test validation fails with invalid top_p."""
        request = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="Hello")],
            top_p=1.5,  # Invalid: > 1
        )

        with pytest.raises(HTTPException) as exc_info:
            validate_chat_request(request)

        assert exc_info.value.status_code == 400
        problem = exc_info.value.detail
        assert "top_p" in problem["errors"]
