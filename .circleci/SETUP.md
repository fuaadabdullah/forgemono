# CircleCI Setup Guide for ForgeMonorepo

## Quick Start

### 1. Create CircleCI Account & Link Repo

1. Go to [circleci.com](https://circleci.com) and sign up with GitHub
2. Click "Set Up Project" for `fuaadabdullah/forgemono`
3. Select "Use existing config" (we have `.circleci/config.yml`)
4. Click "Start Building"

### 2. Create Contexts (Organization-Level Secrets)

Go to **Organization Settings → Contexts** and create:

#### Context: `terraform-cloud`
| Variable | Description | Where to get it |
|----------|-------------|-----------------|
| `TF_TOKEN` | Terraform Cloud API token | [app.terraform.io/app/settings/tokens](https://app.terraform.io/app/settings/tokens) |

#### Context: `docker-ghcr`
| Variable | Description | Where to get it |
|----------|-------------|-----------------|
| `GHCR_USER` | Your GitHub username | `fuaadabdullah` |
| `GHCR_TOKEN` | GitHub PAT with `write:packages` scope | [github.com/settings/tokens](https://github.com/settings/tokens) |

### 3. Required GitHub PAT Scopes

Create a PAT at [github.com/settings/tokens/new](https://github.com/settings/tokens/new):

- ✅ `write:packages` (push to GHCR)
- ✅ `read:packages` (pull from GHCR)
- ✅ `delete:packages` (optional, for cleanup)

### 4. Terraform Cloud Setup

Your HCP Terraform Cloud should already be configured:

- **Organization**: `GoblinOS`
- **Workspaces**:
  - `GoblinOSAssistant` (dev)
  - `GoblinOSAssistant-staging` (staging)
  - `GoblinOSAssistant-prod` (prod)

Ensure the TF_TOKEN has access to these workspaces.

---

## Pipeline Overview

### CI Pipeline (Every Push/PR)
```
backend-lint-test
       ↓
terraform-security-scan
       ↓
   ┌───┴───┐
   ↓       ↓       ↓
plan-dev  plan-staging  plan-prod
```

### Deploy Pipeline (Merge to main)
```
backend-lint-test → docker-build-push
                          ↓
                   security-scan
                          ↓
                    plan-dev → apply-dev (AUTO)
                          ↓
              ┌───────────┴───────────┐
              ↓                       ↓
       plan-staging              plan-prod
              ↓                       ↓
       [MANUAL HOLD]           [MANUAL HOLD]
              ↓                       ↓
       apply-staging             apply-prod
```

### Nightly Security (3 AM UTC)
```
terraform-security-scan (tfsec + checkov)
```

---

## How Manual Approvals Work

1. Pipeline runs plans for staging/prod
2. Hits `hold-staging-approval` or `hold-prod-approval`
3. You get an email or see it in CircleCI dashboard
4. Click "Approve" in CircleCI UI to continue
5. Apply runs automatically after approval

---

## Secrets Checklist

| Secret | Context | Required | Notes |
|--------|---------|----------|-------|
| `TF_TOKEN` | `terraform-cloud` | ✅ Yes | Terraform Cloud API token |
| `GHCR_USER` | `docker-ghcr` | ✅ Yes | GitHub username |
| `GHCR_TOKEN` | `docker-ghcr` | ✅ Yes | GitHub PAT with packages scope |

---

## Branch Protection (GitHub)

Set up in **GitHub → Settings → Branches → main**:

- ✅ Require status checks to pass before merging
- ✅ Require branches to be up to date before merging
- ✅ Status checks:
  - `ci-pipeline/backend-lint-test`
  - `ci-pipeline/terraform-security-scan`

---

## Cost Optimization Tips

1. **Use caching**: Pip dependencies are cached to save build time
2. **Monitor credits**: Free tier = ~6,000 credits/month
3. **Self-hosted runners**: For heavy Docker builds, consider [CircleCI runner](https://circleci.com/docs/runner-overview/)
4. **Parallelism**: Plans run in parallel to save time

---

## Troubleshooting

### "Context not found"

- Create the context in Organization Settings
- Ensure the context name matches exactly (`terraform-cloud`, `docker-ghcr`)

### "Terraform init failed"

- Check `TF_TOKEN` is set correctly
- Ensure Terraform Cloud workspaces exist

### "Docker push failed"

- Verify `GHCR_TOKEN` has `write:packages` scope
- Check `GHCR_USER` is correct (case-sensitive)

### "Tests failing"

- Check `apps/goblin-assistant/tests/` for broken tests
- Tests run with `--tb=short` for concise output

---

## File Structure

```
ForgeMonorepo/
├── .circleci/
│   └── config.yml          # CircleCI pipeline config
├── apps/
│   └── goblin-assistant/
│       ├── Dockerfile      # Docker build
│       └── backend/
│           └── requirements.txt
└── goblin-infra/
    ├── envs/
    │   ├── dev/
    │   ├── staging/
    │   └── prod/
    └── scripts/
        ├── staging_smoke_tests.sh
        └── prod_smoke_tests.sh
```

---

## Adding Harness Later (Optional)

If you want advanced deployment verification:

1. Keep CircleCI as CI (build/test/push)
2. Add Harness as CD (deploy with canary/rollback)
3. Wire Harness to pull artifacts from GHCR
4. Use Harness CV for automatic rollback on errors

This hybrid gives you low-maintenance CI + sophisticated CD.

---

## Quick Commands

```bash
# Validate CircleCI config locally
circleci config validate

# Trigger pipeline manually
circleci pipeline trigger --branch main

# Check pipeline status
circleci workflow list --pipeline-id <id>
```

---

**Last Updated**: December 3, 2025
