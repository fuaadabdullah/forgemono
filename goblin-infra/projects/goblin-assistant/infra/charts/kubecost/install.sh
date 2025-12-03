#!/bin/bash
# Kubecost Installation Script
# This script installs Kubecost and configures cost monitoring for Overmind

set -euo pipefail

NAMESPACE="${NAMESPACE:-kubecost}"
KUBECOST_VERSION="${KUBECOST_VERSION:-2.0.0}"
PROMETHEUS_URL="${PROMETHEUS_URL:-http://prometheus-server.observability.svc.cluster.local:9090}"
CLUSTER_ID="${CLUSTER_ID:-overmind-prod}"

echo "🚀 Installing Kubecost..."

# Add Kubecost Helm repository
echo "📦 Adding Kubecost Helm repository..."
helm repo add kubecost https://kubecost.github.io/cost-analyzer/
helm repo update

echo "✅ Kubecost repository added"

# Create namespace
kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -

echo "✅ Namespace ${NAMESPACE} created"

# Install Kubecost
echo "📦 Installing Kubecost v${KUBECOST_VERSION}..."
helm upgrade --install kubecost kubecost/cost-analyzer \
  --namespace "${NAMESPACE}" \
  --version "${KUBECOST_VERSION}" \
  --set global.prometheus.fqdn="${PROMETHEUS_URL}" \
  --set global.prometheus.enabled=true \
  --set prometheus.server.global.external_labels.cluster_id="${CLUSTER_ID}" \
  --set networkCosts.enabled=true \
  --set networkCosts.podMonitor.enabled=true \
  --set persistentVolume.enabled=true \
  --set persistentVolume.size=10Gi \
  --set ingress.enabled=false \
  --wait \
  --timeout 10m

echo "✅ Kubecost installed"

# Wait for Kubecost to be ready
echo "🔍 Waiting for Kubecost to be ready..."
kubectl wait --timeout=5m -n "${NAMESPACE}" \
  deployment/kubecost-cost-analyzer --for=condition=Available

echo "✅ Kubecost is ready"

# Apply alerts
echo "📊 Applying cost alerts..."
kubectl apply -f alerts/

echo "✅ Alerts configured"

# Apply ServiceMonitor
echo "📊 Applying ServiceMonitor..."
kubectl apply -f monitoring/

echo "✅ ServiceMonitor configured"

# Get Kubecost URL
echo ""
echo "📡 Kubecost is running!"
echo ""
echo "Access Kubecost UI:"
echo "  kubectl port-forward -n ${NAMESPACE} deployment/kubecost-cost-analyzer 9090:9090"
echo "  open http://localhost:9090"
echo ""

# Show example queries
echo "Example queries:"
echo ""
echo "# Get today's costs by namespace"
echo "curl -G http://localhost:9090/model/allocation \\"
echo "  -d window=today \\"
echo "  -d aggregate=namespace"
echo ""
echo "# Get weekly costs by service"
echo "curl -G http://localhost:9090/model/allocation \\"
echo "  -d window=7d \\"
echo "  -d aggregate=service \\"
echo "  -d filterNamespaces=overmind-prod"
echo ""

# Show current costs (if port-forward is active)
echo "💰 Current namespace costs:"
kubectl port-forward -n "${NAMESPACE}" deployment/kubecost-cost-analyzer 9090:9090 &
PF_PID=$!
sleep 5

# Query today's costs
if curl -s -G http://localhost:9090/model/allocation \
  -d window=today \
  -d aggregate=namespace \
  --max-time 5 > /tmp/kubecost-costs.json 2>/dev/null; then

  echo ""
  cat /tmp/kubecost-costs.json | jq -r '.data[] | "\(.name): $\(.totalCost | tonumber | floor)"'
  rm /tmp/kubecost-costs.json
else
  echo "  (API not ready yet - try again in a few minutes)"
fi

# Kill port-forward
kill $PF_PID 2>/dev/null || true

echo ""
echo "✅ Kubecost setup complete!"
echo ""
echo "Next steps:"
echo "1. Configure Slack webhook for alerts:"
echo "   kubectl create secret generic kubecost-slack \\"
echo "     --from-literal=webhook=https://hooks.slack.com/... \\"
echo "     -n ${NAMESPACE}"
echo ""
echo "2. Review cost allocation:"
echo "   kubectl port-forward -n ${NAMESPACE} deployment/kubecost-cost-analyzer 9090:9090"
echo "   open http://localhost:9090"
echo ""
echo "3. Set up Grafana dashboards:"
echo "   Import dashboards from dashboards/"
echo ""
echo "4. Review savings recommendations weekly"
