# Vault Integration

This document describes how to integrate HashiCorp Vault with Goblin Assistant for secrets management, how to rotate provider API keys, and how to run Vault in dev and production.

## Goals

- Secure secret storage for API keys and sensitive configuration.
- Centralize provider keys under `secret/goblin-assistant/providers/<provider>`.
- Provide one-click rotation automation for dev/prod secrets.
- Make it safe and auditable: backup old keys and record rotation metadata.

## Quickstart: Dev Vault

1. Start a local dev Vault:

```bash
# start dev vault
vault server -dev -dev-root-token-id=root &
export VAULT_ADDR=http://127.0.0.1:8200
export VAULT_TOKEN=root
```

2. Store provider API keys for a provider (example `local-llama`):

```bash

vault kv put secret/goblin-assistant/providers/local-llama api_key=demo api_secret=demo
```

3. Load provider keys into env (for local dev):

```bash
python -c "from vault_client import VaultClient; VaultClient.load_env_from_vault()"
source .env.vault  # if created by load_env_from_vault
```

## Using VaultClient

The `vault_client.py` helper is available at the repo root. Typical usage:

```python

from vault_client import get_api_key
key = get_api_key('openai-gpt4')
```

Use `VaultClient.get_provider_keys(provider)` to fetch a dictionary with the provider secrets.

## Rotation Script (tools/rotate_vault_keys.py)

A small rotation script is available in `tools/rotate_vault_keys.py` that performs safe rotation:

- Back up current key value to `secret/goblin-assistant/backups/<provider>/<timestamp>`.
- Store new key value under `secret/goblin-assistant/providers/<provider>`.
- Optionally, log the change to a 'rotations' path and set an expiration tag (if supported by production vault policies).

Usage:

```bash
# Rotate with a user-provided new key
python tools/rotate_vault_keys.py --provider openai-gpt4 --new-key xxxxx

# Auto-generate a random replacement for dev (demo only)
python tools/rotate_vault_keys.py --provider local-llama --auto
```

Note: The rotation script **does not** integrate with external provider APIs to generate provider-side API keys. For production, you must use the provider's API (OpenAI, Anthropic, etc.) to rotate keys and then update Vault with the new key. The script functions as the Vault side of a rotation workflow.

## Production Tips

- Use AppRole or Kubernetes auth to give the service a short-lived token.
- Limit policies to specific KV paths (e.g., `secret/data/goblin-assistant/providers/*`).
- Protect the VAULT_TOKEN used for CI with restricted access (only authorized pipeline service accounts). Use dynamic tokens where supported.
- Audit all `vault` API calls with Vault audit devices.

## Rotating a Provider Key (recommended steps)

1. Create new API key with provider API (OpenAI / Anthropic / etc.).
2. Back up current Vault key (or export audit data), and store new key in Vault using rotation script or your CI job.
3. Deploy the new secrets to apps with a blue/green or canary rollout—update env values and reload.
4. Monitor metrics & logs. If anything breaks, rollback by reapplying the previous key from backup path.
5. Revoke the old key on the provider side after confirming the new key works.

## Automation

In CI, rotate keys by calling provider API and writing new values to Vault. Use short-lived Vault dynamic tokens with a limited scope so the CI identity can only write to the path needed.

```yaml

# Example GitHub Actions step (pseudocode)

- name: Rotate openai key
  uses: actions/checkout@v3
  env:
    VAULT_ADDR: ${{ secrets.VAULT_ADDR }}
    VAULT_TOKEN: ${{ secrets.VAULT_TOKEN }}
  run: |
    python tools/rotate_vault_keys.py --provider openai-gpt4 --new-key ${{ steps.create_openai_key.outputs.key }}
```

## Troubleshooting

- If developer cannot access vault from CI, check `VAULT_ADDR` and `VAULT_TOKEN` and then `vault kv get secret/goblin-assistant/providers/<provider>` manually.
- Use `vault audit` to trace calls during rotations.

## Best Practices

- Never keep secrets in git.
- Use Vault to store and audit all provider keys.
- Rotate keys regularly (quarterly for production keys, monthly for dev keys).
- Use RBAC and dynamic tokens for running services.

---
Last updated: 2025-11-26
