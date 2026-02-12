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
1. "Reopen in Container" when prompted
1. Use VS Code tasks for service startup/testing

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

1. **Simplified Monitoring**:
   - Sentry: Error tracking and crash reporting
   - Vercel Analytics: Frontend performance metrics
   - Fly.io Metrics: Backend performance metrics (built-in)

### Setup Instructions

1. Ensure Kubernetes cluster is running (e.g., via Minikube, AKS, GKE).
1. Apply the manifests:

   ```bash
   kubectl apply -f deployments/
   ```
1. Configure endpoints:
   - Replace `<azure-endpoint-url>` and `<gcp-endpoint-url>` in `ollama-k8s.yaml` with actual URLs.
1. Access services:
   - Sentry: Configure in app settings
   - Vercel Analytics: Available in Vercel dashboard
   - Fly.io Metrics: Available in Fly.io dashboard

### Simplified Monitoring

Error tracking and performance monitoring is now handled by integrated platform services:

- **Frontend**: Vercel Analytics for performance metrics
- **Backend**: Fly.io built-in metrics and logs
- **Errors**: Sentry for crash reporting and error tracking

No complex Kubernetes monitoring stack required for current scale.

## Usage

Start the development stack:

```bash

docker-compose up -d
```
