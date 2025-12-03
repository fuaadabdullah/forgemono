---title: Infrastructure
type: reference
project: ForgeMonorepo
status: draft
owner: GoblinOS
description: "README"

---

Devcontainer, Docker Compose, reverse proxy, and Kubernetes configurations.

> NOTE: This directory contains the working infra manifests for the GoblinOS Assistant app. The canonical infra repository is `goblin-infra/projects/goblin-assistant/` which consolidates K8s manifests, Helm charts, Terraform environments, CI helpers, observability configs, and runbooks. Use that directory as the single source of truth for infra operations.

## Dev Container

This directory contains the VS Code Dev Container specification for the ForgeMonorepo workspace.

- Provides reproducible development for backend (FastAPI), frontend (React/TypeScript), and GoblinOS agent services.
- Integrates with Docker Compose for multi-service orchestration.
- Bootstrap steps (see devcontainer.json):
	- `bash tools/lint_all.sh` for linting
	- `pnpm install --recursive` for Node dependencies
	- `pip install -r ForgeTM/apps/backend/requirements.txt` for Python dependencies

To use:
1. Open workspace in VS Code
2. "Reopen in Container" when prompted
3. Use VS Code tasks for service startup/testing

See `../docs/WORKSPACE_OVERVIEW.md` and `../docs/API_KEYS_MANAGEMENT.md` for architecture and secrets setup.

## Architecture Summary (Edge → K8s → Providers)

This repository hosts a hybrid infra stack designed for low-latency LLM inference with strong security and observability.

- Edge (Cloudflare Workers): Caching, bot filtering (Turnstile), lightweight model gateway, KV cache & D1 database for session/feature flags, and Zero Trust for admin endpoints.
- Kubernetes (K8s): Ollama inference cluster and backend services (FastAPI) with HPA and autoscaling using custom and resource metrics (CPU/memory). Services may be deployed to GKE/AKS/ECS as well.
- Observability: Prometheus, Grafana, Loki, Tempo, and Datadog are installed to capture metrics, logs, and traces. Edge and backend systems publish metrics for centralized dashboards.
- GitOps: Argo CD and SOPS for encrypted secrets (KSOPS), overlay-driven environment configs (dev/prod), and automated deployments triggered by Git.

### Critical Infra Components

- `infra/cloudflare/worker.js` (and variants) - Edge model gateway, Turnstile integration, KV and D1 access, and rate limiting.
- `infra/deployments/ollama-k8s.yaml` - Ollama deployment manifest with HPA and metrics sidecar.
- `infra/observability/` - Prometheus/Grafana/Loki/Tempo setup and deployments.
- `infra/gitops/` - Argo CD application sets and KSOPS integration for secrets.
- `infra/secrets` - SOPS age-backed encrypted secrets for dev/staging/prod.

### Known Gaps and Recommended Improvements

1. Secrets handling: Confirm that no secrets are embedded in config or tags that will be stored in Git or in wrangler.toml. Use SOPS + ArgoCD for encrypting secrets and verify age key rotation.
2. Rate Limiting: The in-memory rate limiter at the backend should be migrated to a Redis-backed distributed rate limiter to support horizontal scaling and multiple replicas across Kubernetes.
3. Backups & DR: Ensure PostgreSQL backups and D1 snapshot procedures exist and are tested; add explicit runbooks for restore actions.
4. Circuit breakers: Add provider circuit breakers and fast fallback policies to avoid cascading failures during provider outages.
5. Observability: Set SLOs and retention policies in Prometheus/Grafana and add synthetic tests for the LLM endpoints.

### Where to find things

- Worker code: `infra/cloudflare/`.
- Kubernetes manifests: `infra/deployments/` and `infra/charts/`.
- Observability: `infra/observability/`.
- GitOps: `infra/gitops/`.
- Encrypted secrets: `infra/secrets/` (SOPS with age)


## Contents

- `.devcontainer/` - VS Code devcontainer setup
- `docker-compose.yml` - Local development stack
- `k8s/` - Kubernetes manifests
- `nginx/` - Reverse proxy configuration

## Kubernetes Deployments

This directory contains Kubernetes manifests for deploying GoblinOS components, including AI-driven services.

### AI Model Integration

For decentralized processing with orchestration:

1. **Ollama Inference Layer**: Local AI model inference integrated with Azure/GCP-hosted models.
   - Deployment: `deployments/ollama-k8s.yaml`
   - Namespace: `goblinos-ai`
   - Replicas: 3 for distributed processing

2. **Telemetry Monitoring**:
   - Prometheus: `deployments/prometheus.yaml` - Metrics collection
   - Grafana: `deployments/grafana.yaml` - Visualization dashboards
   - AI Router: `deployments/ai-router.yaml` - Routing policies with embedded telemetry

### Setup Instructions

1. Ensure Kubernetes cluster is running (e.g., via Minikube, AKS, GKE).
2. Apply the manifests:
   ```bash
   kubectl apply -f deployments/
   ```
3. Configure endpoints:
   - Replace `<azure-endpoint-url>` and `<gcp-endpoint-url>` in `ollama-k8s.yaml` with actual URLs.
4. Access services:
   - Prometheus: `kubectl port-forward svc/prometheus-service 9090:9090`
   - Grafana: `kubectl port-forward svc/grafana-service 3000:3000` (default login: admin/admin)
   - AI Router: Via Ingress at `ai.goblinos.local`

### Routing Policies

The AI Router handles request distribution:
- Routes to Ollama for local inference
- Fallback to Azure/GCP for cloud-based models
- Telemetry embedded via Prometheus annotations and Pushgateway integration

## Usage

Start the development stack:

```bash
docker-compose up -d
```
