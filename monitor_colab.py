#!/usr/bin/env python3
"""
Monitor Colab server status and auto-update integration when it comes online
"""

import time
import requests
import subprocess
import sys
from pathlib import Path


def check_colab_server(url: str) -> bool:
    """Check if Colab server is responding"""
    try:
        response = requests.get(f"{url}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def get_ngrok_url_from_colab() -> str:
    """Try to get current ngrok URL from Colab (this would need to be implemented)"""
    # For now, return the known URL
    return "https://thomasena-auxochromic-joziah.ngrok-free.dev"


def update_and_test(new_url: str) -> bool:
    """Update provider config and run integration test"""
    try:
        # Update config
        result = subprocess.run([
            "python3", "setup_colab_integration.py", "--colab-url", new_url, "--auto-test"
        ], cwd=Path(__file__).parent, capture_output=True, text=True)

        print("Setup Output:")
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)

        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error in update_and_test: {e}")
        return False


def main():
    print("🔍 Monitoring Colab server status...")
    print("   Press Ctrl+C to stop monitoring")

    current_url = "https://thomasena-auxochromic-joziah.ngrok-free.dev"

    try:
        while True:
            if check_colab_server(current_url):
                print("✅ Colab server is online!")
                print(f"   URL: {current_url}")

                if update_and_test(current_url):
                    print("🎉 Integration completed successfully!")
                    return 0
                else:
                    print("❌ Integration failed")
                    return 1
            else:
                print(f"⏳ Colab server offline, checking again in 10 seconds... ({current_url})")

            time.sleep(10)

    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")
        return 0


if __name__ == "__main__":
    sys.exit(main())
