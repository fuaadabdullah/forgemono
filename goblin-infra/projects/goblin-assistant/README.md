# GoblinOS Assistant - Infra Repository

This directory serves as the canonical infrastructure repository for the GoblinOS Assistant application, consolidating all infrastructure artifacts in one location for easier management, deployment, and maintenance.

## Infrastructure Categories

### 🐳 K8s manifests / Helm charts / Kustomize
Located in `infra/` subdirectory:
- `infra/charts/` - Helm charts for various services (argo-rollouts, envoy-gateway, keda, kubecost, kyverno, litellm, nats, otel-collector, temporal-worker)
- `infra/deployments/` - Kubernetes deployment manifests (ai-router, grafana, ollama, prometheus, multi-cloud workflows)
- `infra/gitops/` - GitOps configurations
- `infra/overlays/` - Kustomize overlays for different environments

### ☁️ Terraform (Cloud Infrastructure)
Located in parent `goblin-infra/` directory:
- `../envs/` - Terraform workspace environments (dev, prod, staging)
- `../modules/` - Reusable Terraform modules

### ✈️ Fly.io / flyctl manifests
- `fly.toml` - Fly.io application configuration
- `deploy-fly.sh` - Production deployment script with Bitwarden integration
- `deploy-backend.sh` - Backend deployment automation

### 🔄 CI/CD Deploy Scripts
- `deploy-fly.sh` - Fly.io deployment with secrets management
- `deploy-backend.sh` - Backend deployment automation
- CI references in `.circleci/config.yml` (external)

### 📊 Observability Configuration
Located in `infra/observability/`:
- `prometheus/` - Prometheus configuration and rules
- `grafana/` - Grafana dashboards and datasources
- `alertmanager/` - Alert rules and routing
- `loki/` - Log aggregation configuration
- `tempo/` - Distributed tracing setup
- `otel-collector/` - OpenTelemetry collector configuration
- `datadog/` - Datadog integration manifests

### 🔐 Secrets Bootstrap Scripts
Located in `infra/secrets/`:
- Bitwarden integration scripts
- KMS helpers and key management
- Environment-specific secret configurations
- SOPS encryption configurations

## Quick Start

### Prerequisites
- Bitwarden CLI installed and authenticated
- `kubectl` configured for target cluster
- `flyctl` installed for Fly.io deployments
- Terraform CLI for infrastructure changes

### Validation
```bash
# Test Bitwarden access
./infra/secrets/test_vault.sh

# Validate Kubernetes manifests
kustomize build infra/overlays/prod | kubectl apply -f - --dry-run=client

# Check Terraform plan
cd ../envs/prod && terraform plan
```

### Deployment

#### Fly.io Deployment
```bash
./deploy-fly.sh
```

#### Kubernetes Deployment (GitOps)
```bash
kustomize build infra/overlays/prod | kubectl apply -f -
```

#### Terraform Infrastructure
```bash
cd ../envs/prod
terraform plan
terraform apply
```

## Runbook & Rollback Procedures

See `RUNBOOK.md` for detailed operational procedures including:
- Pre-deployment validation steps
- Deployment execution for different platforms
- Post-deployment verification
- Rollback strategies for Fly.io, Kubernetes, and Terraform
- Incident response and escalation procedures

## Repository Structure

```
goblin-infra/projects/goblin-assistant/
├── README.md              # This file
├── RUNBOOK.md             # Operational runbook
├── MANIFEST.md            # Detailed artifact manifest
├── CI_UPDATES.md          # CI migration checklist
├── fly.toml               # Fly.io configuration
├── deploy-fly.sh          # Fly deployment script
├── deploy-backend.sh      # Backend deployment script
├── import_infra.sh        # Infra import utility
└── infra/
    ├── charts/            # Helm charts
    ├── deployments/       # K8s manifests
    ├── gitops/            # GitOps configs
    ├── observability/     # Monitoring stack
    ├── overlays/          # Kustomize overlays
    └── secrets/           # Secrets management
```

## Migration Status

✅ **Infrastructure artifacts successfully consolidated** from `apps/goblin-assistant/infra` into this canonical location.

- All K8s manifests, Helm charts, and overlays copied
- Observability configurations migrated
- Secrets bootstrap scripts included
- Deploy scripts and Fly configurations present
- Runbook and operational documentation created

The original artifacts remain in `apps/goblin-assistant/infra` for backward compatibility during transition.

## Next Steps

1. **CI Migration**: Follow `CI_UPDATES.md` to update CircleCI and other CI references
2. **Validation**: Run smoke tests against new artifact locations
3. **Cleanup**: Remove duplicate artifacts from `apps/goblin-assistant/infra` after successful validation
4. **Documentation**: Update any external documentation referencing old paths

## Contributing

- All infrastructure changes should be made in this directory
- Update `RUNBOOK.md` when adding new deployment procedures
- Test changes in development environment before production deployment
- Follow the operational procedures in `RUNBOOK.md` for any production changes
