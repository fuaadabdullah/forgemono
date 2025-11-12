#!/usr/bin/env bash
set -euo pipefail

# Bootstrap Vault for observability ExternalSecrets usage.
# Requirements:
# - vault CLI installed and authenticated (VAULT_ADDR + VAULT_TOKEN env or logged in)
# - kubectl configured with access to the cluster
#
# What this script does:
# 1. Writes a Vault policy 'observability-policy' (reads grafana/loki/tempo secrets)
# 2. Writes example secrets for grafana, loki, and tempo
# 3. Creates a Vault token scoped to that policy
# 4. Stores the token as a Kubernetes secret 'vault-token' in the observability namespace

POLICY_NAME=${POLICY_NAME:-observability-policy}
VAULT_MOUNT=${VAULT_MOUNT:-secret}
K8S_NS=${K8S_NS:-observability}

if ! command -v vault >/dev/null 2>&1; then
  echo "vault CLI is required (https://www.vaultproject.io/docs/cli)." >&2
  exit 1
fi

if ! command -v kubectl >/dev/null 2>&1; then
  echo "kubectl is required." >&2
  exit 1
fi

echo "Applying policy ${POLICY_NAME} to Vault (mount: ${VAULT_MOUNT})"
vault policy write ${POLICY_NAME} observability-policy.hcl

echo "Seeding example secrets into Vault (grafana, loki, tempo)."
# Note: these are example values — replace with secure values in production.
vault kv put ${VAULT_MOUNT}/grafana admin-password="changeme-please-replace"
vault kv put ${VAULT_MOUNT}/loki aws_access_key_id="MINIOACCESS" aws_secret_access_key="MINIOSECRET"
vault kv put ${VAULT_MOUNT}/tempo aws_access_key_id="MINIOACCESS" aws_secret_access_key="MINIOSECRET"

echo "Creating Vault token bound to policy ${POLICY_NAME}"
TOKEN_JSON=$(vault token create -policy=${POLICY_NAME} -format=json -ttl=720h)
CLIENT_TOKEN=$(echo "$TOKEN_JSON" | jq -r .auth.client_token)

if [ -z "$CLIENT_TOKEN" ] || [ "$CLIENT_TOKEN" = "null" ]; then
  echo "Failed to create token" >&2
  exit 1
fi

echo "Creating Kubernetes secret 'vault-token' in namespace ${K8S_NS}"
kubectl create namespace ${K8S_NS} --dry-run=client -o yaml | kubectl apply -f -
kubectl create secret generic vault-token --from-literal=token=${CLIENT_TOKEN} -n ${K8S_NS} --dry-run=client -o yaml | kubectl apply -f -

echo "Done. Vault policy created, example secrets written, and Kubernetes secret 'vault-token' created."
echo "Important: rotate the token and replace example secret values before use in production."
