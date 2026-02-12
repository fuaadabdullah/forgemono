---
description: "unified-telemetry-plan"
---

# Unified Telemetry Plan (observability)

This document outlines the GoblinOS unified telemetry approach and points to deployable artifacts (manifests, TLS examples, CI linting, and verification helpers).

## Production-grade observability stack (implementation)

The repository now includes a small, production-ready baseline for observability under `infra/observability`:

- OpenTelemetry Collector (receives OTLP, forwards traces to Tempo and logs to Loki)
- Grafana (visualization)
- Loki (log store)
- Tempo (trace store)

Files and locations:

- `infra/observability/kustomization.yaml` — top-level kustomize that assembles the stack
- `infra/observability/otel-collector/` — otel collector ConfigMap, Deployment, Service
- `infra/observability/loki/` — Loki config and Deployment
- `infra/observability/tempo/` — Tempo config and Deployment
- `infra/observability/grafana/` — Grafana Deployment and service
- `infra/observability/kube-linter.yaml` — kube-linter rules used by CI
- `infra/observability/cert-manager/` — cert-manager Certificate and Ingress example for TLS
- `.github/workflows/observability-lint.yml` — CI lint workflow that runs kustomize, kubeval, and kube-linter
- `tools/observability/verify_deploy.sh` — quick verification script to assert deployments and perform a basic Grafana probe

### TLS and hardening

Production deployments must enable TLS via `cert-manager` and an Ingress controller. Example resources are provided in `infra/observability/cert-manager/` but require a ClusterIssuer (e.g. Let's Encrypt) and cert-manager to be installed in the cluster.

Recommended hardening steps (applied at deploy time):

- Replace default Grafana secret and set a secure admin password via ExternalSecret or sealed secret.
- Configure network policies to restrict access to observability services.
- Use ingress with TLS and optional authentication (OAuth, OIDC) for Grafana.
- Replace the simple in-memory or local storage configs with production backends (S3, GCS, object-store, long-term indexers) and persistent volumes.

### Local testing with MinIO

For developer testing you can run a local S3-compatible MinIO instance included in `infra/observability/minio/`. A kustomize overlay `infra/observability/overlays/local` is provided and will:

- Deploy MinIO (dev mode, `emptyDir` storage) and a creds Secret placeholder
- Patch Loki and Tempo to use MinIO credentials and endpoint

To run locally against MinIO:

```bash
# create base manifests + minio via kustomize overlay
kustomize build infra/observability/overlays/local | kubectl apply -f -

# after resources are created, run the verification script
tools/observability/verify_deploy.sh
```

Replace the example MinIO secret values with real base64-encoded credentials or configure `external-secrets` to populate them.

### ExternalSecrets / Vault

This repo includes example `SecretStore` and `ExternalSecret` manifests under `infra/observability/external-secrets/` showing how to populate the `grafana-admin` Kubernetes Secret from Vault (or AWS). They are examples — you must configure a running ExternalSecrets controller and the backing provider (Vault server or AWS Secrets Manager) before they will populate secrets.

High-level steps to wire Vault (example):

1. Install ExternalSecrets controller in your cluster.
2. Create a `SecretStore` that points to your Vault server and provides auth (token or Kubernetes auth). Example: `infra/observability/external-secrets/secretstore.yaml`.
3. Store the Grafana admin password at `secret/data/grafana` (or your chosen path) in Vault.
4. Apply `infra/observability/external-secrets/grafana-external-secret.yaml` which will create the `grafana-admin` secret in the `observability` namespace.

If you'd like I can create a step-by-step Vault bootstrap manifest (Kubernetes auth role, ServiceAccount to mint tokens, and a short script to seed the secret) tailored for your Vault setup.

#### Vault bootstrap helper (optional)

To help bootstrap Vault for local testing, this repo includes a helper script:

- `infra/observability/external-secrets/observability-policy.hcl` — Vault policy granting read access to observability secrets.
- `infra/observability/external-secrets/bootstrap_vault.sh` — script that writes the policy, seeds example secrets (grafana, loki, tempo), creates a Vault token bound to the policy, and writes a Kubernetes secret `vault-token` into the `observability` namespace. The ExternalSecrets `SecretStore` example references this secret for token-based auth.

If you prefer Kubernetes auth (recommended for production), use the helper `infra/observability/external-secrets/bootstrap_vault_k8s.sh` which:

- Creates a short-lived token reviewer ServiceAccount (`vault-auth`) in `kube-system` and binds it to `system:auth-delegator`.
- Enables and configures the Vault Kubernetes auth method using your kubeconfig (auto-discovers API server and CA).
- Writes the `observability-policy` and creates a Vault role `external-secrets-role` bound to the `external-secrets` ServiceAccount in the `observability` namespace.

The repo includes a `SecretStore` configured for Kubernetes auth at `infra/observability/external-secrets/secretstore-kubernetes.yaml` and a `bootstrap_vault_k8s.sh` script to configure Vault.

Usage (example):

```bash

# requires vault CLI + kubectl
export VAULT_ADDR=<https://vault.example.com>
export VAULT_TOKEN=<root-or-admin-token>
cd infra/observability/external-secrets
./bootstrap_vault.sh
```

Notes:

- The script seeds example values — change them in production and rotate tokens.
- This approach uses token auth (creates a Vault token and stores it as a K8s secret). If you prefer Kubernetes auth (recommended for production), I can provide a variant that configures `auth/kubernetes` and an appropriate ServiceAccount binding instead.

### CI linting and verification

We added a GitHub Actions workflow `.github/workflows/observability-lint.yml` that:

- Builds the kustomize manifests
- Runs `kubeval` against the generated YAML
- Runs `kube-linter` with rules in `infra/observability/kube-linter.yaml`

For post-deploy verification, use `tools/observability/verify_deploy.sh` (requires `kubectl` and cluster access) which waits for deployments and performs a short Grafana HTTP probe.

### How to deploy (quick)

1. Ensure your cluster has an Ingress controller and cert-manager installed and a ClusterIssuer configured.
2. Review and adapt image tags, storage classes, resource sizes, and domain names in `infra/observability`.
3. Deploy with kustomize:

```bash
kustomize build infra/observability | kubectl apply -f -
```

4. Run the verification script after resources are created:

```bash

tools/observability/verify_deploy.sh
```

### Notes / Next steps

- Integrate secrets management (ExternalSecrets / Vault) for Grafana admin credentials.
- Add Prometheus for metrics scraping and retention rules (left intentionally out of the minimal baseline).
- Add Terraform/Multi-cluster manifests if you need to deploy across environments.

If you need me to: 1) wire Prometheus and Alertmanager, 2) add persistent storage backends, or 3) generate Helm charts instead of kustomize, tell me which and I'll implement those next.
