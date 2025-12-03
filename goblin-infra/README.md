# goblin-infra

Dev/staging/production infrastructure for goblin-assistant. This repository manages the deployment and scaling infrastructure for the GoblinOS Assistant application, which consists of backend API, frontend UI, database layer, and monitoring components. See CI/CD in `.circleci/` and workflows in `.github/workflows/` and modules in `modules/`.

## Projects

This repo contains project-specific infra under `projects/`. For GoblinOS Assistant, see `projects/goblin-assistant/` for the consolidated infra README, MANIFEST, runbooks, and helpers.

## CI/CD

This repo uses **CircleCI** for continuous integration and deployment. See [.circleci/README.md](.circleci/README.md) for full documentation.

**Quick Start:**
```bash
# Run interactive setup
./.circleci/setup.sh

# View quick reference
cat .circleci/QUICKREF.md
```

**CircleCI Org ID:** `86f0d600-175c-41cf-bf68-3855b72f7645`

> **Security Note:**
>
> Set your `TF_CLOUD_TOKEN` (Terraform Cloud API token) securely in your `.env` file (see `.circleci/.env.example`) and as a secret in CircleCI project settings. **Never commit real secrets to version control.**

## Repo Layout

```text
goblin-infra/
├─ modules/
│  └─ example_resource/
│     ├─ main.tf
│     ├─ outputs.tf
│     └─ variables.tf
├─ envs/
│  ├─ dev/
│  │  ├─ main.tf
│  │  ├─ backend.tf
│  │  ├─ variables.tf
│  │  └─ outputs.tf
│  ├─ staging/
│  │  ├─ main.tf
│  │  ├─ backend.tf
│  │  ├─ variables.tf
│  │  └─ outputs.tf
│  └─ prod/
│     ├─ main.tf
│     ├─ backend.tf
│     ├─ variables.tf
│     └─ outputs.tf
├─ scripts/
│  ├─ staging_smoke_tests.sh
│  └─ prod_smoke_tests.sh
├─ .github/
│  └─ workflows/
│     ├─ terraform-plan.yml          # dev plan on PR
│     ├─ terraform-apply-dev.yml     # dev auto-apply on merge
│     ├─ terraform-plan-staging.yml  # staging plan on PR
│     ├─ terraform-apply-staging.yml # staging manual apply
│     ├─ terraform-plan-prod.yml     # prod plan on PR
│     └─ terraform-apply-prod.yml    # prod manual apply (protected)
└─ README.md
```

## Environments

| Environment | Workspace | Apply Mode | Approvers | Smoke Tests |
|-------------|-----------|------------|-----------|-------------|
| **dev** | `GoblinOSAssistant` | Auto on merge | None | Optional |
| **staging** | `GoblinOSAssistant-staging` | Manual (workflow_dispatch) | 1 required | Yes |
| **prod** | `GoblinOSAssistant-prod` | Manual (workflow_dispatch) | 2+ required | Yes |

## Backend (HCP Terraform Cloud)

All environments use HCP Terraform Cloud:

```hcl
terraform {
  cloud {
    organization = "GoblinOS"
    workspaces {
      name = "GoblinOSAssistant-<env>"  # dev, staging, prod
    }
  }
}
```

## Local Commands

```bash
cd envs/<env>  # dev, staging, or prod

terraform init
terraform fmt -check
terraform validate
terraform plan -out=tfplan

# For dev only (auto-apply allowed):
terraform apply tfplan

# For staging/prod: use GitHub Actions workflow_dispatch with approvals
```

## GitHub Environment Protection

### Staging (`staging` environment)
- Require 1 approver from infra team
- Store staging-specific secrets in environment

### Production (`production` environment)
- Require 2+ approvers from infra/ops team
- Limit who can approve/run the workflow
- Store PROD_* secrets only in the environment
- Optionally require signed commits

## Safety & Governance

### Dev
- Auto-apply on merge to main
- Tag resources with `env = dev`

### Staging
- Manual apply only (workflow_dispatch)
- Require 1 approver
- Run smoke tests after apply
- Prod-like config but smaller resources

### Prod (Sacred)
- **Separate cloud account/project** when possible
- **Manual apply only** (workflow_dispatch)
- **Require 2+ approvers**
- Pre-apply checks: plan + cost estimate + policy
- Post-apply smoke + integration checks
- Documented rollback paths
- Multi-AZ, HA, encryption, backups enabled
- Least-privilege IAM with OIDC (no long-lived keys)

## Rollback & Recovery

1. **Terraform rollback**: Re-apply prior commit/tag (last-known-good plan)
2. **State backup**: Use Terraform Cloud run history
3. **DB rollback**: Restore from snapshot to isolated instance, test, then swap
4. **Blue/Green**: Deploy to new resources, shift traffic after green checks pass
5. **Emergency kill switch**: Cut traffic to maintenance page, scale down, failover

## Checklist Before Prod Apply

- [ ] Remote state configured and isolated
- [ ] IAM role configured; CI OIDC trust set up
- [ ] GitHub `production` environment with required approvers
- [ ] `terraform plan` validated and cost estimate reviewed
- [ ] Policy checks (security & compliance) passed
- [ ] DB backups/snapshots exist and tested
- [ ] Monitoring & alerts configured
- [ ] Runbook & rollback steps documented
- [ ] Post-deploy smoke tests ready
- [ ] All changes reviewed by infra owners

## Troubleshooting

- **Init fails**: Check backend config, workspace name, credentials
- **Plan shows unexpected destroy**: Confirm state file path/workspace
- **Actions fails on permissions**: Add `id-token: write` for OIDC
- **Locking errors**: Ensure no other apply in progress
- **Smoke tests fail**: Check DNS propagation, security groups, health endpoints
