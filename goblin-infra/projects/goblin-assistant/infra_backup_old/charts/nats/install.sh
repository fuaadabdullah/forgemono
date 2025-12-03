#!/bin/bash
# NATS JetStream Installation Script
# This script installs NATS JetStream and creates streams for Overmind

set -euo pipefail

NAMESPACE="${NAMESPACE:-overmind-prod}"
NATS_VERSION="${NATS_VERSION:-1.1.5}"

echo "🚀 Installing NATS JetStream v${NATS_VERSION}..."

# Add Helm repo
helm repo add nats https://nats-io.github.io/k8s/helm/charts/
helm repo update

# Create namespace if it doesn't exist
kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -

# Install NATS with JetStream
helm upgrade --install nats nats/nats \
  --namespace "${NAMESPACE}" \
  --version "${NATS_VERSION}" \
  --set nats.jetstream.enabled=true \
  --set nats.jetstream.fileStorage.enabled=true \
  --set nats.jetstream.fileStorage.size=10Gi \
  --set nats.jetstream.memStorage.enabled=true \
  --set nats.jetstream.memStorage.size=2Gi \
  --set nats.replicas=3 \
  --set nats.resources.requests.cpu=200m \
  --set nats.resources.requests.memory=512Mi \
  --set nats.resources.limits.cpu=1000m \
  --set nats.resources.limits.memory=2Gi \
  --set nats.exporter.enabled=true \
  --set nats.exporter.serviceMonitor.enabled=true \
  --set podDisruptionBudget.enabled=true \
  --set podDisruptionBudget.minAvailable=2 \
  --wait

echo "✅ NATS JetStream installed"

# Wait for NATS to be ready
echo "🔍 Waiting for NATS pods..."
kubectl wait --for=condition=ready pod \
  -l app.kubernetes.io/name=nats \
  -n "${NAMESPACE}" \
  --timeout=300s

echo "✅ NATS is ready"

# Install NATS CLI (if not already installed)
if ! command -v nats &> /dev/null; then
  echo "📦 Installing NATS CLI..."
  if [[ "$OSTYPE" == "darwin"* ]]; then
    brew tap nats-io/nats-tools
    brew install nats-io/nats-tools/nats
  else
    curl -sf https://binaries.nats.dev/nats-io/natscli/nats@latest | sh
  fi
  echo "✅ NATS CLI installed"
fi

# Port forward for local access
echo "🔌 Setting up port forward..."
kubectl port-forward -n "${NAMESPACE}" svc/nats 4222:4222 &
PF_PID=$!
sleep 3

# Create streams
echo "📊 Creating JetStream streams..."

# routing-decisions stream
nats stream add routing-decisions \
  --subjects="routing.model.selected,routing.fallback.triggered,routing.cost.calculated" \
  --retention=limits \
  --max-age=168h \
  --max-bytes=1GB \
  --max-msgs=1000000 \
  --storage=file \
  --replicas=3 \
  --discard=old \
  --server=nats://localhost:4222 \
  --defaults || echo "Stream routing-decisions may already exist"

echo "✅ Created routing-decisions stream"

# memory-events stream
nats stream add memory-events \
  --subjects="memory.added,memory.consolidated,memory.retrieved,memory.expired" \
  --retention=limits \
  --max-age=720h \
  --max-bytes=5GB \
  --max-msgs=5000000 \
  --storage=file \
  --replicas=3 \
  --discard=old \
  --server=nats://localhost:4222 \
  --defaults || echo "Stream memory-events may already exist"

echo "✅ Created memory-events stream"

# llm-requests stream
nats stream add llm-requests \
  --subjects="llm.request.started,llm.request.completed,llm.request.failed" \
  --retention=limits \
  --max-age=24h \
  --max-bytes=500MB \
  --max-msgs=500000 \
  --storage=file \
  --replicas=3 \
  --discard=old \
  --server=nats://localhost:4222 \
  --defaults || echo "Stream llm-requests may already exist"

echo "✅ Created llm-requests stream"

# Create consumers
echo "👥 Creating JetStream consumers..."

# api-consumer for routing-decisions
nats consumer add routing-decisions api-consumer \
  --filter="routing.>" \
  --ack=explicit \
  --pull \
  --deliver=all \
  --max-deliver=3 \
  --wait=30s \
  --server=nats://localhost:4222 \
  --defaults || echo "Consumer api-consumer may already exist"

echo "✅ Created api-consumer"

# consolidation-consumer for memory-events
nats consumer add memory-events consolidation-consumer \
  --filter="memory.consolidated" \
  --ack=explicit \
  --pull \
  --deliver=all \
  --max-deliver=3 \
  --wait=120s \
  --server=nats://localhost:4222 \
  --defaults || echo "Consumer consolidation-consumer may already exist"

echo "✅ Created consolidation-consumer"

# metrics-consumer for llm-requests
nats consumer add llm-requests metrics-consumer \
  --filter="llm.>" \
  --ack=explicit \
  --pull \
  --deliver=all \
  --max-deliver=3 \
  --wait=30s \
  --server=nats://localhost:4222 \
  --defaults || echo "Consumer metrics-consumer may already exist"

echo "✅ Created metrics-consumer"

# Kill port forward
kill $PF_PID 2>/dev/null || true

# Show status
echo ""
echo "📊 NATS JetStream Status:"
kubectl get pods -n "${NAMESPACE}" -l app.kubernetes.io/name=nats

echo ""
echo "✅ NATS JetStream setup complete!"
echo ""
echo "Next steps:"
echo "1. Verify streams:"
echo "   kubectl port-forward -n ${NAMESPACE} svc/nats 4222:4222"
echo "   nats stream list --server=nats://localhost:4222"
echo ""
echo "2. Publish test message:"
echo "   nats pub --server=nats://localhost:4222 routing.model.selected '{\"model\":\"gemini-pro\"}'"
echo ""
echo "3. Monitor metrics:"
echo "   kubectl port-forward -n ${NAMESPACE} svc/nats 7777:7777"
echo "   curl http://localhost:7777/metrics | grep nats_jetstream"
