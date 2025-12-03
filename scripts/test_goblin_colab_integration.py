#!/usr/bin/env python3
"""
Test Goblin Assistant API Integration with Colab llama.cpp

This script tests that the Goblin Assistant backend can successfully
route requests to the Colab-deployed llama.cpp server.

Usage:
    python3 test_goblin_colab_integration.py --backend-url http://localhost:8000

Requirements:
    pip install requests
"""

import argparse
import requests
import sys


def test_routing_health(backend_url: str) -> bool:
    """Test that the routing system is healthy."""
    try:
        response = requests.get(f"{backend_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Backend healthy")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False


def test_provider_availability(backend_url: str) -> bool:
    """Test that llamacpp_colab is available as a provider."""
    try:
        response = requests.get(f"{backend_url}/routing/providers", timeout=10)
        if response.status_code == 200:
            providers = response.json()
            if "llamacpp_colab" in providers:
                print("✅ llamacpp_colab provider available")
                return True
            else:
                print(f"❌ llamacpp_colab not in providers: {providers}")
                return False
        else:
            print(f"❌ Provider list failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Provider check error: {e}")
        return False


def test_chat_routing(backend_url: str) -> bool:
    """Test routing a chat request to the Colab server."""
    try:
        payload = {
            "task_type": "chat",
            "payload": {
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello! This is a test from Goblin Assistant API.",
                    }
                ],
                "provider": "llamacpp_colab",
                "max_tokens": 100,
            }
        }

        print("🧪 Testing chat routing to Colab llama.cpp...")
        response = requests.post(
            f"{backend_url}/routing/route", json=payload, timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            if "result" in result and "text" in result["result"]:
                print("✅ Successfully routed to llamacpp_colab")
                text = result["result"]["text"]
                # Check if it's not just garbled characters
                if len(text.strip()) > 0 and not all(c in '\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f' for c in text):
                    print(f"   Response: {text[:100]}...")
                    return True
                else:
                    print(f"❌ Response appears garbled: {repr(text[:50])}")
                    return False
            else:
                print(f"❌ Invalid response format: {result}")
                return False
        else:
            print(f"❌ Route request failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"❌ Chat routing test error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Test Goblin Assistant Colab integration"
    )
    parser.add_argument(
        "--backend-url",
        default="http://localhost:8000",
        help="Goblin Assistant backend URL",
    )

    args = parser.parse_args()

    print("🔗 Testing Goblin Assistant + Colab llama.cpp Integration")
    print("=" * 60)

    tests = [
        ("Routing System Health", test_routing_health),
        ("Provider Availability", test_provider_availability),
        ("Chat Routing", test_chat_routing),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\\n{test_name}:")
        if test_func(args.backend_url):
            passed += 1

    print("\\n" + "=" * 60)
    print(f"Integration Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 Full integration successful!")
        print("Goblin Assistant can now route requests to your Colab llama.cpp server.")
    else:
        print("⚠️  Some integration tests failed.")
        print("Check that:")
        print("1. The Goblin Assistant backend is running")
        print("2. The Colab server is accessible")
        print("3. The provider configuration is correct")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
