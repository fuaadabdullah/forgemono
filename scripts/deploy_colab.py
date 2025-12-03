#!/usr/bin/env python3
"""
Deploy Colab llama.cpp Setup

This script helps deploy the llama.cpp Colab notebook to Google Colab
and generates shareable links for remote access.

Usage:
    python3 deploy_colab.py [--upload-to-gist] [--generate-link]

Requirements:
    pip install requests pyperclip
"""

import argparse
import json
import base64
import webbrowser
import sys
import os
from pathlib import Path


def create_github_gist(notebook_path: str, token: str = None) -> str:
    """
    Create a GitHub Gist with the notebook content.

    Args:
        notebook_path: Path to the notebook file
        token: GitHub personal access token (optional)

    Returns:
        URL of the created gist
    """
    try:
        import requests
    except ImportError:
        print("❌ requests library required. Install with: pip install requests")
        return None

    with open(notebook_path, "r") as f:
        content = f.read()

    # Extract filename
    filename = Path(notebook_path).name

    # Create gist payload
    payload = {
        "description": "llama.cpp Server Setup for Google Colab",
        "public": True,
        "files": {filename: {"content": content}},
    }

    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    response = requests.post(
        "https://api.github.com/gists", headers=headers, json=payload
    )

    if response.status_code == 201:
        gist_data = response.json()
        gist_url = gist_data["html_url"]
        print(f"✅ Gist created: {gist_url}")
        return gist_url
    else:
        print(f"❌ Failed to create gist: {response.status_code}")
        print(response.text)
        return None


def generate_colab_url_from_gist(gist_url: str, ngrok_token: str = "") -> str:
    """
    Generate a Colab URL that opens the gist notebook.

    Args:
        gist_url: URL of the GitHub gist
        ngrok_token: ngrok authentication token

    Returns:
        Colab URL with embedded configuration
    """
    # Convert gist URL to Colab-compatible format
    # GitHub gist URLs can be opened directly in Colab
    colab_base = "https://colab.research.google.com/gist"

    # Extract gist ID from URL
    if "/gist/" in gist_url:
        gist_id = gist_url.split("/gist/")[1].split("/")[0]
        colab_url = f"{colab_base}/{gist_id}"
    else:
        print("❌ Invalid gist URL format")
        return None

    # Add configuration if ngrok token provided
    if ngrok_token:
        config = {
            "ngrok_token": ngrok_token,
            "server_port": 8080,
            "model_repo": "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF:q4_k_m",
            "auto_start": True,
        }
        config_json = json.dumps(config, separators=(",", ":"))
        config_b64 = base64.urlsafe_b64encode(config_json.encode()).decode()
        colab_url += f"?config={config_b64}"

    return colab_url


def open_in_browser(url: str):
    """Open URL in default browser."""
    try:
        webbrowser.open(url)
        print(f"🌐 Opened in browser: {url}")
    except Exception as e:
        print(f"⚠️  Could not open browser: {e}")
        print(f"📋 Copy this URL: {url}")


def main():
    parser = argparse.ArgumentParser(description="Deploy Colab llama.cpp setup")
    parser.add_argument(
        "--notebook",
        default="notebooks/colab_llamacpp_setup.ipynb",
        help="Path to the Colab notebook",
    )
    parser.add_argument(
        "--upload-to-gist", action="store_true", help="Upload notebook to GitHub Gist"
    )
    parser.add_argument("--github-token", help="GitHub personal access token")
    parser.add_argument("--ngrok-token", help="ngrok authentication token")
    parser.add_argument(
        "--open-browser",
        action="store_true",
        default=True,
        help="Open generated URLs in browser",
    )

    args = parser.parse_args()

    notebook_path = args.notebook

    if not os.path.exists(notebook_path):
        print(f"❌ Notebook not found: {notebook_path}")
        sys.exit(1)

    print("🚀 Deploying llama.cpp Colab Setup")
    print("=" * 50)

    gist_url = None
    if args.upload_to_gist:
        print("\\n📤 Uploading to GitHub Gist...")
        gist_url = create_github_gist(notebook_path, args.github_token)
        if not gist_url:
            print("❌ Gist upload failed")
            sys.exit(1)
    else:
        print("\\n📋 Manual Upload Instructions:")
        print("1. Go to https://colab.research.google.com/")
        print("2. Click 'File' → 'Upload notebook'")
        print(f"3. Select: {notebook_path}")
        print("4. Run all cells in order")

    # Generate Colab URL
    if gist_url:
        colab_url = generate_colab_url_from_gist(gist_url, args.ngrok_token)
        if colab_url:
            print("\\n🔗 Colab URL (with gist):")
            print(colab_url)

            if args.open_browser:
                open_in_browser(colab_url)
        else:
            print("\\n❌ Failed to generate Colab URL")
    else:
        print("\\n🔗 After uploading to Colab, your notebook will be available at:")
        print("https://colab.research.google.com/drive/YOUR_NOTEBOOK_ID")

        if args.ngrok_token:
            print("\\n💡 To add ngrok configuration:")
            print("1. In Colab, add this to a cell:")
            print(f"!ngrok config add-authtoken {args.ngrok_token}")

    print("\\n📚 Next Steps:")
    print("1. Open the Colab notebook")
    print("2. Run cells 1-7 to set up the server")
    print("3. Run cell 8 to start the server with ngrok tunnel")
    print("4. Use the generated public URL for API access")

    print("\\n🧪 Testing:")
    print("python3 scripts/test_llamacpp_server.py --server-url PUBLIC_NGROK_URL")

    print("\\n📊 Benchmarking:")
    print(
        "python3 scripts/benchmark_llamacpp.py --server-url PUBLIC_NGROK_URL --threads 1,2,4"
    )

    if gist_url:
        print(f"\\n📎 Gist URL: {gist_url}")


if __name__ == "__main__":
    main()
