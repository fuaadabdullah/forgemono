#!/bin/bash
# Envoy Gateway Installation Script
# This script installs Envoy Gateway and configures Overmind ingress

set -euo pipefail

NAMESPACE="${NAMESPACE:-overmind-prod}"
GATEWAY_API_VERSION="${GATEWAY_API_VERSION:-v1.0.0}"
ENVOY_GATEWAY_VERSION="${ENVOY_GATEWAY_VERSION:-v1.0.0}"

echo "🚀 Installing Envoy Gateway..."

# Install Gateway API CRDs
echo "📦 Installing Gateway API CRDs v${GATEWAY_API_VERSION}..."
kubectl apply -f "https://github.com/kubernetes-sigs/gateway-api/releases/download/${GATEWAY_API_VERSION}/standard-install.yaml"

echo "✅ Gateway API CRDs installed"

# Install Envoy Gateway
echo "📦 Installing Envoy Gateway v${ENVOY_GATEWAY_VERSION}..."
helm install eg oci://docker.io/envoyproxy/gateway-helm \
  --version "${ENVOY_GATEWAY_VERSION}" \
  -n envoy-gateway-system \
  --create-namespace \
  --wait

echo "✅ Envoy Gateway installed"

# Wait for Envoy Gateway to be ready
echo "🔍 Waiting for Envoy Gateway..."
kubectl wait --timeout=5m -n envoy-gateway-system \
  deployment/envoy-gateway --for=condition=Available

echo "✅ Envoy Gateway is ready"

# Create namespace for Overmind
kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -

# Apply Gateway resources
echo "📊 Applying Gateway resources..."

# Gateway
kubectl apply -f gateway/gateway.yaml

# HTTPRoutes
kubectl apply -f gateway/httproutes/

# Rate limits
kubectl apply -f gateway/rate-limits/

# Security policies
kubectl apply -f gateway/security/

# Traffic policies
kubectl apply -f gateway/client-traffic/
kubectl apply -f gateway/backend-traffic/

echo "✅ Gateway resources applied"

# Wait for Gateway to be ready
echo "🔍 Waiting for Gateway to be ready..."
kubectl wait --timeout=5m -n "${NAMESPACE}" \
  gateway/overmind-gateway --for=condition=Programmed

# Get Gateway address
echo "📡 Gateway Address:"
GATEWAY_ADDRESS=$(kubectl get gateway overmind-gateway -n "${NAMESPACE}" \
  -o jsonpath='{.status.addresses[0].value}' 2>/dev/null || echo "Pending...")

if [ "$GATEWAY_ADDRESS" != "Pending..." ]; then
  echo "   ${GATEWAY_ADDRESS}"
  echo ""
  echo "✅ Update DNS records:"
  echo "   dashboard.overmind.example.com → ${GATEWAY_ADDRESS}"
  echo "   api.overmind.example.com → ${GATEWAY_ADDRESS}"
else
  echo "   Waiting for LoadBalancer assignment..."
fi

# Show status
echo ""
echo "📊 Gateway Status:"
kubectl get gateway -n "${NAMESPACE}"

echo ""
echo "📊 HTTPRoutes:"
kubectl get httproute -n "${NAMESPACE}"

echo ""
echo "✅ Envoy Gateway setup complete!"
echo ""
echo "Next steps:"
echo "1. Create TLS certificate:"
echo "   kubectl create secret tls overmind-tls \\"
echo "     --cert=tls.crt --key=tls.key -n ${NAMESPACE}"
echo ""
echo "2. Test routes:"
echo "   curl -H 'Host: api.overmind.example.com' http://${GATEWAY_ADDRESS}/health"
echo ""
echo "3. Monitor metrics:"
echo "   kubectl port-forward -n envoy-gateway-system deployment/envoy-gateway 19000:19000"
echo "   curl http://localhost:19000/stats/prometheus"
