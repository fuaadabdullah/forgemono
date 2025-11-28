# KEDA Installation Script
# This script installs KEDA operator and creates ScaledObjects for Overmind

set -euo pipefail

NAMESPACE="${KEDA_NAMESPACE:-keda}"
KEDA_VERSION="${KEDA_VERSION:-2.14.0}"
ENV="${ENV:-prod}"

echo "🚀 Installing KEDA v${KEDA_VERSION}..."

# Add Helm repo
helm repo add kedacore https://kedacore.github.io/charts
helm repo update

# Install KEDA operator
helm upgrade --install keda kedacore/keda \
  --namespace "${NAMESPACE}" \
  --create-namespace \
  --version "${KEDA_VERSION}" \
  --set prometheus.metricServer.enabled=true \
  --set prometheus.metricServer.port=8080 \
  --set prometheus.operator.enabled=true \
  --set prometheus.operator.port=8080 \
  --wait

echo "✅ KEDA operator installed"

# Verify installation
echo "🔍 Verifying KEDA installation..."
kubectl wait --for=condition=ready pod \
  -l app.kubernetes.io/name=keda-operator \
  -n "${NAMESPACE}" \
  --timeout=300s

echo "✅ KEDA operator is ready"

# Apply ScaledObjects based on environment
echo "📦 Applying ScaledObjects for environment: ${ENV}..."

if [ "${ENV}" = "dev" ]; then
  kubectl apply -f scaledobjects/overmind-bridge-scaler-dev.yaml
  echo "✅ Applied dev ScaledObjects (with scale-to-zero)"
elif [ "${ENV}" = "prod" ]; then
  kubectl apply -f scaledobjects/litellm-scaler.yaml
  kubectl apply -f scaledobjects/temporal-worker-scaler.yaml
  kubectl apply -f scaledobjects/overmind-api-scaler.yaml
  echo "✅ Applied prod ScaledObjects"
else
  echo "❌ Unknown environment: ${ENV}"
  echo "   Valid options: dev, prod"
  exit 1
fi

# Show status
echo "📊 KEDA Resources:"
kubectl get scaledobjects -n "overmind-${ENV}"
kubectl get hpa -n "overmind-${ENV}"

echo ""
echo "✅ KEDA setup complete!"
echo ""
echo "Next steps:"
echo "1. Verify metrics are available:"
echo "   kubectl get --raw /apis/external.metrics.k8s.io/v1beta1"
echo ""
echo "2. Monitor scaling:"
echo "   kubectl get hpa -n overmind-${ENV} --watch"
echo ""
echo "3. Check KEDA metrics:"
echo "   kubectl port-forward -n keda svc/keda-operator-metrics-apiserver 8080:8080"
echo "   curl http://localhost:8080/metrics | grep keda"
