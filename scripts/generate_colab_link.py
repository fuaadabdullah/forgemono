#!/usr/bin/env python3
"""
Colab Link Generator for llama.cpp Server

This script generates shareable Google Colab links with embedded ngrok configuration
for running llama.cpp servers. It creates a link that automatically sets up the
environment and starts the server with ngrok tunneling.

Usage:
    python3 generate_colab_link.py --notebook-url https://colab.research.google.com/drive/your-notebook --ngrok-token your_token

Requirements:
    pip install requests urllib3
"""

import argparse
import urllib.parse
import json
import base64
import sys


class ColabLinkGenerator:
    def __init__(self):
        self.base_colab_url = "https://colab.research.google.com/github"

    def generate_shareable_link(
        self,
        notebook_url: str,
        ngrok_token: str = "",
        server_port: int = 8080,
        model_repo: str = "",
        auto_start: bool = True,
    ) -> str:
        """
        Generate a shareable Colab link with embedded configuration.

        Args:
            notebook_url: URL to the Colab notebook
            ngrok_token: ngrok authentication token (optional)
            server_port: Port for the llama.cpp server
            model_repo: HuggingFace model repo (e.g., "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF")
            auto_start: Whether to auto-start the server

        Returns:
            Shareable Colab URL with embedded parameters
        """

        # Extract notebook path from URL
        if "colab.research.google.com" in notebook_url:
            # Handle different Colab URL formats
            if "/drive/" in notebook_url:
                # Drive URL format: https://colab.research.google.com/drive/1abc123...#scrollTo=...
                drive_id = notebook_url.split("/drive/")[1].split("/")[0].split("#")[0]
                notebook_path = f"?id={drive_id}"
            elif "/github/" in notebook_url:
                # GitHub URL format: https://colab.research.google.com/github/user/repo/blob/main/notebook.ipynb
                path_parts = notebook_url.split("/github/")[1].split("/")
                user = path_parts[0]
                repo = path_parts[1]
                branch = path_parts[3] if len(path_parts) > 3 else "main"
                notebook_file = "/".join(path_parts[4:]) if len(path_parts) > 4 else ""
                notebook_path = f"/{user}/{repo}/blob/{branch}/{notebook_file}"
            else:
                print("❌ Unsupported Colab URL format")
                return ""
        else:
            print("❌ Not a valid Colab URL")
            return ""

        # Create configuration object
        config = {
            "ngrok_token": ngrok_token,
            "server_port": server_port,
            "model_repo": model_repo,
            "auto_start": auto_start,
            "timestamp": "2025-01-28",  # Current date for cache busting
        }

        # Encode config as base64 (URL-safe)
        config_json = json.dumps(config, separators=(",", ":"))
        config_b64 = base64.urlsafe_b64encode(config_json.encode()).decode()

        # Build the final URL with parameters
        final_url = f"{self.base_colab_url}{notebook_path}"

        if config_b64:
            final_url += f"?config={config_b64}"

        return final_url

    def generate_qr_code_link(self, colab_url: str) -> str:
        """Generate a QR code link for the Colab URL."""
        encoded_url = urllib.parse.quote(colab_url)
        return f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={encoded_url}"

    def print_setup_instructions(self, colab_url: str, ngrok_token: str = ""):
        """Print setup instructions for sharing the link."""
        print("\\n" + "=" * 60)
        print("COLAB LINK GENERATED SUCCESSFULLY")
        print("=" * 60)
        print("\\n📎 Shareable Link:")
        print(colab_url)

        if ngrok_token:
            print("\\n✅ ngrok authentication included")
        else:
            print("\\n⚠️  No ngrok token provided - users will need to add their own")

        print("\\n📱 QR Code:")
        qr_url = self.generate_qr_code_link(colab_url)
        print(qr_url)

        print("\\n📋 Instructions for recipients:")
        print("1. Open the link above in Google Colab")
        print(
            "2. If ngrok token not included, run: !ngrok config add-authtoken YOUR_TOKEN"
        )
        print("3. Run all cells in order")
        print("4. The server will be available at the ngrok URL shown in the output")

        print("\\n🔧 Configuration:")
        print("- llama.cpp server on port 8080")
        print("- ngrok tunnel for external access")
        print("- Model loaded from HuggingFace (if specified)")

        print("\\n💡 Tips:")
        print("- Colab Pro recommended for better performance")
        print("- Keep the tab open to maintain the server")
        print("- Use the benchmark script to test performance")


def main():
    parser = argparse.ArgumentParser(
        description="Generate shareable Colab links for llama.cpp server"
    )
    parser.add_argument(
        "--notebook-url", required=True, help="URL to the Colab notebook"
    )
    parser.add_argument(
        "--ngrok-token", default="", help="ngrok authentication token (optional)"
    )
    parser.add_argument(
        "--server-port", type=int, default=8080, help="Port for llama.cpp server"
    )
    parser.add_argument(
        "--model-repo",
        default="TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF:q4_k_m",
        help="HuggingFace model repo and quantization",
    )
    parser.add_argument(
        "--auto-start",
        action="store_true",
        default=True,
        help="Auto-start server when notebook opens",
    )

    args = parser.parse_args()

    generator = ColabLinkGenerator()

    colab_url = generator.generate_shareable_link(
        notebook_url=args.notebook_url,
        ngrok_token=args.ngrok_token,
        server_port=args.server_port,
        model_repo=args.model_repo,
        auto_start=args.auto_start,
    )

    if colab_url:
        generator.print_setup_instructions(colab_url, args.ngrok_token)
    else:
        print("❌ Failed to generate Colab link")
        sys.exit(1)


if __name__ == "__main__":
    main()
