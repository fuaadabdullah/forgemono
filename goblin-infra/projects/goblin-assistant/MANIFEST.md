# GoblinOS Assistant - Infra Manifest (Detailed)

This file lists infra artifacts and their preferred canonical locations in the infra repository.

## K8s manifests / Helm / Kustomize (source files)
- goblin-infra/projects/goblin-assistant/infra/deployments/
- goblin-infra/projects/goblin-assistant/infra/charts/
- goblin-infra/projects/goblin-assistant/infra/overlays/
- goblin-infra/projects/goblin-assistant/infra/gitops/

## Terraform (source)
- goblin-infra/envs/
- goblin-infra/modules/
- (.circleci references Terraform Cloud in .circleci/config.yml)

## Fly / flyctl
- apps/goblin-assistant/fly.toml
- apps/goblin-assistant/deploy-backend.sh (generates fly.toml dynamically)
- apps/goblin-assistant/deploy-fly.sh

## CI / deploy helpers
- apps/goblin-assistant/.circleci/config.yml
- apps/goblin-assistant/.circleci/fetch_secrets.sh
- apps/goblin-assistant/deploy-backend.sh
- apps/goblin-assistant/deploy-frontend.sh
- apps/goblin-assistant/deploy-vercel.sh
- apps/goblin-assistant/deploy-vercel-bw.sh
- goblin-infra/projects/goblin-assistant/frontend/vercel.json
- goblin-infra/projects/goblin-assistant/frontend/deploy-vercel.sh
- goblin-infra/projects/goblin-assistant/frontend/deploy-vercel-simple.sh
- goblin-infra/projects/goblin-assistant/frontend/README.md

## Observability

- goblin-infra/projects/goblin-assistant/infra/observability/ (kustomize manifests and helm renderers)
- goblin-infra/projects/goblin-assistant/infra/deployments/prometheus.yaml
- goblin-infra/projects/goblin-assistant/infra/deployments/grafana.yaml
- goblin-infra/projects/goblin-assistant/infra/observability/overlays/**

## Secrets bootstrap / helpers

- apps/goblin-assistant/scripts/setup_bitwarden.sh
- apps/goblin-assistant/scripts/test_vault.sh
- apps/goblin-assistant/scripts/load_env.sh
- apps/goblin-assistant/scripts/setup_ssh_key.sh

## Runbooks / Readmes

- apps/goblin-assistant/FLY_DEPLOYMENT.md
- apps/goblin-assistant/DEPLOYMENT_CHECKLIST.md
- apps/goblin-assistant/PRODUCTION_DEPLOYMENT.md
- apps/goblin-assistant/PRODUCTION_MONITORING.md
- apps/goblin-assistant/backend/docs/PRODUCTION_MONITORING.md  # Canonical backend docs
- goblin-infra/README.md

---

## Suggested retention policy

- Keep production manifests in `goblin-infra/projects/goblin-assistant/` and reference them in `apps/goblin-assistant/` with minimal wrappers.
- Keep per-environment overlays in `goblin-infra/projects/goblin-assistant/infra/overlays` as the canonical location.
- `apps/goblin-assistant/infra` is a symlink to the canonical location for backward compatibility.

