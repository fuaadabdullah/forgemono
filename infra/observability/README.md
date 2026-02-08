---
description: "README"
---

Observability manifests
======================

This folder contains kustomize-based manifests for a production-ready observability stack used by GoblinOS.

Components included (minimal, production-ready starting point):

- OpenTelemetry Collector (receiver/processor/exporter pipelines)
- Grafana (visualization)
- Loki (log store)
- Tempo (trace store)

Security & assumptions
----------------------

- Assumes an Ingress controller is present (e.g., nginx-ingress).
- TLS is handled via cert-manager; examples are provided but cert-manager installation is required.

How to use
----------

1. Review and adapt image tags, storage classes, and resource sizes to your cluster.
1. Use `kustomize build infra/observability | kubectl apply -f -` to deploy.
1. Use `.github/workflows/observability-lint.yml` to lint manifests in CI.

This folder is intentionally conservative. It provides a reproducible, linted baseline.
