#!/usr/bin/env python3
"""
Standalone Cloud Provider Health Check

Tests cloud provider APIs directly without requiring package imports.
This bypasses the relative import issues for quick testing.
"""

import asyncio
import os
import sys
from pathlib import Path

# Load environment
try:
    from dotenv import load_dotenv

    backend_dir = Path(__file__).parent
    env_path = backend_dir.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed, using system env vars")

import httpx


async def test_gcp_ollama():
    """Test GCP Ollama provider directly."""
    print("\n" + "=" * 60)
    print("🔍 Testing GCP Provider (Ollama)")
    print("=" * 60)

    # Try multiple possible Ollama URLs
    urls = [
        os.getenv("OLLAMA_URL", "http://localhost:11434"),
        os.getenv("OLLAMA_GCP_URL", ""),
        os.getenv("OLLAMA_GCP_BASE_URL", ""),
    ]

    for url in urls:
        if not url:
            continue

        print(f"   Testing: {url}")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{url}/api/tags")

                if response.status_code == 200:
                    data = response.json()
                    models = data.get("models", [])
                    print(f"   ✅ Ollama: HEALTHY at {url}")
                    print(f"   📦 Models available: {len(models)}")
                    for model in models[:5]:
                        name = model.get("name", "unknown")
                        size = model.get("size", 0) / (1024**3)  # GB
                        print(f"      - {name} ({size:.1f} GB)")
                    return True
                else:
                    print(f"   ⚠️  Status {response.status_code}")
        except httpx.ConnectError:
            print(f"   ⚠️  Cannot connect to {url}")
        except Exception as e:
            print(f"   ⚠️  Error: {e}")

    print("   ❌ Ollama: UNHEALTHY (not reachable)")
    return False


async def test_runpod():
    """Test RunPod API directly."""
    print("\n" + "=" * 60)
    print("🔍 Testing RunPod Provider")
    print("=" * 60)

    api_key = os.getenv("RUNPOD_API_KEY", "")

    if not api_key or len(api_key) < 20:
        print("   ⚠️  RUNPOD_API_KEY not set or invalid")
        print("      Get your key from: https://www.runpod.io/console/user/settings")
        return False

    print(f"   API Key: {api_key[:10]}...{api_key[-4:]}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test GraphQL API
            response = await client.post(
                "https://api.runpod.io/graphql",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={"query": "query { myself { id email currentSpendPerHr } }"},
            )

            if response.status_code == 200:
                data = response.json()
                if "errors" in data:
                    print(f"   ❌ API Error: {data['errors']}")
                    return False

                myself = data.get("data", {}).get("myself", {})
                email = myself.get("email", "unknown")
                spend = myself.get("currentSpendPerHr", 0)

                print("   ✅ RunPod: HEALTHY")
                print(f"   👤 Account: {email}")
                print(f"   💰 Current spend: ${spend:.4f}/hr")

                # Get GPU pricing info
                gpu_response = await client.post(
                    "https://api.runpod.io/graphql",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "query": """
                        query { 
                            gpuTypes { 
                                id 
                                displayName 
                                memoryInGb 
                                securePrice 
                                communityPrice 
                            } 
                        }
                    """
                    },
                )

                if gpu_response.status_code == 200:
                    gpu_data = gpu_response.json()
                    gpus = gpu_data.get("data", {}).get("gpuTypes", [])
                    print(f"   🎮 GPU Types Available: {len(gpus)}")

                    # Show a few key GPUs
                    key_gpus = ["RTX 4090", "A100", "H100"]
                    for gpu in gpus:
                        name = gpu.get("displayName", "")
                        if any(k in name for k in key_gpus):
                            secure = gpu.get("securePrice", 0)
                            community = gpu.get("communityPrice", 0)
                            mem = gpu.get("memoryInGb", 0)
                            print(
                                f"      - {name} ({mem}GB): ${secure:.2f}/hr (secure), ${community:.2f}/hr (community)"
                            )

                return True
            else:
                print(f"   ❌ API returned status {response.status_code}")
                print(f"      Response: {response.text[:200]}")
                return False

    except Exception as e:
        print(f"   ❌ RunPod Error: {e}")
        return False


async def test_vastai():
    """Test Vast.ai API directly."""
    print("\n" + "=" * 60)
    print("🔍 Testing Vast.ai Provider")
    print("=" * 60)

    api_key = os.getenv("VASTAI_API_KEY", "")

    if not api_key or len(api_key) < 20:
        print("   ⚠️  VASTAI_API_KEY not set or invalid")
        print("      Get your key from: https://vast.ai/console/account")
        return False

    print(f"   API Key: {api_key[:10]}...{api_key[-4:]}")

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            # Test user endpoint (note trailing slash)
            response = await client.get(
                "https://console.vast.ai/api/v0/users/current/",
                params={"api_key": api_key},
            )

            if response.status_code == 200:
                data = response.json()
                credit = data.get("credit", 0)
                email = data.get("email", "unknown")

                print("   ✅ Vast.ai: HEALTHY")
                print(f"   👤 Account: {email}")
                print(f"   💰 Credit balance: ${credit:.2f}")

                # Get available offers
                offers_response = await client.get(
                    "https://console.vast.ai/api/v0/bundles/",
                    params={
                        "api_key": api_key,
                        "q": '{"rentable":{"eq":true},"num_gpus":{"eq":1}}',
                        "limit": 10,
                    },
                )

                if offers_response.status_code == 200:
                    offers_data = offers_response.json()
                    offers = offers_data.get("offers", [])
                    print(f"   🎮 Available GPU offers: {len(offers)}+")

                    # Show cheapest offers
                    for offer in sorted(offers, key=lambda x: x.get("dph_total", 999))[
                        :5
                    ]:
                        gpu = offer.get("gpu_name", "unknown")
                        vram = offer.get("gpu_ram", 0) / 1024  # GB
                        price = offer.get("dph_total", 0)
                        reliability = offer.get("reliability2", 0) * 100
                        print(
                            f"      - {gpu} ({vram:.0f}GB): ${price:.3f}/hr (reliability: {reliability:.0f}%)"
                        )

                return True
            else:
                print(f"   ❌ API returned status {response.status_code}")
                print(f"      Response: {response.text[:200]}")
                return False

    except Exception as e:
        print(f"   ❌ Vast.ai Error: {e}")
        return False


async def test_llamacpp():
    """Test llama.cpp server if configured."""
    print("\n" + "=" * 60)
    print("🔍 Testing llama.cpp Server")
    print("=" * 60)

    urls = [
        os.getenv("LLAMA_CPP_URL", ""),
        os.getenv("LLAMACPP_GCP_URL", ""),
        os.getenv("LLAMACPP_GCP_BASE_URL", ""),
        "http://localhost:8080",
    ]

    for url in urls:
        if not url:
            continue

        print(f"   Testing: {url}")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{url}/health")

                if response.status_code == 200:
                    print(f"   ✅ llama.cpp: HEALTHY at {url}")

                    # Try to get model info
                    try:
                        props = await client.get(f"{url}/props")
                        if props.status_code == 200:
                            data = props.json()
                            print(f"      Model: {data.get('model', 'unknown')}")
                    except Exception:
                        pass

                    return True
        except httpx.ConnectError:
            print(f"   ⚠️  Cannot connect to {url}")
        except Exception as e:
            print(f"   ⚠️  Error: {e}")

    print("   ❌ llama.cpp: Not configured or not reachable")
    return False


async def main():
    """Run all cloud provider tests."""
    print("\n" + "🚀 " * 20)
    print("GOBLIN ASSISTANT - CLOUD PROVIDER HEALTH CHECK (Standalone)")
    print("🚀 " * 20)

    results = {}

    # Test each provider
    results["GCP/Ollama"] = await test_gcp_ollama()
    results["llama.cpp"] = await test_llamacpp()
    results["RunPod"] = await test_runpod()
    results["Vast.ai"] = await test_vastai()

    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)

    healthy = sum(1 for v in results.values() if v)
    total = len(results)

    for name, status in results.items():
        icon = "✅" if status else "❌"
        print(f"   {icon} {name}")

    print(f"\n   Total: {healthy}/{total} providers healthy")

    if healthy >= 2:
        print("\n   🎉 Cloud providers are operational!")
        print("      You have redundancy for inference workloads.")
    elif healthy >= 1:
        print("\n   ⚠️  Limited provider availability.")
        print("      Consider fixing other providers for redundancy.")
    else:
        print("\n   ❌ No providers are operational!")
        print("      Check API keys and network connectivity.")

    return healthy > 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
