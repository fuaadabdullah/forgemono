#!/usr/bin/env python3
"""
Unified Colab Integration Setup
Automatically updates Ollama or llama.cpp Colab provider endpoints and tests integration
"""

import argparse
import subprocess
import sys
import time
import requests
from pathlib import Path


def update_provider_url(provider_type: str, new_url: str) -> bool:
    """Update the Colab provider endpoint in providers.toml"""
    config_path = (
        Path(__file__).parent / "goblin-assistant" / "config" / "providers.toml"
    )

    try:
        with open(config_path, "r") as f:
            content = f.read()

        # Find and replace the provider endpoint
        import re

        provider_name = (
            f"ollama_colab" if provider_type == "ollama" else "llamacpp_colab"
        )
        pattern = rf'(\[providers\.{provider_name}\][\s\S]*?endpoint\s*=\s*)"[^"]*"'
        replacement = rf'\1"{new_url}"'

        if re.search(pattern, content):
            updated_content = re.sub(
                pattern, replacement, content, flags=re.MULTILINE | re.DOTALL
            )

            with open(config_path, "w") as f:
                f.write(updated_content)

            print(f"✅ Updated {provider_name} endpoint to: {new_url}")
            return True
        else:
            print(f"❌ Could not find the {provider_name} provider in providers.toml")
            return False

    except Exception as e:
        print(f"❌ Error updating config: {e}")
        return False


def test_colab_server(provider_type: str, url: str) -> bool:
    """Test if Colab server is responding"""
    try:
        if provider_type == "ollama":
            # Test Ollama API tags endpoint
            response = requests.get(f"{url}/api/tags", timeout=10)
            return response.status_code == 200
        else:
            # Test llama.cpp health endpoint
            response = requests.get(f"{url}/health", timeout=10)
            return response.status_code == 200
    except:
        return False


def run_integration_test() -> bool:
    """Run the integration test"""
    try:
        result = subprocess.run(
            [
                "python3",
                "scripts/test_goblin_colab_integration.py",
                "--backend-url",
                "http://localhost:8001",
            ],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            timeout=120,
        )

        print("Integration Test Output:")
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)

        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("❌ Integration test timed out")
        return False
    except Exception as e:
        print(f"❌ Error running integration test: {e}")
        return False


def get_current_url(provider_type: str) -> str:
    """Get current URL for the provider"""
    config_path = (
        Path(__file__).parent / "goblin-assistant" / "config" / "providers.toml"
    )

    try:
        with open(config_path, "r") as f:
            content = f.read()

        import re

        provider_name = (
            f"ollama_colab" if provider_type == "ollama" else "llamacpp_colab"
        )
        match = re.search(
            rf'\[providers\.{provider_name}\][\s\S]*?endpoint\s*=\s*"([^"]*)"',
            content,
            re.MULTILINE | re.DOTALL,
        )
        if match:
            return match.group(1)
        else:
            return None
    except Exception as e:
        print(f"❌ Error reading config: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Unified Colab Integration Setup")
    parser.add_argument(
        "--provider",
        choices=["ollama", "llamacpp"],
        default="ollama",
        help="Which Colab provider to configure (default: ollama)",
    )
    parser.add_argument("--colab-url", help="New Colab ngrok URL")
    parser.add_argument(
        "--auto-test",
        action="store_true",
        help="Automatically run integration test after URL update",
    )

    args = parser.parse_args()

    provider_type = args.provider
    provider_display = "Ollama" if provider_type == "ollama" else "llama.cpp"

    if args.colab_url:
        print(f"🔄 Updating {provider_display} Colab provider URL to: {args.colab_url}")

        if update_provider_url(provider_type, args.colab_url):
            print("✅ Provider configuration updated")

            if test_colab_server(provider_type, args.colab_url):
                print(f"✅ Colab {provider_display} server is responding!")

                if args.auto_test:
                    print("🧪 Running integration test...")
                    if run_integration_test():
                        print("🎉 Integration successful!")
                        return 0
                    else:
                        print("❌ Integration test failed")
                        return 1
                else:
                    print("🎉 URL updated successfully!")
                    return 0
            else:
                print(f"❌ Colab {provider_display} server is not responding")
                print(
                    "   Make sure the server is running in Colab and the URL is correct"
                )
                return 1
        else:
            print("❌ Failed to update provider configuration")
            return 1

    else:
        print(f"🔍 Checking current {provider_display} Colab server status...")
        current_url = get_current_url(provider_type)

        if current_url is None:
            print(f"❌ Could not find {provider_type}_colab provider in config")
            return 1

        print(f"Current URL: {current_url}")

        placeholder_url = (
            "https://your-ngrok-url.ngrok.io"
            if provider_type == "ollama"
            else "https://thomasena-auxochromic-joziah.ngrok-free.dev"
        )

        if current_url == placeholder_url:
            print("❌ URL is still set to placeholder")
            print("   Please run:")
            print(
                f"   python3 setup_colab_integration.py --provider {provider_type} --colab-url YOUR_ACTUAL_NGROK_URL"
            )
            return 1

        if test_colab_server(provider_type, current_url):
            print(f"✅ Colab {provider_display} server is online!")
            print("🧪 Running integration test...")
            if run_integration_test():
                print("🎉 Integration successful!")
                return 0
            else:
                print("❌ Integration test failed")
                return 1
        else:
            print(f"❌ Colab {provider_display} server is offline")
            print(f"   Current URL: {current_url}")
            print("   Please update with:")
            print(
                f"   python3 setup_colab_integration.py --provider {provider_type} --colab-url YOUR_NEW_NGROK_URL"
            )
            return 1


if __name__ == "__main__":
    sys.exit(main())
