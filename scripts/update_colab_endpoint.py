#!/usr/bin/env python3
"""
Update Colab llama.cpp provider endpoint in providers.toml

This script updates the ngrok endpoint for the llamacpp_colab provider
in the Goblin Assistant configuration.

Usage:
    python3 update_colab_endpoint.py --url https://new-ngrok-url.ngrok-free.dev
"""

import argparse
import tomllib
import tomli_w
import os
from pathlib import Path


def update_provider_endpoint(config_path: str, new_url: str) -> bool:
    """
    Update the llamacpp_colab provider endpoint in providers.toml

    Args:
        config_path: Path to providers.toml file
        new_url: New ngrok URL for the Colab server

    Returns:
        True if successful, False otherwise
    """
    try:
        # Read current config
        with open(config_path, 'rb') as f:
            config = tomllib.load(f)

        # Update the endpoint
        if 'providers' in config and 'llamacpp_colab' in config['providers']:
            config['providers']['llamacpp_colab']['endpoint'] = new_url
            print(f"✅ Updated llamacpp_colab endpoint to: {new_url}")
        else:
            print("❌ llamacpp_colab provider not found in config")
            return False

        # Write back the config
        with open(config_path, 'wb') as f:
            tomli_w.dump(config, f)

        print(f"✅ Configuration saved to {config_path}")
        return True

    except Exception as e:
        print(f"❌ Error updating config: {e}")
        return False


def test_endpoint(url: str) -> bool:
    """
    Test if the endpoint is accessible

    Args:
        url: Full URL to test (including /v1/chat/completions)

    Returns:
        True if accessible, False otherwise
    """
    import requests

    test_url = f"{url}/v1/chat/completions"
    try:
        response = requests.post(
            test_url,
            json={
                "model": "tinyllama-1.1b-chat-v1.0.Q4_K_M",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10
            },
            timeout=10
        )
        if response.status_code == 200:
            print(f"✅ Endpoint {test_url} is accessible")
            return True
        else:
            print(f"❌ Endpoint {test_url} returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Could not connect to {test_url}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Update Colab llama.cpp provider endpoint")
    parser.add_argument(
        "--url",
        required=True,
        help="New ngrok URL (e.g., https://abc123.ngrok-free.dev)"
    )
    parser.add_argument(
        "--config",
        default="/Users/fuaadabdullah/ForgeMonorepo/goblin-assistant/config/providers.toml",
        help="Path to providers.toml file"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test the endpoint after updating"
    )

    args = parser.parse_args()

    # Validate URL format
    if not args.url.startswith("https://") or "ngrok" not in args.url:
        print("❌ URL must be a valid ngrok HTTPS URL")
        return 1

    # Check if config file exists
    if not os.path.exists(args.config):
        print(f"❌ Config file not found: {args.config}")
        return 1

    print(f"🔄 Updating llamacpp_colab endpoint to: {args.url}")

    # Update the configuration
    if not update_provider_endpoint(args.config, args.url):
        return 1

    # Test the endpoint if requested
    if args.test:
        print("\\n🧪 Testing endpoint...")
        if not test_endpoint(args.url):
            print("⚠️  Endpoint test failed, but config was updated")
            return 1

    print("\\n✅ Configuration updated successfully!")
    print("\\n📋 Next steps:")
    print("1. Restart the Goblin Assistant backend server")
    print("2. Run integration tests: python3 scripts/test_goblin_colab_integration.py --backend-url http://localhost:8000")
    print("3. Test KPI sending: python3 scripts/test_send_llamacpp_kpi.py --provider llamacpp_colab")

    return 0


if __name__ == "__main__":
    exit(main())
