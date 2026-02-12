#!/usr/bin/env python3
"""
Test script to verify the consolidated provider adapters work correctly.
"""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(__file__))

# Import base adapter
from providers.base_adapter import AdapterBase, ProviderError

# Import adapters with error handling
try:
    from providers.openai_adapter import OpenAIAdapter

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from providers.anthropic_adapter import AnthropicAdapter

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    from providers.ollama_adapter import OllamaAdapter

    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False


async def test_base_adapter():
    """Test the base adapter functionality."""
    print("Testing base adapter...")

    # Test that we can't instantiate the abstract base class
    try:
        AdapterBase("test")
        print("❌ ERROR: Should not be able to instantiate abstract base class")
        return False
    except TypeError:
        print("✅ Base adapter correctly prevents direct instantiation")

    # Test ProviderError
    try:
        raise ProviderError("test_provider", "Test error")
    except ProviderError as e:
        print(f"✅ ProviderError works: {e}")

    return True


async def test_openai_adapter():
    """Test OpenAI adapter inheritance."""
    print("\nTesting OpenAI adapter...")

    # Test with invalid API key (should fail gracefully)
    adapter = OpenAIAdapter("invalid_key")

    # Check inheritance
    assert isinstance(adapter, AdapterBase), (
        "OpenAI adapter should inherit from AdapterBase"
    )
    assert hasattr(adapter, "generate"), "Should have generate method"
    assert hasattr(adapter, "a_generate"), "Should have a_generate method"
    print("✅ OpenAI adapter correctly inherits from base")

    return True


async def test_anthropic_adapter():
    """Test Anthropic adapter inheritance."""
    print("\nTesting Anthropic adapter...")

    # Test with invalid API key (should fail gracefully)
    adapter = AnthropicAdapter("invalid_key")

    # Check inheritance
    assert isinstance(adapter, AdapterBase), (
        "Anthropic adapter should inherit from AdapterBase"
    )
    assert hasattr(adapter, "generate"), "Should have generate method"
    assert hasattr(adapter, "a_generate"), "Should have a_generate method"
    print("✅ Anthropic adapter correctly inherits from base")

    return True


async def test_ollama_adapter():
    """Test Ollama adapter inheritance."""
    print("\nTesting Ollama adapter...")

    adapter = OllamaAdapter()

    # Check inheritance
    assert isinstance(adapter, AdapterBase), (
        "Ollama adapter should inherit from AdapterBase"
    )
    assert hasattr(adapter, "generate"), "Should have generate method"
    assert hasattr(adapter, "a_generate"), "Should have a_generate method"
    print("✅ Ollama adapter correctly inherits from base")

    return True


async def main():
    """Run all tests."""
    print("Running provider adapter consolidation tests...\n")

    tests = [
        test_base_adapter,
        test_openai_adapter,
        test_anthropic_adapter,
        test_ollama_adapter,
    ]

    passed = 0
    for test in tests:
        try:
            if await test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed: {e}")

    print(f"\n{passed}/{len(tests)} tests passed")

    if passed == len(tests):
        print("🎉 All adapter consolidation tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
