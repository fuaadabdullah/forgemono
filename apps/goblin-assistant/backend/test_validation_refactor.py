#!/usr/bin/env python3
"""
Test script to verify the refactored validation functions work correctly.
This script tests the cognitive complexity reduction changes.
"""

import sys
import os
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# Mock the raise_validation_error function since we can't import backend.errors
def mock_raise_validation_error(message, errors=None):
    """Mock validation error function for testing."""
    if errors:
        error_msg = f"{message}: {errors}"
    else:
        error_msg = message
    raise ValueError(error_msg)


# Patch the import before importing request_validation
import sys

sys.modules["backend.errors"] = type(
    "MockModule", (), {"raise_validation_error": mock_raise_validation_error}
)()

from services.request_validation import (
    ChatCompletionRequest,
    ChatMessage,
    validate_chat_request,
    validate_temperature,
    validate_max_tokens,
    validate_top_p,
    validate_latency_target,
    validate_intent,
    ValidationError,
    ValidationContext,
)


def test_message_validation():
    """Test message validation functions."""
    print("Testing message validation...")

    # Test valid messages
    valid_messages = [
        ChatMessage(role="user", content="Hello"),
        ChatMessage(role="assistant", content="Hi there"),
    ]

    try:
        request = ChatCompletionRequest(messages=valid_messages)
        validate_chat_request(request)
        print("✓ Valid messages passed validation")
    except Exception as e:
        print(f"✗ Valid messages failed: {e}")
        return False

    # Test empty messages
    try:
        request = ChatCompletionRequest(messages=[])
        validate_chat_request(request)
        print("✗ Empty messages should have failed")
        return False
    except Exception:
        print("✓ Empty messages correctly failed validation")

    # Test too many messages
    try:
        many_messages = [ChatMessage(role="user", content="test")] * 51
        request = ChatCompletionRequest(messages=many_messages)
        validate_chat_request(request)
        print("✗ Too many messages should have failed")
        return False
    except Exception:
        print("✓ Too many messages correctly failed validation")

    # Test empty content
    try:
        messages = [ChatMessage(role="user", content="")]
        request = ChatCompletionRequest(messages=messages)
        validate_chat_request(request)
        print("✗ Empty content should have failed")
        return False
    except Exception:
        print("✓ Empty content correctly failed validation")

    # Test invalid role
    try:
        messages = [ChatMessage(role="invalid", content="test")]
        request = ChatCompletionRequest(messages=messages)
        validate_chat_request(request)
        print("✗ Invalid role should have failed")
        return False
    except Exception:
        print("✓ Invalid role correctly failed validation")

    return True


def test_parameter_validation():
    """Test individual parameter validation functions."""
    print("\nTesting parameter validation...")

    # Test temperature
    try:
        result = validate_temperature(0.5)
        assert math.isclose(result, 0.5)
        print("✓ Valid temperature passed")
    except Exception as e:
        print(f"✗ Valid temperature failed: {e}")
        return False

    try:
        result = validate_temperature(None)
        assert math.isclose(result, 0.2)
        print("✓ None temperature defaulted correctly")
    except Exception as e:
        print(f"✗ None temperature failed: {e}")
        return False

    try:
        validate_temperature(-1)
        print("✗ Invalid temperature should have failed")
        return False
    except Exception:
        print("✓ Invalid temperature correctly failed")

    # Test max_tokens
    try:
        result = validate_max_tokens(100)
        assert result == 100
        print("✓ Valid max_tokens passed")
    except Exception as e:
        print(f"✗ Valid max_tokens failed: {e}")
        return False

    try:
        result = validate_max_tokens(None)
        assert result == 512
        print("✓ None max_tokens defaulted correctly")
    except Exception as e:
        print(f"✗ None max_tokens failed: {e}")
        return False

    try:
        validate_max_tokens(0)
        print("✗ Invalid max_tokens should have failed")
        return False
    except Exception:
        print("✓ Invalid max_tokens correctly failed")

    # Test top_p
    try:
        result = validate_top_p(0.8)
        assert math.isclose(result, 0.8)
        print("✓ Valid top_p passed")
    except Exception as e:
        print(f"✗ Valid top_p failed: {e}")
        return False

    try:
        result = validate_top_p(None)
        assert math.isclose(result, 0.95)
        print("✓ None top_p defaulted correctly")
    except Exception as e:
        print(f"✗ None top_p failed: {e}")
        return False

    try:
        validate_top_p(1.5)
        print("✗ Invalid top_p should have failed")
        return False
    except Exception:
        print("✓ Invalid top_p correctly failed")

    # Test latency_target
    try:
        result = validate_latency_target("low")
        assert result == "low"
        print("✓ Valid latency_target passed")
    except Exception as e:
        print(f"✗ Valid latency_target failed: {e}")
        return False

    try:
        result = validate_latency_target(None)
        assert result == "medium"
        print("✓ None latency_target defaulted correctly")
    except Exception as e:
        print(f"✗ None latency_target failed: {e}")
        return False

    try:
        validate_latency_target("invalid")
        print("✗ Invalid latency_target should have failed")
        return False
    except Exception:
        print("✓ Invalid latency_target correctly failed")

    # Test intent
    try:
        result = validate_intent("code-gen")
        assert result == "code-gen"
        print("✓ Valid intent passed")
    except Exception as e:
        print(f"✗ Valid intent failed: {e}")
        return False

    try:
        result = validate_intent(None)
        assert result is None
        print("✓ None intent passed correctly")
    except Exception as e:
        print(f"✗ None intent failed: {e}")
        return False

    try:
        validate_intent("invalid")
        print("✗ Invalid intent should have failed")
        return False
    except Exception:
        print("✓ Invalid intent correctly failed")

    return True


def test_pydanmodel_validation():
    """Test Pydantic model validation."""
    print("\nTesting Pydantic model validation...")

    # Test valid request
    try:
        request = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="Hello")],
            temperature=0.5,
            max_tokens=100,
            top_p=0.8,
            latency_target="low",
            intent="code-gen",
        )
        assert request is not None
        print("✓ Valid request created successfully")
    except Exception as e:
        print(f"✗ Valid request failed: {e}")
        return False

    # Test invalid temperature
    try:
        _ = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="Hello")], temperature=-1
        )
        print("✗ Invalid temperature should have failed")
        return False
    except Exception:
        print("✓ Invalid temperature correctly failed")

    # Test invalid max_tokens
    try:
        _ = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="Hello")], max_tokens=0
        )
        print("✗ Invalid max_tokens should have failed")
        return False
    except Exception:
        print("✓ Invalid max_tokens correctly failed")

    return True


def main():
    """Run all tests."""
    print("Running validation refactoring tests...\n")

    tests = [
        test_message_validation,
        test_parameter_validation,
        test_pydanmodel_validation,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print(f"\nTest Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Refactoring successful.")
        return True
    else:
        print("❌ Some tests failed. Please review the refactoring.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
