#!/usr/bin/env python3
"""
Raptor Mini Readiness Test
Run this script to verify your Colab-deployed Raptor Mini is ready for the documentation system.
"""

import os
import requests
import sys
from pathlib import Path


def test_raptor_connectivity():
    """Test basic connectivity to Raptor Colab endpoint."""
    raptor_url = os.getenv(
        "RAPTOR_MINI_URL", "https://your-colab-raptor-endpoint.ngrok.io"
    )

    print(f"🔍 Testing Raptor Mini at: {raptor_url}")
    print("-" * 50)

    # Test 1: Health check
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{raptor_url}/health", timeout=10)
        if response.status_code == 200:
            print("   ✅ Health check passed!")
            health_data = response.json()
            print(f"   📊 Status: {health_data}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        return False

    # Test 2: Analyze endpoint (with sample data)
    print("\n2. Testing analyze endpoint...")
    test_payload = {
        "task": "analyze_document",
        "content": "This is a test document for quality analysis.",
        "analysis_type": "quality_score",
    }

    try:
        response = requests.post(
            f"{raptor_url}/analyze",
            json=test_payload,
            timeout=30,
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 200:
            print("   ✅ Analyze endpoint working!")
            result = response.json()
            print(
                f"   📊 Response keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}"
            )
        else:
            print(
                f"   ❌ Analyze failed: {response.status_code} - {response.text[:200]}"
            )
            return False
    except Exception as e:
        print(f"   ❌ Analyze error: {e}")
        return False

    print("\n" + "=" * 50)
    print("🎉 Raptor Mini is READY for the documentation system!")
    print("=" * 50)
    return True


def test_documentation_cli():
    """Test that the documentation CLI can find and run."""
    print("\n3. Testing documentation CLI...")

    cli_path = Path("scripts/doc_cli.py")
    if not cli_path.exists():
        print("   ❌ CLI script not found")
        return False

    # Test CLI help
    import subprocess

    try:
        result = subprocess.run(
            [sys.executable, str(cli_path), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and "analyze" in result.stdout:
            print("   ✅ CLI is working!")
            return True
        else:
            print("   ❌ CLI help failed")
            return False
    except Exception as e:
        print(f"   ❌ CLI test error: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Raptor Mini Readiness Test")
    print("=" * 50)

    # Load environment
    env_file = Path(".env")
    if env_file.exists():
        print("📄 Loading .env file...")
        # Simple env loading (in production, use python-dotenv)
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    os.environ[key] = value
        print("   ✅ Environment loaded")
    else:
        print("   ⚠️  No .env file found - using defaults")

    # Run tests
    raptor_ok = test_raptor_connectivity()
    cli_ok = test_documentation_cli()

    print("\n" + "=" * 50)
    if raptor_ok and cli_ok:
        print("🎯 ALL SYSTEMS GO! Raptor is ready for documentation analysis.")
        print("\nNext steps:")
        print("1. Run: python3 scripts/doc_cli.py analyze docs/your-doc.md")
        print("2. Or: python3 scripts/doc_cli.py audit")
    else:
        print("❌ Some tests failed. Please check the output above.")
        if not raptor_ok:
            print("\n💡 To fix Raptor issues:")
            print("   1. Make sure your Colab notebook is running")
            print("   2. Check that ngrok is properly configured")
            print("   3. Update RAPTOR_MINI_URL in .env with the correct ngrok URL")
        sys.exit(1)
