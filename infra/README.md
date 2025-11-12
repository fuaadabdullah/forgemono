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

## Usage

Start the development stack:

```bash
docker-compose up -d
```
