#!/usr/bin/env python3
"""
Get ngrok URL from Colab notebook
Run this in your Colab notebook to get your ngrok URL
"""

import requests


def get_ngrok_url():
    """Try multiple methods to get ngrok URL"""
    print("🔍 Searching for ngrok URL...")

    # Method 1: ngrok API (if accessible)
    try:
        print("1. Checking ngrok API...")
        response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
        if response.status_code == 200:
            tunnels = response.json()
            if tunnels.get("tunnels"):
                url = tunnels["tunnels"][0]["public_url"]
                print(f"✅ Found via API: {url}")
                return url
    except Exception as e:
        print(f"   API method failed: {e}")

    # Method 2: Check common ngrok URLs (brute force)
    print("2. Checking common ngrok patterns...")
    import subprocess

    try:
        # Try to get from system processes or logs
        result = subprocess.run(
            ["ps", "aux"], capture_output=True, text=True, timeout=5
        )
        if "ngrok" in result.stdout:
            print("   Found ngrok process running")
            # Could try to parse logs here
    except Exception:
        pass

    # Method 3: Ask user to provide it
    print("3. Please provide your ngrok URL manually")
    print("   Look for a line like: 'https://xxxxx.ngrok.io' in your Colab output")

    return None


if __name__ == "__main__":
    url = get_ngrok_url()
    if url:
        print(f"\n🎉 Your ngrok URL is: {url}")
        print(f"Update your .env file with: RAPTOR_MINI_URL={url}")
    else:
        print("\n❌ Could not find ngrok URL automatically.")
        print("Please check your Colab notebook output for the ngrok URL.")
        print("It should look like: https://xxxxx.ngrok.io")
