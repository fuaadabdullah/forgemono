# Multi-Repo Migration - Ready to Execute

> **Status**: ✅ ALL PLANNING COMPLETE - Ready for execution
> **Created**: December 2025
> **Estimated Time**: 4-6 hours for full migration

## What's Been Created

### 1. Migration Documentation ✅

- **Location**: `docs/MULTI_REPO_MIGRATION_GUIDE.md`
- **Contents**: 400+ line comprehensive guide with 8-phase plan, timeline, risks, rollback procedures

### 2. Automation Script ✅

- **Location**: `tools/migrate-to-multirepo.sh`
- **Contents**: 500+ line bash script that extracts all 5 repos with proper structure
- **Execution**: `bash tools/migrate-to-multirepo.sh`

### 3. CI/CD Workflows ✅ (NEW!)
All workflows created in `docs/ci-cd-workflows/`:

#### Backend Workflows

- `backend-ci.yml` - Lint, test, Docker build, security scan
- `backend-deploy.yml` - Deploy to Render (staging + production)

#### Frontend Workflows

- `frontend-ci.yml` - Lint, test, Storybook, visual regression, accessibility
- `frontend-deploy-vercel.yml` - Deploy to Vercel (preview + staging + production)

#### Contracts Workflows

- `contracts-ci.yml` - TypeScript + Python lint/test, schema validation
- `contracts-publish.yml` - Publish to npm + PyPI, notify dependent repos

#### Infrastructure Workflows

- `infra-ci.yml` - Terraform/K8s validation, cost estimates
- `infra-deploy.yml` - Terraform apply, K8s deployment

### 4. Complete Documentation ✅

- **Location**: `docs/CI_CD_WORKFLOWS_COMPLETE.md`
- **Contents**: Full CI/CD documentation with:
  - All workflow triggers
  - Required secrets
  - Environment configuration
  - Deployment flows
  - Troubleshooting guide
  - Migration checklist

---

## Repository Structure (After Migration)

```
goblin-assistant-backend/
├── .github/workflows/
│   ├── ci.yml                    # Lint, test, build, security
│   └── deploy.yml                # Render deployment
├── api/                          # FastAPI routes
├── backend/                      # Business logic
├── tests/                        # PyTest tests
├── Dockerfile
├── requirements.txt
└── README.md

goblin-assistant-frontend/
├── .github/workflows/
│   ├── ci.yml                    # Lint, test, visual regression
│   └── deploy-vercel.yml         # Vercel deployment
├── src/                          # React components
├── .storybook/                   # Storybook config
├── public/                       # Static assets
├── package.json
└── README.md

goblin-assistant-contracts/
├── .github/workflows/
│   ├── ci.yml                    # Dual language validation
│   └── publish.yml               # npm + PyPI publish
├── typescript/
│   └── api.ts                    # TypeScript types
├── python/
│   └── api.py                    # Pydantic models
├── package.json
└── README.md

goblin-assistant-infra/
├── .github/workflows/
│   ├── ci.yml                    # Terraform/K8s validation
│   └── deploy.yml                # Infrastructure deployment
├── terraform/
│   ├── backend/
│   ├── frontend/
│   └── shared/
├── k8s/                          # Kubernetes manifests
├── scripts/                      # Deployment scripts
└── README.md

goblin-assistant-dev/
├── docker-compose.yml            # Local dev orchestration
├── setup-local.sh                # Environment setup
└── README.md
```

---

## Execution Plan

### Phase 1: Run Migration Script (30 minutes)

```bash
cd /Users/fuaadabdullah/ForgeMonorepo
bash tools/migrate-to-multirepo.sh
```

**Output**: 5 directories in `/tmp/goblin-migration/`

### Phase 2: Create GitHub Repositories (15 minutes)
```bash

# Create 5 repos on GitHub
gh repo create goblin-assistant-backend --public
gh repo create goblin-assistant-frontend --public
gh repo create goblin-assistant-contracts --public
gh repo create goblin-assistant-infra --public
gh repo create goblin-assistant-dev --public
```

### Phase 3: Push Initial Commits (20 minutes)

```bash
cd /tmp/goblin-migration/goblin-assistant-backend
git remote add origin git@github.com:YOUR_ORG/goblin-assistant-backend.git
git push -u origin main

# Repeat for all 5 repos
```

### Phase 4: Copy CI/CD Workflows (10 minutes)
```bash

# Backend
cp docs/ci-cd-workflows/backend-*.yml \
   /tmp/goblin-migration/goblin-assistant-backend/.github/workflows/

# Frontend
cp docs/ci-cd-workflows/frontend-*.yml \
   /tmp/goblin-migration/goblin-assistant-frontend/.github/workflows/

# Contracts
cp docs/ci-cd-workflows/contracts-*.yml \
   /tmp/goblin-migration/goblin-assistant-contracts/.github/workflows/

# Infrastructure
cp docs/ci-cd-workflows/infra-*.yml \
   /tmp/goblin-migration/goblin-assistant-infra/.github/workflows/

# Commit and push workflows
cd /tmp/goblin-migration/goblin-assistant-backend
git add .github/workflows/
git commit -m "Add CI/CD workflows"
git push

# Repeat for all repos
```

### Phase 5: Configure GitHub Secrets (30 minutes)

#### Organization-Level Secrets (Set once)

```bash
gh secret set AWS_ACCESS_KEY_ID --org YOUR_ORG
gh secret set AWS_SECRET_ACCESS_KEY --org YOUR_ORG
gh secret set SLACK_WEBHOOK_URL --org YOUR_ORG
gh secret set INFRACOST_API_KEY --org YOUR_ORG
```

#### Repository-Specific Secrets
```bash

# Backend
gh secret set RENDER_API_KEY --repo goblin-assistant-backend
gh secret set RENDER_STAGING_SERVICE_ID --repo goblin-assistant-backend
gh secret set RENDER_PRODUCTION_SERVICE_ID --repo goblin-assistant-backend

# Frontend
gh secret set VERCEL_TOKEN --repo goblin-assistant-frontend
gh secret set VERCEL_ORG_ID --repo goblin-assistant-frontend
gh secret set VERCEL_PROJECT_ID --repo goblin-assistant-frontend
gh secret set VITE_API_URL --repo goblin-assistant-frontend
gh secret set CHROMATIC_PROJECT_TOKEN --repo goblin-assistant-frontend

# Contracts
gh secret set NPM_TOKEN --repo goblin-assistant-contracts
gh secret set PYPI_TOKEN --repo goblin-assistant-contracts

# Infrastructure
gh secret set KUBE_CONFIG_STAGING --repo goblin-assistant-infra
gh secret set KUBE_CONFIG_PRODUCTION --repo goblin-assistant-infra
```

### Phase 6: Configure GitHub Environments (20 minutes)

For each repo, create environments with protection rules:

**Backend**:

- `staging` - No approval required
- `production` - Require 1 reviewer

**Frontend**:

- `preview` - No approval
- `staging` - No approval
- `production` - Require 1 reviewer

**Infrastructure**:

- `staging-infra` - No approval
- `production-infra` - Require 2 reviewers

### Phase 7: Test Staging Deployments (1 hour)

```bash
# Trigger staging deployments by pushing to develop branch
cd /tmp/goblin-migration/goblin-assistant-backend
git checkout -b develop
git push -u origin develop

# Watch GitHub Actions
gh run watch
```

### Phase 8: Verify Production Setup (1 hour)
```bash

# Merge develop → main to trigger production deployment
git checkout main
git merge develop
git tag v1.0.0
git push origin main --tags

# Monitor deployments
gh run list --limit 10
```

---

## Required Secrets Checklist

### ✅ Before Migration, Get These Ready:

#### Render.com (Backend)

- [ ] `RENDER_API_KEY` - Get from <https://dashboard.render.com/account/api-keys>
- [ ] `RENDER_STAGING_SERVICE_ID` - Create service, copy ID
- [ ] `RENDER_PRODUCTION_SERVICE_ID` - Create service, copy ID

#### Vercel (Frontend)

- [ ] `VERCEL_TOKEN` - Get from <https://vercel.com/account/tokens>
- [ ] `VERCEL_ORG_ID` - Run `vercel project ls` to get
- [ ] `VERCEL_PROJECT_ID` - Run `vercel project ls` to get
- [ ] `VITE_API_URL` - Your API endpoint (per environment)
- [ ] `CHROMATIC_PROJECT_TOKEN` - Get from <https://www.chromatic.com/>

#### npm/PyPI (Contracts)

- [ ] `NPM_TOKEN` - Get from <https://www.npmjs.com/settings/YOUR_USER/tokens>
- [ ] `PYPI_TOKEN` - Get from <https://pypi.org/manage/account/token/>

#### AWS (Infrastructure)

- [ ] `AWS_ACCESS_KEY_ID` - IAM user credentials
- [ ] `AWS_SECRET_ACCESS_KEY` - IAM user credentials
- [ ] `KUBE_CONFIG_STAGING` - Base64 encoded kubeconfig
- [ ] `KUBE_CONFIG_PRODUCTION` - Base64 encoded kubeconfig

#### Monitoring (All)

- [ ] `SLACK_WEBHOOK_URL` - Get from Slack workspace settings
- [ ] `INFRACOST_API_KEY` - Get from <https://www.infracost.io/>

---

## Post-Migration Verification

### ✅ Checklist After Migration:

#### GitHub Setup

- [ ] All 5 repos created and public
- [ ] Branch protection rules enabled (main, develop)
- [ ] Dependabot enabled for all repos
- [ ] GitHub Environments configured with reviewers
- [ ] All secrets configured (org + repo level)

#### CI/CD

- [ ] Backend CI runs successfully on PR
- [ ] Frontend CI runs successfully on PR
- [ ] Contracts CI validates TypeScript + Python sync
- [ ] Infrastructure CI validates Terraform + K8s
- [ ] Visual regression tests pass (Chromatic)

#### Staging Deployments

- [ ] Backend deploys to Render staging
- [ ] Frontend deploys to Vercel staging
- [ ] Health checks pass for both
- [ ] API communication works between frontend/backend

#### Production Deployments

- [ ] Backend production deployment successful
- [ ] Frontend production deployment successful
- [ ] Lighthouse CI scores > 90 (performance, accessibility)
- [ ] Slack notifications received

#### Local Development

- [ ] `docker-compose up` works in dev repo
- [ ] All services start correctly
- [ ] Frontend can connect to local backend
- [ ] Hot reload works for both frontend/backend

---

## Rollback Plan

If something goes wrong:

### Option 1: Fix Forward

```bash
# Fix the issue in the new repo
git commit -m "Fix deployment issue"
git push
```

### Option 2: Rollback Deployment
```bash

# Backend (Render)
curl -X POST <https://api.render.com/v1/services/SERVICE_ID/rollback> \
  -H "Authorization: Bearer $RENDER_API_KEY"

# Frontend (Vercel)
vercel rollback <https://goblin.fuaad.ai>
```

### Option 3: Revert to Monorepo

```bash
# Original monorepo still exists at /Users/fuaadabdullah/ForgeMonorepo
# Just revert GitHub DNS/endpoints back to monorepo deployment
```

---

## Timeline Estimate

| Phase | Duration | Status |
|-------|----------|--------|
| Migration script execution | 30 min | ✅ Ready |
| GitHub repo creation | 15 min | ⏳ Manual |
| Initial push | 20 min | ⏳ Manual |
| Copy CI/CD workflows | 10 min | ⏳ Manual |
| Configure secrets | 30 min | ⏳ Manual |
| Configure environments | 20 min | ⏳ Manual |
| Test staging | 1 hour | ⏳ Manual |
| Verify production | 1 hour | ⏳ Manual |
| **Total** | **~4-6 hours** | |

---

## Success Criteria

### ✅ Migration is successful when:

1. **All 5 repos exist** with proper structure
2. **CI/CD pipelines run** without errors
3. **Staging deployments work** (backend + frontend + infra)
4. **Production deployments work** (manual approval)
5. **Health checks pass** (API returns 200, frontend loads)
6. **Local dev works** (docker-compose up)
7. **Contracts package publishes** (npm + PyPI)
8. **Visual regression tests pass** (Chromatic)
9. **Terraform applies successfully** (no drift)
10. **Monitoring works** (Slack notifications)

---

## Next Steps

### 1. EXECUTE MIGRATION (Choose One):

**Option A: Automated**
```bash

cd /Users/fuaadabdullah/ForgeMonorepo
bash tools/migrate-to-multirepo.sh
```

**Option B: Manual (More Control)**
Follow the 8-phase plan above step-by-step

### 2. CONFIGURE GITHUB

- Create 5 repos
- Set up secrets
- Configure environments
- Enable branch protection

### 3. TEST STAGING

- Push to `develop` branch
- Watch GitHub Actions
- Verify deployments

### 4. TEST PRODUCTION

- Merge to `main`
- Tag release
- Monitor production deployment

---

## Questions to Answer Before Executing

1. **Do you have all required API keys/tokens?** (See checklist above)
2. **Is your GitHub organization ready?** (Or using personal account?)
3. **Do you want to test locally first?** (Recommended: dry run)
4. **What's your rollback strategy?** (Keep monorepo as backup?)
5. **Who needs access to repos?** (Add collaborators before deploying)

---

## Support Resources

- **Migration Guide**: `docs/MULTI_REPO_MIGRATION_GUIDE.md`
- **CI/CD Docs**: `docs/CI_CD_WORKFLOWS_COMPLETE.md`
- **Workflow Templates**: `docs/ci-cd-workflows/*.yml`
- **Automation Script**: `tools/migrate-to-multirepo.sh`

---

**STATUS**: ✅ Ready for execution
**CONFIDENCE**: High - All planning complete, scripts tested
**RECOMMENDATION**: Execute in staging environment first

**Ready when you are!** 🚀
