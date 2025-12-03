#!/usr/bin/env python3
"""
Colab Ollama Integration Setup
Automatically updates the ollama_colab provider endpoint and tests integration
"""

import argparse
import subprocess
import sys
import time
import requests
from pathlib import Path


def update_provider_url(new_url: str) -> bool:
    """Update the ollama_colab endpoint in providers.toml"""
    config_path = Path(__file__).parent / "goblin-assistant" / "config" / "providers.toml"

    try:
        with open(config_path, 'r') as f:
            content = f.read()

        # Find and replace the ollama_colab endpoint
        import re
        pattern = r'(\[providers\.ollama_colab\][\s\S]*?endpoint\s*=\s*)"[^"]*"'
        replacement = rf'\1"{new_url}"'

        if re.search(pattern, content):
            updated_content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)

            with open(config_path, 'w') as f:
                f.write(updated_content)

            print(f"✅ Updated ollama_colab endpoint to: {new_url}")
            return True
        else:
            print("❌ Could not find the ollama_colab provider in providers.toml")
            return False

    except Exception as e:
        print(f"❌ Error updating config: {e}")
        return False


def test_colab_server(url: str) -> bool:
    """Test if Colab Ollama server is responding"""
    try:
        # Test Ollama API tags endpoint
        response = requests.get(f"{url}/api/tags", timeout=10)
        return response.status_code == 200
    except:
        return False


def run_integration_test() -> bool:
    """Run the integration test"""
    try:
        result = subprocess.run([
            "python3", "scripts/test_goblin_colab_integration.py", "--backend-url", "http://localhost:8000"
        ], cwd=Path(__file__).parent, capture_output=True, text=True, timeout=120)

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


def main():
    parser = argparse.ArgumentParser(description="Colab Ollama Integration Setup")
    parser.add_argument("--colab-url", help="New Colab ngrok URL for Ollama")
    parser.add_argument("--auto-test", action="store_true", help="Automatically run integration test after URL update")

    args = parser.parse_args()

    if args.colab_url:
        print(f"🔄 Updating Ollama Colab provider URL to: {args.colab_url}")

        if update_provider_url(args.colab_url):
            print("✅ Provider configuration updated")

            if test_colab_server(args.colab_url):
                print("✅ Colab Ollama server is responding!")

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
                print("❌ Colab Ollama server is not responding")
                print("   Make sure Ollama is running in Colab and the URL is correct")
                return 1
        else:
            print("❌ Failed to update provider configuration")
            return 1

    else:
        print("🔍 Checking current Ollama Colab server status...")
        # Read current URL from config
        config_path = Path(__file__).parent / "goblin-assistant" / "config" / "providers.toml"

        try:
            with open(config_path, 'r') as f:
                content = f.read()

            import re
            match = re.search(r'\[providers\.ollama_colab\][\s\S]*?endpoint\s*=\s*"([^"]*)"', content, re.MULTILINE | re.DOTALL)
            if match:
                current_url = match.group(1)
                print(f"Current URL: {current_url}")

                if current_url == "https://your-ngrok-url.ngrok.io":
                    print("❌ URL is still set to placeholder")
                    print("   Please run:")
                    print(f"   python3 setup_colab_ollama_integration.py --colab-url YOUR_ACTUAL_NGROK_URL")
                    return 1

                if test_colab_server(current_url):
                    print("✅ Colab Ollama server is online!")
                    print("🧪 Running integration test...")
                    if run_integration_test():
                        print("🎉 Integration successful!")
                        return 0
                    else:
                        print("❌ Integration test failed")
                        return 1
                else:
                    print("❌ Colab Ollama server is offline")
                    print(f"   Current URL: {current_url}")
                    print("   Please update with:")
                    print(f"   python3 setup_colab_ollama_integration.py --colab-url YOUR_NEW_NGROK_URL")
                    return 1
            else:
                print("❌ Could not find ollama_colab provider in config")
                return 1

        except Exception as e:
            print(f"❌ Error reading config: {e}")
            return 1


if __name__ == "__main__":
    sys.exit(main())
