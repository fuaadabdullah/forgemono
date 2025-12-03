#!/usr/bin/env bash
set -euo pipefail

# Install ExternalSecrets controller via Helm (recommended)
# This script performs a simple helm install/upgrade into the cluster.

NAMESPACE=${1:-external-secrets}
RELEASE_NAME=${2:-external-secrets}

if ! command -v helm >/dev/null 2>&1; then
  echo "helm CLI required. Install https://helm.sh/" >&2
  exit 1
fi

echo "Creating namespace $NAMESPACE"
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

echo "Adding helm repo and updating"
helm repo add external-secrets https://charts.external-secrets.io
helm repo update

echo "Installing ExternalSecrets controller (release: $RELEASE_NAME)"
helm upgrade --install $RELEASE_NAME external-secrets/external-secrets -n $NAMESPACE --set installCRDs=true

echo "ExternalSecrets controller installed. Verify with: kubectl -n $NAMESPACE get pods"
