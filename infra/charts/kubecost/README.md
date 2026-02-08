---title: Kubecost Cost Monitoring for Overmind
type: reference
project: GoblinOS/Overmind
status: published
owner: GoblinOS
goblin_name: Overmind Cost Monitor
description: "README"

---

# Kubecost Cost Monitoring

Cost monitoring, allocation, and optimization for Overmind using [Kubecost](https://www.kubecost.com/).

## Overview

> **Huntress Runbook Tip:** Trigger the VS Code task **"🎯 Magnolia: Kubecost smoke test"** (`tools/smoke.sh`) before deep-dive troubleshooting to ensure the allocation API responds locally.

Kubecost provides:

- 💰 **Cost allocation** - Per-namespace, per-service, per-label granularity
- 📊 **Real-time monitoring** - Live cost dashboards and metrics
- 💡 **Savings recommendations** - Rightsizing, spot instances, abandoned workloads
- 🚨 **Budget alerts** - Daily/monthly thresholds with Slack notifications
- 📈 **Trend analysis** - Historical cost data and forecasting
- 🔍 **Resource optimization** - CPU/memory efficiency tracking

## Architecture

```
Prometheus (9090)
    │
    ▼
┌─────────────────────────────────────┐
│        Kubecost Cost Analyzer       │
│  - Cost Allocation Engine           │
│  - Savings Recommendations          │
│  - Budget Alerts                    │
│  - Report Generation                │
└─────────────┬───────────────────────┘
              │
    ┌─────────┴─────────┬─────────────┐
    ▼                   ▼             ▼
┌──────────┐      ┌──────────┐   ┌──────────┐
│ Grafana  │      │  Alerts  │   │ Exports  │
│Dashboard │      │  Slack   │   │BigQuery/S3
└──────────┘      └──────────┘   └──────────┘

Cost Metrics:

- overmind-dev: CPU, Memory, Network, Storage
- overmind-prod: CPU, Memory, Network, Storage
- LiteLLM Gateway: API call costs
- Temporal Workers: Workflow execution costs
```

## Quick Start

### Install Kubecost

```bash
# Add Kubecost repo
helm repo add kubecost https://kubecost.github.io/cost-analyzer/
helm repo update

# Install Kubecost
cd infra/charts/kubecost
bash install.sh

# Verify installation
kubectl get pods -n kubecost
kubectl wait --timeout=5m -n kubecost \
  deployment/kubecost-cost-analyzer --for=condition=Available
```

### Access UI

```bash

# Port forward to Kubecost UI
kubectl port-forward -n kubecost \
  deployment/kubecost-cost-analyzer 9090:9090

# Open browser
open <http://localhost:9090>
```

### View Costs

```bash
# Get namespace costs
kubectl port-forward -n kubecost deployment/kubecost-cost-analyzer 9090:9090 &
curl http://localhost:9090/model/allocation \
  -d window=today \
  -d aggregate=namespace \
  -G

# Get service costs
curl http://localhost:9090/model/allocation \
  -d window=7d \
  -d aggregate=service \
  -d filterNamespaces=overmind-prod \
  -G
```

## Cost Allocation

### Namespace-Level Allocation

**Overmind Production:**
```yaml

namespace: overmind-prod
labels:
  environment: production
  project: overmind
  team: goblinos
  owner: GoblinOS

resources:
  cpu: 16 cores
  memory: 32Gi
  storage: 100Gi
  network: 1TB/month

daily_cost: ~$50-100
monthly_budget: $2000
```

**Overmind Development:**

```yaml
namespace: overmind-dev
labels:
  environment: development
  project: overmind
  team: goblinos
  owner: GoblinOS

resources:
  cpu: 4 cores
  memory: 8Gi
  storage: 20Gi
  network: 100GB/month

daily_cost: ~$10-50
monthly_budget: $1000
```

### Service-Level Costs

**LiteLLM Gateway:**
- CPU: 2-20 replicas × 500m = 1-10 cores
- Memory: 2-20 replicas × 1Gi = 2-20Gi
- Estimated: $20-200/day (varies with autoscaling)

**Overmind API:**
- CPU: 2-15 replicas × 200m = 0.4-3 cores
- Memory: 2-15 replicas × 512Mi = 1-7.5Gi
- Estimated: $10-100/day

**Overmind Bridge:**
- CPU: 0-5 replicas × 200m = 0-1 cores (scale-to-zero dev)
- Memory: 0-5 replicas × 512Mi = 0-2.5Gi
- Estimated: $0-30/day (dev only when active)

**Temporal Workers:**
- CPU: 2-10 replicas × 500m = 1-5 cores
- Memory: 2-10 replicas × 1Gi = 2-10Gi
- Estimated: $15-75/day

## Cost Queries

### API Examples

**Get today's costs by namespace:**
```bash

curl -G <http://localhost:9090/model/allocation> \
  -d window=today \
  -d aggregate=namespace \
  -d accumulate=true \
 | jq '.data[] | {name: .name, totalCost: .totalCost}'
```

**Get weekly costs by service:**

```bash
curl -G http://localhost:9090/model/allocation \
  -d window=7d \
  -d aggregate=service \
  -d filterNamespaces=overmind-prod \
 | jq '.data[] | {service: .name, cost: .totalCost, cpuCost: .cpuCost, ramCost: .ramCost}'
```

**Get cost breakdown by label:**
```bash

curl -G <http://localhost:9090/model/allocation> \
  -d window=month \
  -d aggregate=label:app \
  -d filterNamespaces=overmind-prod \
 | jq '.data[] | {app: .name, cost: .totalCost}'
```

**Get efficiency metrics:**

```bash
curl -G http://localhost:9090/model/allocation \
  -d window=7d \
  -d aggregate=deployment \
  -d filterNamespaces=overmind-prod \
 | jq '.data[] | {
      deployment: .name,
      cpuEfficiency: .cpuEfficiency,
      ramEfficiency: .ramEfficiency,
      totalCost: .totalCost
    }'
```

## Savings Recommendations

### Rightsizing

Kubecost analyzes actual resource usage and recommends optimal requests/limits:

**Example - LiteLLM Gateway:**
```yaml

# Current
resources:
  requests:
    cpu: 500m
    memory: 1Gi
  limits:
    cpu: 2000m
    memory: 4Gi

# Actual usage (p95)
cpu: 350m (70% efficiency)
memory: 750Mi (75% efficiency)

# Recommendation
resources:
  requests:
    cpu: 400m     # Savings: 20%
    memory: 800Mi # Savings: 20%
  limits:
    cpu: 1000m    # Savings: 50%
    memory: 2Gi   # Savings: 50%

# Estimated savings: $10-15/day
```

### Abandoned Workloads

Detects low-utilization resources:

```bash
# Query abandoned workloads
curl -G http://localhost:9090/model/allocation \
  -d window=7d \
  -d filterNamespaces=overmind-dev,overmind-prod \
 | jq '.data[] | select(.cpuEfficiency < 0.05) | {
      name: .name,
      cpuEfficiency: .cpuEfficiency,
      cost: .totalCost
    }'
```

### Cluster Optimization

**Node pool recommendations:**
- Right-size node types (CPU vs memory-optimized)
- Spot instance opportunities (dev environment)
- Reserved instance commitments (prod environment)

**Expected savings:**
- Dev environment: 60-80% with spot instances + scale-to-zero
- Prod environment: 30-40% with reserved instances + rightsizing

## Budget Alerts

### Daily Cost Alert

**File:** `alerts/daily-budget.yaml`

```yaml

apiVersion: v1
kind: ConfigMap
metadata:
  name: kubecost-daily-alert
  namespace: kubecost
data:
  alert.json: | 
    {
      "type": "budget",
      "threshold": 100,
      "window": "1d",
      "aggregation": "namespace",
      "filter": "overmind-prod",
      "slack": {
        "webhook": "${SLACK_WEBHOOK_URL}",
        "channel": "#overmind-alerts"
      }
    }
```

### Monthly Budget Alert

**File:** `alerts/monthly-budget.yaml`

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: kubecost-monthly-alert
  namespace: kubecost
data:
  alert.json: | 
    {
      "type": "budget",
      "threshold": 2000,
      "window": "30d",
      "aggregation": "namespace",
      "filter": "overmind-prod",
      "slack": {
        "webhook": "${SLACK_WEBHOOK_URL}",
        "channel": "#overmind-finops"
      }
    }
```

### Efficiency Alert

**File:** `alerts/efficiency.yaml`

```yaml

apiVersion: v1
kind: ConfigMap
metadata:
  name: kubecost-efficiency-alert
  namespace: kubecost
data:
  alert.json: | 
    {
      "type": "efficiency",
      "cpuEfficiencyThreshold": 0.5,
      "ramEfficiencyThreshold": 0.5,
      "window": "7d",
      "aggregation": "deployment",
      "filter": "overmind-prod",
      "slack": {
        "webhook": "${SLACK_WEBHOOK_URL}",
        "channel": "#overmind-finops"
      }
    }
```

## Grafana Dashboards

### Cost Dashboard

**File:** `dashboards/cost-overview.json`

Visualizes:

- Total daily/monthly costs
- Cost breakdown by namespace
- Cost breakdown by service
- Cost trends (7d, 30d)
- Budget vs actual

### Efficiency Dashboard

**File:** `dashboards/efficiency.json`

Visualizes:

- CPU efficiency by deployment
- Memory efficiency by deployment
- Rightsizing recommendations
- Savings opportunities

### Allocation Dashboard

**File:** `dashboards/allocation.json`

Visualizes:

- Cost per request
- Cost per user
- Cost per feature
- Cost attribution

## Reports

### Weekly Cost Report

```bash
# Generate weekly report
curl -X POST http://localhost:9090/model/reports \
  -H 'Content-Type: application/json' \
  -d '{
    "window": "7d",
    "aggregation": "namespace",
    "format": "pdf",
    "email": "team@example.com"
  }'
```

### Monthly Executive Summary

```bash

# Generate monthly summary
curl -X POST <http://localhost:9090/model/reports> \
  -H 'Content-Type: application/json' \
  -d '{
    "window": "30d",
    "aggregation": "project",
    "format": "pdf",
    "includeRecommendations": true,
    "email": "executives@example.com"
  }'
```

## Prometheus Integration

### ServiceMonitor

**File:** `monitoring/service-monitor.yaml`

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: kubecost
  namespace: kubecost
spec:
  selector:
    matchLabels:
      app: cost-analyzer
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
```

### Key Metrics

```promql

# Total cluster cost
sum(kubecost_cluster_cost_total)

# Namespace cost
sum(kubecost_namespace_cost_total{namespace="overmind-prod"})

# Pod cost
kubecost_pod_cost_total{namespace="overmind-prod", pod=~"litellm.*"}

# CPU efficiency
kubecost_cpu_efficiency{namespace="overmind-prod"}

# Memory efficiency
kubecost_memory_efficiency{namespace="overmind-prod"}

# Monthly forecast
kubecost_cost_forecast_monthly{namespace="overmind-prod"}
```

## Export Configuration

### BigQuery Export

```yaml
export:
  bigquery:
    enabled: true
    projectId: overmind-analytics
    datasetId: kubecost
    table: costs
    schedule: "0 2 * * *"  # Daily at 2am
```

### S3 Export

```yaml

export:
  s3:
    enabled: true
    bucket: overmind-cost-data
    region: us-east-1
    prefix: kubecost/
    schedule: "0 2 * * *"  # Daily at 2am
```

## Troubleshooting

### Kubecost not collecting data

```bash
# Check Prometheus connection
kubectl logs -n kubecost deployment/kubecost-cost-analyzer | grep prometheus

# Verify Prometheus targets
kubectl port-forward -n observability svc/prometheus-server 9090:9090
# Visit http://localhost:9090/targets
```

### Inaccurate costs

```bash

# Verify node labels
kubectl get nodes --show-labels

# Check pricing configuration
kubectl get cm -n kubecost kubecost-config -o yaml

# Verify cloud provider pricing
kubectl logs -n kubecost deployment/kubecost-cost-analyzer | grep pricing
```

### Missing namespace costs

```bash
# Check allocation API
curl -G http://localhost:9090/model/allocation \
  -d window=today \
  -d aggregate=namespace

# Verify namespace labels
kubectl get ns overmind-prod -o yaml
```

## Best Practices

1. **Label everything** - Use consistent labels (app, component, environment)
1. **Set budgets** - Define daily/monthly budgets per namespace
1. **Review weekly** - Check efficiency metrics and recommendations
1. **Automate rightsizing** - Use HPA/KEDA for dynamic scaling
1. **Use spot instances** - For dev/test environments (60-80% savings)
1. **Monitor trends** - Track cost changes over time
1. **Export data** - Archive to BigQuery/S3 for long-term analysis
1. **Act on alerts** - Don't ignore budget overruns

## Cost Optimization Checklist

- [ ] Enable autoscaling (HPA/KEDA) ✅ (Week 3)
- [ ] Implement scale-to-zero for dev ✅ (KEDA)
- [ ] Set resource requests/limits based on actual usage
- [ ] Use spot instances for non-critical workloads
- [ ] Configure PodDisruptionBudgets
- [ ] Enable cluster autoscaler
- [ ] Review and remove unused resources
- [ ] Use reserved instances for prod (30-40% savings)
- [ ] Optimize storage (compress, dedupe, lifecycle policies)
- [ ] Monitor network egress costs

## References

- [Kubecost Documentation](https://docs.kubecost.com/)
- [Cost Allocation Guide](https://docs.kubecost.com/allocation)
- [Savings Recommendations](https://docs.kubecost.com/savings)
- [Prometheus Integration](https://docs.kubecost.com/prometheus)

## License

MIT
