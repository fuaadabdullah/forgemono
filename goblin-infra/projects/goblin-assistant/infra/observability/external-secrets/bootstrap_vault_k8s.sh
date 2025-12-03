#!/usr/bin/env bash
set -euo pipefail

# Bootstrap Vault Kubernetes auth for observability ExternalSecrets usage.
# Requirements:
# - vault CLI installed and authenticated (VAULT_ADDR + VAULT_TOKEN env or logged in)
# - kubectl configured with access to the cluster
# - jq installed
#
# What this script does:
# 1. Creates a Kubernetes SA 'vault-auth' in kube-system and grants it 'system:auth-delegator'
# 2. Enables Vault 'kubernetes' auth method and configures it with the cluster CA and host
# 3. Writes an observability policy (observability-policy.hcl must be alongside the script)
# 4. Creates a Vault role 'external-secrets-role' bound to the ServiceAccount 'external-secrets' in namespace 'observability'
# 5. Creates the Kubernetes ServiceAccount 'external-secrets' in namespace 'observability'

KUBE_AUTH_SA=${KUBE_AUTH_SA:-vault-auth}
KUBE_AUTH_NS=${KUBE_AUTH_NS:-kube-system}
EXTERNAL_SECRETS_SA=${EXTERNAL_SECRETS_SA:-external-secrets}
EXTERNAL_SECRETS_NS=${EXTERNAL_SECRETS_NS:-observability}
VAULT_K8S_PATH=${VAULT_K8S_PATH:-kubernetes}
VAULT_ROLE_NAME=${VAULT_ROLE_NAME:-external-secrets-role}
POLICY_FILE=${POLICY_FILE:-observability-policy.hcl}

if ! command -v vault >/dev/null 2>&1; then
  echo "vault CLI is required." >&2
  exit 1
fi
if ! command -v kubectl >/dev/null 2>&1; then
  echo "kubectl is required." >&2
  exit 1
fi
if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required." >&2
  exit 1
fi

echo "Creating service account ${KUBE_AUTH_SA} in namespace ${KUBE_AUTH_NS}"
kubectl create namespace ${KUBE_AUTH_NS} --dry-run=client -o yaml | kubectl apply -f -
kubectl create serviceaccount ${KUBE_AUTH_SA} -n ${KUBE_AUTH_NS} --dry-run=client -o yaml | kubectl apply -f -

echo "Binding ${KUBE_AUTH_SA} to 'system:auth-delegator' clusterrole (required for TokenReview)
kubectl create clusterrolebinding ${KUBE_AUTH_SA}-auth-delegator --clusterrole=system:auth-delegator --serviceaccount=${KUBE_AUTH_NS}:${KUBE_AUTH_SA} --dry-run=client -o yaml | kubectl apply -f -

echo "Gathering Kubernetes API server and CA info from kubeconfig"
K8S_HOST=$(kubectl config view --raw -o jsonpath='{.clusters[0].cluster.server}')
K8S_CA_DATA=$(kubectl config view --raw -o jsonpath='{.clusters[0].cluster.certificate-authority-data}')
if [ -z "$K8S_CA_DATA" ]; then
  echo "Could not read cluster CA from kubeconfig. Exiting." >&2
  exit 1
fi
echo "$K8S_CA_DATA" | base64 --decode > /tmp/k8s_ca.crt

echo "Getting token for ${KUBE_AUTH_SA} to use as token_reviewer_jwt"
if kubectl create token ${KUBE_AUTH_SA} -n ${KUBE_AUTH_NS} >/dev/null 2>&1; then
  TOKEN_REVIEWER_JWT=$(kubectl create token ${KUBE_AUTH_SA} -n ${KUBE_AUTH_NS})
else
  # fallback: try to read secret associated with SA (older clusters)
  SECRET_NAME=$(kubectl -n ${KUBE_AUTH_NS} get sa ${KUBE_AUTH_SA} -o jsonpath='{.secrets[0].name}')
  TOKEN_REVIEWER_JWT=$(kubectl -n ${KUBE_AUTH_NS} get secret ${SECRET_NAME} -o jsonpath='{.data.token}' | base64 --decode)
fi

echo "Enabling Vault Kubernetes auth at path: ${VAULT_K8S_PATH}"
if vault auth list -format=json | jq -r "keys[]" | grep -q "^${VAULT_K8S_PATH}/"; then
  echo "Auth method already enabled at ${VAULT_K8S_PATH}, continuing"
else
  vault auth enable -path=${VAULT_K8S_PATH} kubernetes
fi

echo "Configuring Vault Kubernetes auth with API server and CA"
vault write auth/${VAULT_K8S_PATH}/config kubernetes_host=${K8S_HOST} kubernetes_ca_cert=@/tmp/k8s_ca.crt token_reviewer_jwt=${TOKEN_REVIEWER_JWT}

echo "Writing policy ${POLICY_FILE} into Vault as 'observability-policy'"
vault policy write observability-policy ${POLICY_FILE}

echo "Creating Kubernetes ServiceAccount ${EXTERNAL_SECRETS_SA} in namespace ${EXTERNAL_SECRETS_NS}"
kubectl create namespace ${EXTERNAL_SECRETS_NS} --dry-run=client -o yaml | kubectl apply -f -
kubectl create serviceaccount ${EXTERNAL_SECRETS_SA} -n ${EXTERNAL_SECRETS_NS} --dry-run=client -o yaml | kubectl apply -f -

echo "Creating Vault role ${VAULT_ROLE_NAME} bound to ${EXTERNAL_SECRETS_SA} in namespace ${EXTERNAL_SECRETS_NS}"
vault write auth/${VAULT_K8S_PATH}/role/${VAULT_ROLE_NAME} bound_service_account_names=${EXTERNAL_SECRETS_SA} bound_service_account_namespaces=${EXTERNAL_SECRETS_NS} policies=observability-policy ttl=24h

echo "Done. Vault Kubernetes auth configured and role created. ExternalSecrets controller can use the ServiceAccount '${EXTERNAL_SECRETS_SA}' to authenticate via Kubernetes auth."
