#!/usr/bin/env python3
"""
Configure Goblin Assistant for Colab llama.cpp Server

This script updates the Goblin Assistant provider configuration
to connect to a remote Colab-deployed llama.cpp server.

Usage:
    python3 configure_colab_llamacpp.py --ngrok-url https://abc123.ngrok.io --model tinyllama

Requirements:
    pip install tomllib tomli_w
"""

import argparse
from pathlib import Path
import tomllib
import tomli_w


def update_provider_config(config_path: Path, ngrok_url: str, model: str) -> bool:
    """Update the llama.cpp Colab provider configuration."""
    try:
        # Read current config
        with open(config_path, "rb") as f:
            config = tomllib.load(f)

        # Update llama.cpp Colab provider
        if "providers" not in config:
            config["providers"] = {}

        config["providers"]["llamacpp_colab"] = {
            "name": "llama.cpp (Colab)",
            "endpoint": ngrok_url.rstrip("/"),
            "capabilities": ["chat", "reasoning", "code"],
            "models": [model],
            "priority_tier": 0,  # High priority for fast responses
            "cost_score": 0.0,  # Free (Colab compute)
            "default_timeout_ms": 30000,
            "bandwidth_score": 0.6,  # Moderate for GGUF models
            "supports_cot": False,  # Small models work better without CoT
            "invoke_path": "/v1/chat/completions",
        }
        # keep existing KPI section if present – we won't overwrite it unless explicitly requested
        if "kpi" in config["providers"].get("llamacpp_colab", {}):
            pass

        # Write updated config
        with open(config_path, "wb") as f:
            tomli_w.dump(config, f)

        print(f"✅ Updated provider config: {config_path}")
        print(f"   Endpoint: {ngrok_url}")
        print(f"   Model: {model}")
        return True

    except Exception as e:
        print(f"❌ Failed to update config: {e}")
        return False


def test_connection(ngrok_url: str) -> bool:
    """Test connection to the Colab llama.cpp server."""
    try:
        import requests

        # Test health endpoint
        health_url = f"{ngrok_url.rstrip('/')}/health"
        response = requests.get(health_url, timeout=10)

        if response.status_code == 200:
            print("✅ Server connection successful")
            return True
        else:
            print(f"⚠️  Server responded with status {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Configure Goblin Assistant for Colab llama.cpp"
    )
    parser.add_argument(
        "--ngrok-url",
        required=True,
        help="ngrok URL from Colab deployment (e.g., https://abc123.ngrok.io)",
    )
    parser.add_argument(
        "--model",
        default="tinyllama-1.1b-chat-v1.0.Q4_K_M",
        help="Model name deployed on Colab",
    )
    parser.add_argument(
        "--config-path",
        default="/Users/fuaadabdullah/ForgeMonorepo/goblin-assistant/config/providers.toml",
        help="Path to providers.toml config file",
    )
    parser.add_argument(
        "--test-connection",
        action="store_true",
        help="Test connection to the server after configuration",
    )
    parser.add_argument(
        "--kpi-provider",
        choices=["datadog", "prometheus"],
        help="Monitoring provider for KPIs (datadog or prometheus)",
    )
    parser.add_argument(
        "--kpi-api-env",
        default="LLAMACPP_COLAB_DATADOG_API_KEY",
        help="The env var name used to read the KPI API/key",
    )
    parser.add_argument(
        "--kpi-endpoint",
        help="Optional KPI endpoint, default is provider-specific",
    )
    parser.add_argument(
        "--kpi-metric-prefix",
        default="goblin.llamacpp_colab",
        help="Metric prefix for KPI metrics",
    )
    parser.add_argument(
        "--kpi-tags",
        default="env:colab,region:colab",
        help="Comma-separated tags for KPI metrics",
    )

    args = parser.parse_args()

    config_path = Path(args.config_path)

    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        print("Make sure you're running this from the correct directory.")
        return 1

    print("🔧 Configuring Goblin Assistant for Colab llama.cpp server")
    print("=" * 60)

    # Update configuration
    if not update_provider_config(config_path, args.ngrok_url, args.model):
        return 1

    # Optionally configure KPI settings
    if args.kpi_provider:
        try:
            import tomllib
            import tomli_w

            with open(config_path, "rb") as f:
                cfg = tomllib.load(f)
            provider_cfg = cfg["providers"]["llamacpp_colab"]
            provider_cfg["kpi"] = {
                "enabled": True,
                "provider": args.kpi_provider,
                "api_key_env": args.kpi_api_env,
                "endpoint": args.kpi_endpoint
                or (
                    "https://api.datadoghq.com/api/v1/series"
                    if args.kpi_provider == "datadog"
                    else args.kpi_endpoint
                ),
                "metric_prefix": args.kpi_metric_prefix,
                "tags": [t.strip() for t in args.kpi_tags.split(",") if t.strip()],
            }
            with open(config_path, "wb") as f:
                tomli_w.dump(cfg, f)
            print(f"✅ Added KPI config for '{args.kpi_provider}' to {config_path}")
        except Exception as e:
            print(f"❌ Failed to add KPI config: {e}")
            return 1

    # Test connection if requested
    if args.test_connection:
        print("\\n🧪 Testing connection...")
        if not test_connection(args.ngrok_url):
            print("⚠️  Connection test failed, but configuration was updated.")
            print("   Make sure the Colab server is running and accessible.")

    print("\\n📋 Next Steps:")
    print("1. Restart the Goblin Assistant backend:")
    print("   cd goblin-assistant/api && python start_server.py")
    print("\\n2. Test the integration:")
    print(
        '   python test_api.py --endpoint /routing/route --data \'{"task_type": "chat", "payload": {"messages": [{"role": "user", "content": "Hello from Colab!"}]}}\''
    )

    print(
        "\\n3. The routing system will now include llamacpp_colab as an available provider"
    )
    print("   with high priority for chat, reasoning, and code tasks.")

    return 0


if __name__ == "__main__":
    exit(main())
