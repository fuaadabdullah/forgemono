#!/usr/bin/env bash
set -euo pipefail

# Render the kube-prometheus-stack Helm chart into a directory used by kustomize.
# Outputs YAML files to infra/observability/helm/rendered/

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
RENDER_DIR="$ROOT_DIR/helm/rendered"
VALUES_FILE="$ROOT_DIR/helm/values.yaml"
RELEASE_NAME=${1:-kube-prometheus-stack}
NAMESPACE=${2:-observability}

mkdir -p "$RENDER_DIR"
rm -f "$RENDER_DIR"/*.yaml || true

if ! command -v helm >/dev/null 2>&1; then
  echo "helm CLI required to render chart" >&2
  exit 1
fi

echo "Rendering kube-prometheus-stack to $RENDER_DIR"
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts >/dev/null
helm repo update >/dev/null

helm template "$RELEASE_NAME" prometheus-community/kube-prometheus-stack \
  -n "$NAMESPACE" \
  -f "$VALUES_FILE" \
  --include-crds \
  --output-dir "$RENDER_DIR/_helm"

# Helm 3 --output-dir creates directories. Collect rendered YAML into render dir root.
if [ -d "$RENDER_DIR/_helm/$RELEASE_NAME" ]; then
  find "$RENDER_DIR/_helm/$RELEASE_NAME" -type f -name '*.yaml' -exec cp {} "$RENDER_DIR/" \;
fi

echo "Rendered files:" $(ls -1 "$RENDER_DIR" | wc -l)
