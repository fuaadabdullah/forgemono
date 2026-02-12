#!/usr/bin/env python3
"""
Canary smoke tests for a llama.cpp server.

Usage:
  python3 test_llamacpp_server.py --server-url https://example --auth-token <jwt>
"""

import argparse
import json
import sys
import requests


def _headers(auth_token: str) -> dict:
    headers = {"Content-Type": "application/json"}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    return headers


def test_server_connectivity(server_url: str, auth_token: str, health_path: str) -> bool:
    try:
        health_url = f"{server_url}{health_path}"
        response = requests.get(health_url, headers=_headers(auth_token), timeout=10)
        if response.status_code == 200:
            print("✅ Server health check passed")
            return True
        print(f"❌ Server health check failed: HTTP {response.status_code}")
        return False
    except Exception as exc:
        print(f"❌ Server connectivity test failed: {exc}")
        return False


def test_server_info(server_url: str, auth_token: str, info_path: str) -> bool:
    try:
        props_url = f"{server_url}{info_path}"
        response = requests.get(props_url, headers=_headers(auth_token), timeout=10)
        if response.status_code == 200:
            info = response.json()
            print("✅ Server info retrieved:")
            print(f"   Model: {info.get('model', {}).get('path', 'Unknown')}")
            print(f"   Threads: {info.get('cpu', {}).get('threads', 'Unknown')}")
            return True
        print(f"⚠️  Server info not available: HTTP {response.status_code}")
        return True
    except Exception as exc:
        print(f"⚠️  Server info test failed: {exc}")
        return True


def test_completion_endpoint(server_url: str, auth_token: str, completion_path: str) -> bool:
    try:
        completions_url = f"{server_url}{completion_path}"
        payload = {
            "prompt": "Hello, how are you?",
            "n_predict": 16,
            "temperature": 0.2,
            "stream": False,
        }

        print("🧪 Testing completion endpoint...")
        response = requests.post(
            completions_url,
            data=json.dumps(payload),
            headers=_headers(auth_token),
            timeout=30,
        )

        if response.status_code == 200:
            result = response.json()
            content = result.get("content", "").strip()
            if content:
                print("✅ Completion test passed")
                print(f"   Response: {content[:100]}{'...' if len(content) > 100 else ''}")
                return True
            print("❌ Completion test failed: Empty response")
            return False

        print(f"❌ Completion test failed: HTTP {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        return False

    except Exception as exc:
        print(f"❌ Completion test failed: {exc}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test llama.cpp server")
    parser.add_argument("--server-url", required=True, help="llama.cpp server URL")
    parser.add_argument("--auth-token", default="", help="Bearer token for auth")
    parser.add_argument("--health-path", default="/health", help="Health endpoint path")
    parser.add_argument("--info-path", default="/props", help="Info endpoint path")
    parser.add_argument("--completion-path", default="/completion", help="Completion endpoint path")

    args = parser.parse_args()

    print(f"Testing llama.cpp server at: {args.server_url}")
    print("=" * 50)

    tests = [
        ("Server Connectivity", lambda: test_server_connectivity(args.server_url, args.auth_token, args.health_path)),
        ("Server Info", lambda: test_server_info(args.server_url, args.auth_token, args.info_path)),
        ("Completion Endpoint", lambda: test_completion_endpoint(args.server_url, args.auth_token, args.completion_path)),
    ]

    passed = 0
    for name, fn in tests:
        print(f"\n{name}:")
        if fn():
            passed += 1

    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{len(tests)} tests passed")

    if passed == len(tests):
        print("🎉 All tests passed! Server is ready.")
        return 0

    print("⚠️  Some tests failed. Check server configuration.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
