---
description: "Observability Stack for Goblin Assistant"
---

Observability manifests
======================

This folder contains kustomize-based manifests for a production-ready observability stack used by GoblinOS.

Components included (minimal, production-ready starting point):

- OpenTelemetry Collector (receiver/processor/exporter pipelines)
- Grafana (visualization)
- Loki (log store)
- Tempo (trace store)
- **Datadog Agent** (process monitoring, APM, metrics)

## Datadog Process Monitoring

The `datadog/` directory contains a complete setup for Datadog process monitoring with I/O stats.

### Quick Start

```bash
cd datadog
sudo ./setup-datadog-processes.sh
```

See [Datadog Quick Reference](./datadog/QUICKSTART.md) or [Full Documentation](./datadog/README.md).

### Features

- ✅ Process discovery and metrics (CPU, memory, I/O)
- ✅ Sensitive argument scrubbing
- ✅ Optimized collection (runs in core agent)
- ✅ Container-aware monitoring
- ✅ APM integration

### Deployment Options

- **Linux Host**: `setup-datadog-processes.sh`
- **Docker**: `docker-compose-datadog.yml`
- **Kubernetes**: `k8s-datadog-agent.yaml` or Helm chart

Security & assumptions
----------------------

- Assumes an Ingress controller is present (e.g., nginx-ingress).
- TLS is handled via cert-manager; examples are provided but cert-manager installation is required.
- Datadog Agent requires elevated privileges for system-probe (I/O stats).

How to use
----------

1. Review and adapt image tags, storage classes, and resource sizes to your cluster.
2. Use `kustomize build infra/observability | kubectl apply -f -` to deploy.
3. Use `.github/workflows/observability-lint.yml` to lint manifests in CI.

This folder is intentionally conservative. It provides a reproducible, linted baseline.
