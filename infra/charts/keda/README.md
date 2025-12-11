---title: KEDA Autoscaling for Overmind
type: reference
project: GoblinOS/Overmind
status: published
owner: GoblinOS
goblin_name: Overmind KEDA
description: "README"

---

# KEDA Autoscaling

[KEDA](https://keda.sh/) (Kubernetes Event-Driven Autoscaling) provides advanced autoscaling for Overmind based on event sources and custom metrics.

## Overview

KEDA replaces traditional HPA with:

- ✅ **Event-driven scaling** - Scale based on NATS queue depth, Prometheus metrics
- ✅ **Scale-to-zero** - Save costs in dev environments
- ✅ **Multiple triggers** - Combine CPU, memory, and custom metrics
- ✅ **External scalers** - Support for 60+ event sources
- ✅ **Fallback policies** - Handle metric unavailability gracefully

## Architecture

```
KEDA Operator → Monitors ScaledObjects
├── Prometheus Scaler → llm_request_rate metric
├── NATS JetStream Scaler → routing-decisions queue depth
├── Memory Scaler → memory_consolidation_queue_depth
└── Creates/manages HPA → Scales Deployments
```

## Quick Start

### Install KEDA

```bash
# Add Helm repo
helm repo add kedacore https://kedacore.github.io/charts
helm repo update

# Install KEDA operator
helm install keda kedacore/keda \
  --namespace keda \
  --create-namespace \
  --version 2.14.0

# Verify installation
kubectl get pods -n keda
kubectl get crd | grep keda
```

### Verify KEDA is Running

```bash

# Check operator pods
kubectl get pods -n keda

# Should see

# keda-operator-<hash>

# keda-metrics-apiserver-<hash>
```

## ScaledObject Examples

### LiteLLM Gateway Autoscaling

Scale based on LLM request rate from Prometheus:

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: litellm-scaler
  namespace: overmind-prod
spec:
  scaleTargetRef:
    name: litellm

  # Scaling behavior
  minReplicaCount: 2
  maxReplicaCount: 20
  pollingInterval: 30
  cooldownPeriod: 300

  # Triggers
  triggers:
  # Prometheus: LLM request rate
  - type: prometheus
    metadata:
      serverAddress: http://prometheus:9090
      metricName: llm_requests_per_second
      query: sum(rate(llm_request_total[1m]))
      threshold: "10"  # Scale up if > 10 req/sec

  # CPU fallback
  - type: cpu
    metricType: Utilization
    metadata:
      value: "70"
```

### Temporal Worker Autoscaling

Scale based on memory consolidation queue depth:

```yaml

apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: temporal-worker-scaler
  namespace: overmind-prod
spec:
  scaleTargetRef:
    name: temporal-worker

  minReplicaCount: 2
  maxReplicaCount: 10
  pollingInterval: 30
  cooldownPeriod: 300

  triggers:
  # Temporal queue depth (via Prometheus)

  - type: prometheus
    metadata:
      serverAddress: <http://prometheus:9090>
      metricName: temporal_queue_depth
      query: sum(temporal_task_queue_depth{task_queue="overmind-memory"})
      threshold: "5"  # Scale if > 5 tasks pending

  # Memory utilization

  - type: memory
    metricType: Utilization
    metadata:
      value: "80"
```

### API Server Autoscaling with NATS

Scale based on NATS JetStream queue depth:

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: overmind-api-scaler
  namespace: overmind-prod
spec:
  scaleTargetRef:
    name: overmind-api

  minReplicaCount: 2
  maxReplicaCount: 15
  pollingInterval: 30
  cooldownPeriod: 300

  triggers:
  # NATS JetStream: routing decisions queue
  - type: nats-jetstream
    metadata:
      natsServerMonitoringEndpoint: nats:8222
      stream: routing-decisions
      consumer: api-consumer
      lagThreshold: "10"  # Scale if > 10 messages behind

  # CPU utilization
  - type: cpu
    metricType: Utilization
    metadata:
      value: "70"
```

### Bridge Autoscaling (Dev with Scale-to-Zero)

```yaml

apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: overmind-bridge-scaler
  namespace: overmind-dev
spec:
  scaleTargetRef:
    name: overmind-bridge

  # Scale to zero in dev when idle
  minReplicaCount: 0
  maxReplicaCount: 5
  pollingInterval: 30
  cooldownPeriod: 600  # 10 min idle before scaling to 0

  triggers:
  # Prometheus: HTTP requests

  - type: prometheus
    metadata:
      serverAddress: <http://prometheus:9090>
      metricName: http_requests_per_minute
      query: sum(rate(http_requests_total{service="bridge"}[1m])) * 60
      threshold: "1"  # Scale up if > 1 req/min
```

## Advanced Patterns

### Multiple Triggers (AND logic)

Scale only if ALL conditions are met:

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: multi-trigger-scaler
spec:
  scaleTargetRef:
    name: overmind-api

  minReplicaCount: 2
  maxReplicaCount: 20

  # Advanced mode: AND logic
  advanced:
    horizontalPodAutoscalerConfig:
      behavior:
        scaleDown:
          stabilizationWindowSeconds: 300
          policies:
          - type: Percent
            value: 50
            periodSeconds: 60

  triggers:
  - type: prometheus
    metadata:
      serverAddress: http://prometheus:9090
      query: sum(rate(llm_request_total[1m]))
      threshold: "10"

  - type: cpu
    metricType: Utilization
    metadata:
      value: "70"

  - type: memory
    metricType: Utilization
    metadata:
      value: "80"
```

### Fallback Policy

Handle metric unavailability:

```yaml

apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: fallback-scaler
spec:
  scaleTargetRef:
    name: overmind-api

  minReplicaCount: 2
  maxReplicaCount: 20

  fallback:
    failureThreshold: 3  # Fail after 3 attempts
    replicas: 5          # Scale to this if metrics unavailable

  triggers:

  - type: prometheus
    metadata:
      serverAddress: <http://prometheus:9090>
      query: sum(rate(llm_request_total[1m]))
      threshold: "10"
```

### Custom Metrics from Prometheus

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: custom-metrics-scaler
spec:
  scaleTargetRef:
    name: overmind-api

  minReplicaCount: 2
  maxReplicaCount: 20

  triggers:
  # LLM cost per hour
  - type: prometheus
    metadata:
      serverAddress: http://prometheus:9090
      metricName: llm_cost_per_hour
      query: sum(rate(llm_cost_total[1h])) * 3600
      threshold: "100"  # Scale if cost > $100/hr

  # Memory consolidation backlog
  - type: prometheus
    metadata:
      serverAddress: http://prometheus:9090
      metricName: memory_backlog
      query: sum(memory_consolidation_queue_depth)
      threshold: "50"
```

## Monitoring

### KEDA Metrics

KEDA exposes Prometheus metrics:

```bash

# Port forward metrics endpoint
kubectl port-forward -n keda svc/keda-operator-metrics-apiserver 8080:8080

# Query metrics
curl <http://localhost:8080/metrics> | grep keda

# Key metrics

# keda_scaler_errors_total

# keda_scaled_object_paused

# keda_scaler_metrics_value

# keda_scaled_object_errors
```

### Grafana Dashboard

Import KEDA dashboard (ID: 18172):

```bash
# Add to Grafana
# Dashboard → Import → 18172
```

## Troubleshooting

### ScaledObject not scaling

```bash

# Check ScaledObject status
kubectl describe scaledobject <name> -n <namespace>

# Check KEDA operator logs
kubectl logs -n keda deployment/keda-operator

# Check HPA created by KEDA
kubectl get hpa -n <namespace>
```

### Metrics unavailable

```bash
# Test Prometheus query
kubectl run -it --rm curl --image=curlimages/curl --restart=Never -- \
  curl http://prometheus:9090/api/v1/query?query=<your_query>

# Check NATS monitoring endpoint
kubectl run -it --rm curl --image=curlimages/curl --restart=Never -- \
  curl http://nats:8222/streaming/channelsz
```

### Scale-to-zero not working

```bash

# Check cooldown period elapsed
kubectl describe scaledobject <name> -n <namespace> | grep -A5 Conditions

# Check if metrics are truly zero
kubectl get --raw /apis/external.metrics.k8s.io/v1beta1
```

## Best Practices

1. **Start conservative** - Begin with higher thresholds, adjust based on load
1. **Use fallback policies** - Handle metric unavailability gracefully
1. **Set appropriate cooldown** - Prevent flapping (300-600s recommended)
1. **Combine triggers** - Use both custom metrics and CPU/memory
1. **Monitor KEDA metrics** - Watch for scaler errors
1. **Test scale-to-zero** - Verify activation from zero replicas
1. **Use stabilization windows** - Smooth out rapid changes

## Migration from HPA

### Step 1: Identify existing HPAs

```bash
kubectl get hpa --all-namespaces
```

### Step 2: Convert to ScaledObject

For each HPA, create equivalent ScaledObject:

```yaml

# Old HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: litellm
spec:
  minReplicas: 2
  maxReplicas: 20
  metrics:

  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70

# New ScaledObject
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: litellm-scaler
spec:
  scaleTargetRef:
    name: litellm
  minReplicaCount: 2
  maxReplicaCount: 20
  triggers:

  - type: cpu
    metricType: Utilization
    metadata:
      value: "70"
```

### Step 3: Apply and verify

```bash
# Apply ScaledObject
kubectl apply -f scaledobject.yaml

# KEDA will create HPA automatically
kubectl get hpa

# Delete old HPA if needed
kubectl delete hpa <name>
```

## References

- [KEDA Documentation](https://keda.sh/docs/)
- [Scalers Catalog](https://keda.sh/docs/scalers/)
- [Prometheus Scaler](https://keda.sh/docs/scalers/prometheus/)
- [NATS JetStream Scaler](https://keda.sh/docs/scalers/nats-jetstream/)

## License

MIT
