# 🚀 Multi-Repo Migration - Quick Start

**TLDR**: Run `bash tools/migrate-to-multirepo.sh` → Copy workflows → Configure secrets → Deploy

---

## 📦 What You Have

| File | Purpose | Status |
|------|---------|--------|
| `docs/MULTI_REPO_MIGRATION_GUIDE.md` | Full migration plan (400+ lines) | ✅ Ready |
| `tools/migrate-to-multirepo.sh` | Automated extraction script (500+ lines) | ✅ Ready |
| `docs/ci-cd-workflows/*.yml` | 8 GitHub Actions workflows | ✅ Ready |
| `docs/CI_CD_WORKFLOWS_COMPLETE.md` | CI/CD documentation | ✅ Ready |
| `docs/MIGRATION_READY_TO_EXECUTE.md` | Execution checklist | ✅ Ready |

---

## 🎯 5-Minute Quick Start

### Step 1: Run Migration Script
```bash
cd /Users/fuaadabdullah/ForgeMonorepo
bash tools/migrate-to-multirepo.sh
```

**Output**: 5 directories created in `/tmp/goblin-migration/`

### Step 2: Create GitHub Repos
```bash
gh repo create YOUR_ORG/goblin-assistant-backend --public
gh repo create YOUR_ORG/goblin-assistant-frontend --public
gh repo create YOUR_ORG/goblin-assistant-contracts --public
gh repo create YOUR_ORG/goblin-assistant-infra --public
gh repo create YOUR_ORG/goblin-assistant-dev --public
```

### Step 3: Push Code + Workflows
```bash
# For each repo in /tmp/goblin-migration/
cd /tmp/goblin-migration/goblin-assistant-backend

# Copy workflows
cp /Users/fuaadabdullah/ForgeMonorepo/docs/ci-cd-workflows/backend-*.yml .github/workflows/

# Commit and push
git add .
git commit -m "Add CI/CD workflows"
git remote add origin git@github.com:YOUR_ORG/goblin-assistant-backend.git
git push -u origin main

# Create develop branch
git checkout -b develop
git push -u origin develop
```

### Step 4: Configure Secrets (See Checklist Below)

### Step 5: Test
```bash
# Push to develop → triggers staging deployment
git push origin develop

# Watch CI/CD
gh run watch
```

---

## 🔑 Required Secrets Checklist

### Get These Before Starting:

#### Backend (goblin-assistant-backend)
- [ ] `RENDER_API_KEY` - https://dashboard.render.com/account/api-keys
- [ ] `RENDER_STAGING_SERVICE_ID` - Create Render service
- [ ] `RENDER_PRODUCTION_SERVICE_ID` - Create Render service

#### Frontend (goblin-assistant-frontend)
- [ ] `VERCEL_TOKEN` - https://vercel.com/account/tokens
- [ ] `VERCEL_ORG_ID` - Run `vercel project ls`
- [ ] `VERCEL_PROJECT_ID` - Run `vercel project ls`
- [ ] `VITE_API_URL` - Your API URL per environment
- [ ] `CHROMATIC_PROJECT_TOKEN` - https://www.chromatic.com/

#### Contracts (goblin-assistant-contracts)
- [ ] `NPM_TOKEN` - https://www.npmjs.com/settings/YOUR_USER/tokens
- [ ] `PYPI_TOKEN` - https://pypi.org/manage/account/token/

#### Infrastructure (goblin-assistant-infra)
- [ ] `AWS_ACCESS_KEY_ID` - IAM credentials
- [ ] `AWS_SECRET_ACCESS_KEY` - IAM credentials
- [ ] `KUBE_CONFIG_STAGING` - Base64 kubeconfig
- [ ] `KUBE_CONFIG_PRODUCTION` - Base64 kubeconfig

#### All Repos (Org-Level)
- [ ] `SLACK_WEBHOOK_URL` - Slack incoming webhook
- [ ] `INFRACOST_API_KEY` - https://www.infracost.io/

---

## 📋 5 Repositories You'll Create

```
1. goblin-assistant-backend      → FastAPI + PostgreSQL + Redis
2. goblin-assistant-frontend     → React + TypeScript + Vite
3. goblin-assistant-contracts    → Shared types (npm + PyPI)
4. goblin-assistant-infra        → Terraform + Kubernetes
5. goblin-assistant-dev          → Docker Compose for local dev
```

---

## 🔄 Deployment Flow

### Staging (Automatic)
```
Push to develop → CI runs → Deploy to staging
```

**URLs**:
- Backend: `https://staging-api.goblin.fuaad.ai`
- Frontend: `https://staging.goblin.fuaad.ai`

### Production (Manual Approval)
```
Merge develop → main → Tag v1.0.0 → Manual approval → Deploy
```

**URLs**:
- Backend: `https://api.goblin.fuaad.ai`
- Frontend: `https://goblin.fuaad.ai`

---

## 🎨 Visual Testing (Chromatic)

Chromatic runs automatically on PRs:
- Captures screenshots of all Storybook stories
- Compares against baseline
- Requires approval for visual changes
- Token required: `CHROMATIC_PROJECT_TOKEN`

Get token: https://www.chromatic.com/start

---

## 🐳 Local Development

```bash
cd /tmp/goblin-migration/goblin-assistant-dev
docker-compose up
```

**Services**:
- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- PostgreSQL: localhost:5432
- Redis: localhost:6379

---

## ⚡ CI/CD Workflows Overview

### Backend
- **CI**: Black, Ruff, MyPy, PyTest, Docker build, Trivy scan
- **Deploy**: Build image → Push to GHCR → Deploy to Render

### Frontend
- **CI**: ESLint, TypeScript, Vitest, Storybook, Chromatic, Lighthouse
- **Deploy**: Build with Vite → Deploy to Vercel

### Contracts
- **CI**: Lint TypeScript + Python, test both, validate sync
- **Publish**: Publish to npm + PyPI, notify dependent repos

### Infrastructure
- **CI**: Terraform validate, K8s validate, tfsec, cost estimate
- **Deploy**: Terraform apply → K8s rollout

---

## 🛡️ Security & Quality Gates

### Automated Checks
- ✅ Dependency vulnerability scanning (Dependabot)
- ✅ Code quality (ESLint, Black, Ruff)
- ✅ Type checking (TypeScript, MyPy)
- ✅ Test coverage (Codecov)
- ✅ Visual regression (Chromatic)
- ✅ Accessibility (Lighthouse CI, axe)
- ✅ Security scanning (Trivy, tfsec)

### Manual Gates
- ✅ Production deployments require approval
- ✅ Infrastructure changes require 2 approvers

---

## 📊 Success Metrics

Migration is successful when:
1. All 5 repos exist with CI/CD
2. Staging deploys automatically
3. Production requires approval
4. Health checks pass
5. Visual regression tests pass
6. Local dev works (docker-compose)
7. Contracts package publishes
8. Monitoring works (Slack notifications)

---

## 🚨 Rollback Plan

### If deployment fails:
```bash
# Backend (Render)
curl -X POST https://api.render.com/v1/services/SERVICE_ID/rollback \
  -H "Authorization: Bearer $RENDER_API_KEY"

# Frontend (Vercel)
vercel rollback https://goblin.fuaad.ai
```

### If migration fails:
- Original monorepo still exists at `/Users/fuaadabdullah/ForgeMonorepo`
- Just point DNS/endpoints back to monorepo deployment

---

## 📚 Full Documentation

| Document | Purpose |
|----------|---------|
| `MULTI_REPO_MIGRATION_GUIDE.md` | Comprehensive 8-phase plan |
| `CI_CD_WORKFLOWS_COMPLETE.md` | Full CI/CD documentation |
| `MIGRATION_READY_TO_EXECUTE.md` | Step-by-step execution guide |
| This file | Quick reference card |

---

## ⏱️ Time Estimate

| Phase | Duration |
|-------|----------|
| Run migration script | 30 min |
| Create GitHub repos | 15 min |
| Push code + workflows | 20 min |
| Configure secrets | 30 min |
| Test staging | 1 hour |
| Verify production | 1 hour |
| **Total** | **4-6 hours** |

---

## 🎯 Next Action

**Option 1: Execute Now**
```bash
bash tools/migrate-to-multirepo.sh
```

**Option 2: Review First**
Read `docs/MIGRATION_READY_TO_EXECUTE.md` for detailed checklist

**Option 3: Test Locally**
```bash
bash tools/migrate-to-multirepo.sh --dry-run
```

---

## 🆘 Need Help?

- Migration issues: See `docs/MULTI_REPO_MIGRATION_GUIDE.md`
- CI/CD issues: See `docs/CI_CD_WORKFLOWS_COMPLETE.md`
- Workflow errors: Check GitHub Actions logs
- Deployment issues: Check service-specific logs (Render/Vercel)

---

**STATUS**: ✅ Ready to execute
**CREATED**: December 2025
**NEXT**: Run migration script or read full docs

🚀 **Ready when you are!**
