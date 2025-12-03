#!/usr/bin/env python3
"""
Deploy llama.cpp to Google Colab and update Goblin Assistant config

This script guides you through deploying llama.cpp on Google Colab
and automatically updates the Goblin Assistant configuration.
"""

import os
import sys
import subprocess
import webbrowser
import time

def print_header():
    print("🚀 Deploying llama.cpp to Google Colab")
    print("=" * 50)

def open_colab():
    """Open the Colab notebook in browser"""
    colab_url = "https://colab.research.google.com/github/fuaadabdullah/ForgeMonorepo/blob/main/notebooks/colab_llamacpp_setup_complete.ipynb"
    print("📖 Opening Colab notebook...")
    print(f"URL: {colab_url}")
    webbrowser.open(colab_url)
    print("✅ Colab notebook opened in browser")
    print()

def print_colab_instructions():
    """Print step-by-step Colab instructions"""
    print("📋 Run these cells in Colab (in order):")
    print()
    print("🔵 Cell 1: Mount Google Drive")
    print("   • Click the play button")
    print("   • Sign in with your Google account")
    print("   • Grant permissions")
    print()

    print("🔵 Cell 2: Install dependencies & build llama.cpp")
    print("   • This takes 2-3 minutes")
    print()

    print("🔵 Cell 3: Install ngrok")
    print("   • Auth token is already configured")
    print()

    print("🔵 Cell 4: Install huggingface-cli (optional)")
    print()

    print("🔵 Cell 5: Download TinyLlama model")
    print("   • Downloads to your Google Drive")
    print("   • Takes 1-2 minutes")
    print()

    print("🔵 Cell 6: Start llama.cpp server")
    print("   • Server starts on port 8080")
    print()

    print("🔵 Cell 7: Setup ngrok tunnel")
    print("   • Creates public URL")
    print("   • Copy the URL from the output (looks like: https://abc123.ngrok-free.app)")
    print()

def get_ngrok_url():
    """Get ngrok URL from user input"""
    while True:
        url = input("Enter the ngrok URL from Colab (e.g., https://abc123.ngrok-free.app): ").strip()

        if not url:
            print("❌ No URL provided. Please try again.")
            continue

        if not url.startswith("https://") or "ngrok" not in url:
            print("❌ URL must be a valid ngrok HTTPS URL. Please try again.")
            continue

        return url

def update_config(ngrok_url):
    """Update the Goblin Assistant configuration"""
    repo_root = "/Users/fuaadabdullah/ForgeMonorepo"
    config_file = f"{repo_root}/goblin-assistant/config/providers.toml"

    print(f"🔄 Updating configuration with URL: {ngrok_url}")

    # Change to repo root
    os.chdir(repo_root)

    # Run the update script
    cmd = [
        sys.executable,
        "scripts/update_colab_endpoint.py",
        "--url", ngrok_url,
        "--test"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ Configuration updated successfully!")
        return True
    else:
        print("❌ Failed to update configuration:")
        print(result.stdout)
        print(result.stderr)
        return False

def test_integration():
    """Test the integration"""
    print("🧪 Testing integration...")

    cmd = [
        sys.executable,
        "scripts/test_goblin_colab_integration.py",
        "--backend-url", "http://localhost:8000"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print("🎉 Integration test passed!")
        return True
    else:
        print("⚠️  Integration test failed:")
        print(result.stdout)
        print(result.stderr)
        return False

def print_success():
    """Print success message and next steps"""
    print()
    print("🎉 Deployment successful!")
    print()
    print("Your llama.cpp server is now running on Google Colab and integrated with Goblin Assistant.")
    print()
    print("📋 Important notes:")
    print("• Colab sessions timeout after ~90 minutes")
    print("• Keep the Colab tab open to maintain the session")
    print("• Models are saved in your Google Drive for reuse")
    print("• Use Colab Pro for longer sessions if needed")
    print()
    print("📚 Useful commands:")
    print("• Restart backend: cd goblin-assistant/api && uvicorn main:app --host 0.0.0.0 --port 8000")
    print("• Run tests: python3 scripts/test_goblin_colab_integration.py --backend-url http://localhost:8000")
    print("• Check backend: curl http://localhost:8000/health")

def main():
    print_header()
    open_colab()
    print_colab_instructions()

    # Get ngrok URL from user
    ngrok_url = get_ngrok_url()
    print(f"✅ Got ngrok URL: {ngrok_url}")
    print()

    # Update configuration
    if not update_config(ngrok_url):
        print("❌ Configuration update failed. Exiting.")
        return 1

    # Test integration
    if not test_integration():
        print()
        print("The configuration was updated, but integration test failed.")
        print("Try restarting the Goblin Assistant backend and running tests again.")
        return 1

    print_success()
    return 0

if __name__ == "__main__":
    sys.exit(main())
