---title: Infrastructure
type: reference
project: ForgeMonorepo
status: draft
owner: GoblinOS
description: "README"

---

Devcontainer, Docker Compose, reverse proxy, and Kubernetes configurations.

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
