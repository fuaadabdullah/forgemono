#!/usr/bin/env python3
"""
Quick Test Script for llama.cpp Server

This script performs basic connectivity and functionality tests
against a running llama.cpp server.

Usage:
    python3 test_llamacpp_server.py --server-url http://localhost:8080

Requirements:
    pip install requests
"""

import argparse
import requests
import json
import sys


def test_server_connectivity(server_url: str) -> bool:
    """Test basic server connectivity."""
    try:
        health_url = f"{server_url}/health"
        response = requests.get(health_url, timeout=5)
        if response.status_code == 200:
            print("✅ Server health check passed")
            return True
        else:
            print(f"❌ Server health check failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server connectivity test failed: {e}")
        return False


def test_server_info(server_url: str) -> bool:
    """Test server info endpoint."""
    try:
        props_url = f"{server_url}/props"
        response = requests.get(props_url, timeout=5)
        if response.status_code == 200:
            info = response.json()
            print("✅ Server info retrieved:")
            print(f"   Model: {info.get('model', {}).get('path', 'Unknown')}")
            print(f"   Threads: {info.get('cpu', {}).get('threads', 'Unknown')}")
            return True
        else:
            print(f"⚠️  Server info not available: HTTP {response.status_code}")
            return True  # Not critical
    except Exception as e:
        print(f"⚠️  Server info test failed: {e}")
        return True  # Not critical


def test_completion_endpoint(server_url: str) -> bool:
    """Test completion endpoint with a simple prompt."""
    try:
        completions_url = f"{server_url}/completion"
        payload = {
            "prompt": "Hello, how are you?",
            "n_predict": 20,
            "temperature": 0.7,
            "stream": False,
        }

        print("🧪 Testing completion endpoint...")
        response = requests.post(
            completions_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        if response.status_code == 200:
            result = response.json()
            content = result.get("content", "").strip()
            if content:
                print("✅ Completion test passed")
                print(
                    f"   Response: {content[:100]}{'...' if len(content) > 100 else ''}"
                )
                return True
            else:
                print("❌ Completion test failed: Empty response")
                return False
        else:
            print(f"❌ Completion test failed: HTTP {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"❌ Completion test failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Test llama.cpp server functionality")
    parser.add_argument(
        "--server-url", default="http://localhost:8080", help="llama.cpp server URL"
    )

    args = parser.parse_args()

    print(f"Testing llama.cpp server at: {args.server_url}")
    print("=" * 50)

    # Run tests
    tests = [
        ("Server Connectivity", test_server_connectivity),
        ("Server Info", test_server_info),
        ("Completion Endpoint", test_completion_endpoint),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\\n{test_name}:")
        if test_func(args.server_url):
            passed += 1

    print("\\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Server is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Check server configuration.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
