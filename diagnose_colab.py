#!/usr/bin/env python3
"""
Comprehensive Colab Integration Diagnostics CLI
Provides detailed insights into the integration status
"""

import argparse
import requests
import subprocess
import sys
import time
from pathlib import Path


def check_backend_status():
    """Check if the local backend is running"""
    print("🔍 Checking Backend Status...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend: ONLINE (FastAPI server responding)")
            return True
        else:
            print(f"❌ Backend: ERROR (Status code: {response.status_code})")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Backend: OFFLINE (Connection refused)")
        return False
    except Exception as e:
        print(f"❌ Backend: ERROR ({e})")
        return False


def check_colab_server(url=None):
    """Check Colab server status"""
    print("🔍 Checking Colab Server Status...")

    if not url:
        # Check the configured URL in providers.toml
        config_path = Path(__file__).parent / "goblin-assistant" / "config" / "providers.toml"
        try:
            with open(config_path, 'r') as f:
                content = f.read()
                if 'endpoint = "' in content:
                    for line in content.split('\n'):
                        if 'endpoint = "' in line and 'llamacpp_colab' in content:
                            url = line.split('"')[1]
                            break
        except:
            pass

        if not url:
            url = "https://thomasena-auxochromic-joziah.ngrok-free.dev"

    print(f"   Testing URL: {url}")

    # Test basic connectivity
    try:
        response = requests.get(url, timeout=5)
        print(f"✅ Colab: HTTP {response.status_code} (Basic connectivity OK)")
    except:
        print("❌ Colab: No response (Server offline or unreachable)")
        return False

    # Test health endpoint
    try:
        response = requests.get(f"{url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Colab: Health endpoint responding")
        else:
            print(f"⚠️  Colab: Health endpoint returned {response.status_code}")
    except:
        print("❌ Colab: Health endpoint not responding")

    # Test chat endpoint
    try:
        response = requests.post(f"{url}/v1/chat/completions",
                               json={"messages": [{"role": "user", "content": "test"}]},
                               timeout=10)
        if response.status_code == 200:
            print("✅ Colab: Chat endpoint responding")
            return True
        else:
            print(f"❌ Colab: Chat endpoint returned {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print("❌ Colab: Chat endpoint timed out")
        return False
    except Exception as e:
        print(f"❌ Colab: Chat endpoint error: {e}")
        return False


def check_routing_system():
    """Check the routing system configuration"""
    print("🔍 Checking Routing System...")

    try:
        response = requests.get("http://localhost:8000/routing/providers", timeout=5)
        if response.status_code == 200:
            providers = response.json()
            print(f"✅ Routing: Available providers: {providers}")

            if "llamacpp_colab" in providers:
                print("✅ Routing: llamacpp_colab provider found")
                return True
            else:
                print("❌ Routing: llamacpp_colab provider NOT found")
                return False
        else:
            print(f"❌ Routing: Failed to get providers (Status: {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Routing: Error - {e}")
        return False


def check_provider_config():
    """Check the provider configuration"""
    print("🔍 Checking Provider Configuration...")

    config_path = Path(__file__).parent / "goblin-assistant" / "config" / "providers.toml"
    try:
        with open(config_path, 'r') as f:
            content = f.read()

        if "[providers.llamacpp_colab]" in content:
            print("✅ Config: llamacpp_colab section found")

            # Extract endpoint
            lines = content.split('\n')
            in_llamacpp_section = False
            endpoint = None
            for line in lines:
                if "[providers.llamacpp_colab]" in line:
                    in_llamacpp_section = True
                elif line.startswith("[providers.") and in_llamacpp_section:
                    break
                elif in_llamacpp_section and line.startswith("endpoint = "):
                    endpoint = line.split('"')[1] if '"' in line else line.split()[2]
                    break

            if endpoint:
                print(f"✅ Config: Endpoint configured: {endpoint}")
                return endpoint
            else:
                print("❌ Config: No endpoint found in llamacpp_colab section")
                return None
        else:
            print("❌ Config: llamacpp_colab section not found")
            return None

    except Exception as e:
        print(f"❌ Config: Error reading providers.toml - {e}")
        return None


def run_integration_test():
    """Run the full integration test"""
    print("🧪 Running Integration Test...")
    try:
        result = subprocess.run([
            "python3", "run_integration_test.py"
        ], cwd=Path(__file__).parent, capture_output=True, text=True, timeout=120)

        print("Integration Test Results:")
        print("=" * 50)
        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)
        print("=" * 50)

        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("❌ Integration test timed out")
        return False


def diagnose_network():
    """Network diagnostics"""
    print("🔍 Network Diagnostics...")

    # Test internet connectivity
    try:
        response = requests.get("https://httpbin.org/get", timeout=5)
        print("✅ Internet: Connected")
    except:
        print("❌ Internet: No connectivity")
        return

    # Test ngrok service
    try:
        response = requests.get("https://ngrok.com", timeout=5)
        print("✅ ngrok: Service reachable")
    except:
        print("❌ ngrok: Service unreachable")

    # Test Colab connectivity
    try:
        response = requests.get("https://colab.research.google.com", timeout=5)
        print("✅ Colab: Service reachable")
    except:
        print("❌ Colab: Service unreachable")


def main():
    parser = argparse.ArgumentParser(description="Colab Integration Diagnostics CLI")
    parser.add_argument("--full", action="store_true", help="Run full diagnostic suite")
    parser.add_argument("--backend", action="store_true", help="Check backend status only")
    parser.add_argument("--colab", action="store_true", help="Check Colab server only")
    parser.add_argument("--routing", action="store_true", help="Check routing system only")
    parser.add_argument("--config", action="store_true", help="Check configuration only")
    parser.add_argument("--network", action="store_true", help="Run network diagnostics")
    parser.add_argument("--test", action="store_true", help="Run integration test only")

    args = parser.parse_args()

    if args.full or len(sys.argv) == 1:
        print("🚀 Full Colab Integration Diagnostics")
        print("=" * 50)

        # Run all checks
        backend_ok = check_backend_status()
        print()

        endpoint = check_provider_config()
        print()

        colab_ok = check_colab_server(endpoint)
        print()

        routing_ok = check_routing_system()
        print()

        diagnose_network()
        print()

        if backend_ok and colab_ok and routing_ok:
            print("🎉 All systems check out! Running integration test...")
            run_integration_test()
        else:
            print("❌ Issues found. Fix the problems above before running integration test.")
            print("\n💡 Quick fixes:")
            if not backend_ok:
                print("   - Start backend: cd goblin-assistant/api && uvicorn main:app --host 0.0.0.0 --port 8000")
            if not colab_ok:
                print("   - Restart Colab server and update endpoint in providers.toml")
            if not routing_ok:
                print("   - Check providers.toml configuration")

    elif args.backend:
        check_backend_status()
    elif args.colab:
        endpoint = check_provider_config()
        check_colab_server(endpoint)
    elif args.routing:
        check_routing_system()
    elif args.config:
        check_provider_config()
    elif args.network:
        diagnose_network()
    elif args.test:
        run_integration_test()


if __name__ == "__main__":
    main()
