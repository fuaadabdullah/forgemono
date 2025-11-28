#!/usr/bin/env python3
"""
Rotate provider API keys stored in HashiCorp Vault (demo script)

This script demonstrates a safe pattern for rotating provider API keys:
 - Back up the existing key to a backups path: `secret/goblin-assistant/backups/<provider>/<timestamp>`
 - Store new key values in `secret/goblin-assistant/providers/<provider>`
 - (Optionally) Notify team, record audit metadata, and set a short TTL/policy

Note: For production, integrate provider API key creation (e.g., OpenAI admin API) to generate new keys.
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from uuid import uuid4
from typing import Optional

sys.path.append(".")
sys.path.append("goblin-assistant")

from vault_client import init_vault_from_env, VaultClient

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def rotate_provider_key(
    provider: str, new_key: Optional[str] = None, auto: bool = False
):
    vault = init_vault_from_env()
    if not vault:
        logger.error("Vault is not configured (set VAULT_ADDR and VAULT_TOKEN in env)")
        return 1

    if not new_key and not auto:
        logger.error("Either new_key must be provided or --auto flag must be used")
        return 2

    if auto:
        new_key = str(uuid4())

    base_path = f"secret/goblin-assistant/providers/{provider}"
    backup_path = (
        f"secret/goblin-assistant/backups/{provider}/{datetime.utcnow().isoformat()}"
    )

    # Read current key
    current = {}
    try:
        current = vault.get_provider_keys(provider)
    except Exception as e:
        logger.warning(f"Could not read current secrets for provider={provider}: {e}")

    # Back up the current secret data if found
    if current:
        try:
            vault.set_secret(backup_path, current)
            logger.info(f"Backed up existing provider key to {backup_path}")
        except Exception as e:
            logger.warning(f"Failed to back up old secrets for {provider}: {e}")

    # Replace the API key and write new value
    new_secrets = {**current, "api_key": new_key}
    try:
        vault.set_secret(base_path, new_secrets)
        logger.info(f"Rotated provider key for {provider} (stored at {base_path})")
    except Exception as e:
        logger.error(f"Failed to store new secrets for {provider}: {e}")
        return 3

    # Write an audit record (optional) to a known path
    try:
        audit_path = f"secret/goblin-assistant/rotations/{provider}"
        record = {
            "rotated_at": datetime.utcnow().isoformat(),
            "new_key_id": str(uuid4()),
        }
        vault.client.secrets.kv.v2.create_or_update_secret_version(
            path=audit_path, secret=record
        )
        logger.info(f"Rotation recorded in {audit_path}")
    except Exception as e:
        logger.warning(f"Failed to record audit rotation event for {provider}: {e}")

    logger.info(
        "Rotation complete — confirm by testing the new key in provider dev/test environment and then revoke the previous key on provider side."
    )
    return 0


def main():
    parser = argparse.ArgumentParser(description="Rotate provider keys in Vault (demo)")
    parser.add_argument(
        "--provider", required=True, help="Provider name (e.g., openai-gpt4)"
    )
    parser.add_argument("--new-key", help="New API key value to store")
    parser.add_argument(
        "--auto", action="store_true", help="Auto-generate a demo key (for dev only)"
    )
    args = parser.parse_args()

    code = rotate_provider_key(args.provider, args.new_key, args.auto)
    sys.exit(code)


if __name__ == "__main__":
    main()
