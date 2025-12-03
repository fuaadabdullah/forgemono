#!/usr/bin/env python3
"""
Test sending a KPI metric for the llamacpp_colab provider.

This script reads `goblin-assistant/config/providers.toml` and sends a simple
Datadog metric if the provider has KPI config and the required environment
variable is set. This helps validate that KPI wiring is configured.

Usage:
  python3 scripts/test_send_llamacpp_kpi.py --provider llamacpp_colab

Note: This script will not commit secrets to source control; it reads the API
key from the `api_key_env` specified in the provider configuration.
"""

import argparse
import os
import time
import tomllib
import requests


def load_provider_config(path, provider_name):
    with open(path, "rb") as f:
        data = tomllib.load(f)
    providers = data.get("providers", {})
    return providers.get(provider_name)


def send_datadog_metric(api_key, endpoint, metric_name, value, tags):
    headers = {
        "DD-API-KEY": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "series": [
            {
                "metric": metric_name,
                "points": [[int(time.time()), value]],
                "type": "gauge",
                "tags": tags,
            }
        ]
    }
    resp = requests.post(endpoint, headers=headers, json=payload, timeout=10)
    return resp


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", default="llamacpp_colab")
    parser.add_argument(
        "--config",
        default="goblin-assistant/config/providers.toml",
        help="Path to providers.toml",
    )
    args = parser.parse_args()
    provider = load_provider_config(args.config, args.provider)
    if not provider:
        print(f"Provider '{args.provider}' not found in {args.config}")
        return
    kpi = provider.get("kpi") or {}
    if not kpi.get("enabled"):
        print("KPI reporting disabled for provider; set kpi.enabled = true to test.")
        return
    provider_name = kpi.get("provider", "datadog")
    if provider_name != "datadog":
        print(f"Provider '{provider_name}' not supported by this test script yet.")
        return
    api_key_env = kpi.get("api_key_env")
    if not api_key_env:
        print(
            "No api_key_env configured for KPI; please add 'api_key_env' to the provider.kpi section in providers.toml"
        )
        return
    api_key = os.environ.get(api_key_env)
    if not api_key:
        print(
            f"Environment variable {api_key_env} is missing. Export it and re-run the script."
        )
        return
    endpoint = kpi.get("endpoint")
    metric_prefix = kpi.get("metric_prefix", "goblin.llamacpp_colab")
    tags = kpi.get("tags", ["env:colab"])
    metric_name = metric_prefix + ".test.latency"
    print(
        f"Sending a test metric to Datadog at {endpoint} as {metric_name} with tags {tags}..."
    )
    try:
        resp = send_datadog_metric(api_key, endpoint, metric_name, 0.123, tags)
        if resp.ok:
            print("Metric sent successfully.")
        else:
            print("Failed to send metric:", resp.status_code, resp.text)
    except Exception as e:
        print("Error sending metric:", e)


if __name__ == "__main__":
    main()
