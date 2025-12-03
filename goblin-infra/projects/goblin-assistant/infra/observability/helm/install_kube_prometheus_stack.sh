#!/usr/bin/env bash
set -euo pipefail

# Install or upgrade kube-prometheus-stack using Helm with example values provided.
# Usage: ./install_kube_prometheus_stack.sh [release_name] [namespace]

RELEASE=${1:-kube-prometheus-stack}
NAMESPACE=${2:-observability}
VALUES_FILE=$(dirname "$0")/values.yaml

if ! command -v helm >/dev/null 2>&1; then
  echo "helm is required" >&2
  exit 1
fi

echo "Creating namespace $NAMESPACE"
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

echo "Adding prometheus-community repo"
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

echo "Installing/upgrading $RELEASE in $NAMESPACE"
helm upgrade --install $RELEASE prometheus-community/kube-prometheus-stack -n $NAMESPACE -f "$VALUES_FILE"

echo "Installation complete. Monitor pods with: kubectl -n $NAMESPACE get pods"
