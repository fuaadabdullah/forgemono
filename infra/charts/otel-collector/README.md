---
description: "README"
---

# OpenTelemetry Collector Helm Chart

This chart deploys the GoblinOS OpenTelemetry data plane:

- **DaemonSet agents** on every node receiving OTLP traffic from workloads and forwarding to the central collector
- **Central collector deployment** that performs batching/tail sampling and exports to Tempo, Loki, Prometheus, and audit sinks
- **Secure OTLP** via mTLS (SPIFFE-compatible certificates) with optional API-key fallback for legacy workloads

## Quick Start

```bash
cd infra/charts/otel-collector
helm upgrade --install otel-collector . \
  --namespace observability \
  --create-namespace \
  -f values.yaml
```

### Prereqs

1. TLS secret containing CA + leaf cert (`security.mtls.secretName`)
1. Optional API key secret (`security.apiKey.secretName`) with key specified via `security.apiKey.secretKey`
1. Tempo, Loki, and Prometheus endpoints reachable inside the cluster

### Configuration Highlights

 | Value | Description | 
 | --- | --- | 
 | `daemonset.config` | ConfigMap content for node agents (default enables OTLP -> upstream) | 
 | `deployment.config` | Central collector pipeline (tail sampling, exporters) | 
 | `security.mtls.*` | Enables TLS certificates for OTLP listeners | 
 | `security.apiKey.*` | Header injection for agents forwarding to central collector | 

For advanced scenarios create environment-specific values files (e.g., `values.staging.yaml`) that override exporter endpoints or sampling policies.
