# CI/CD Workflows - Complete Documentation

> **Status**: ✅ All workflow templates created and ready for multi-repo migration
> **Created**: December 2025
> **Last Updated**: December 2025

## Overview

This document provides comprehensive documentation for all GitHub Actions workflows across the 5 Goblin Assistant repositories. Each repo has independent CI/CD pipelines with environment-specific deployments.

## Repository Workflows

### 1. Backend Repository (`goblin-assistant-backend`)

#### CI Workflow (`.github/workflows/ci.yml`)
**Triggers**: Push to `main`/`develop`, PRs
**Jobs**:
- **lint**: Black, Ruff, MyPy code quality checks
- **test**: PyTest with PostgreSQL + Redis services, codecov integration
- **build**: Docker image build with BuildKit cache
- **security**: Trivy vulnerability scanning, SARIF upload to GitHub Security

**Dependencies**:
- Python 3.11
- PostgreSQL 15 (test database)
- Redis 7 (cache service)
- Docker for containerization

#### Deploy Workflow (`.github/workflows/deploy.yml`)
**Triggers**: Push to `main`, tags `v*`, manual dispatch
**Jobs**:
- **build-and-push**: Docker build → GitHub Container Registry (ghcr.io), SBOM generation
- **deploy-staging**: Render API deployment (staging environment)
- **deploy-production**: Render API deployment (production environment)
- **create-release**: GitHub release with changelog on version tags

**Environments**:
- Staging: `https://staging-api.goblin.fuaad.ai`
- Production: `https://api.goblin.fuaad.ai`

**Required Secrets**:
- `RENDER_API_KEY`: Render.com API authentication
- `RENDER_STAGING_SERVICE_ID`: Staging service identifier
- `RENDER_PRODUCTION_SERVICE_ID`: Production service identifier
- `SLACK_WEBHOOK_URL`: Deployment notifications

---

### 2. Frontend Repository (`goblin-assistant-frontend`)

#### CI Workflow (`.github/workflows/ci.yml`)
**Triggers**: Push to `main`/`develop`, PRs
**Jobs**:
- **lint**: ESLint + TypeScript type checking
- **test**: Vitest unit tests with coverage
- **storybook**: Build Storybook static site
- **visual-regression**: Chromatic visual testing (PRs only)
- **build**: Vite production build with artifacts
- **accessibility**: Lighthouse CI for WCAG compliance
- **security**: npm audit for vulnerable dependencies

**Dependencies**:
- Node.js 20
- npm 10
- Chromatic for visual regression

#### Deploy Workflow (`.github/workflows/deploy-vercel.yml`)
**Triggers**: Push to `main`/`develop`, PRs, manual dispatch
**Jobs**:
- **deploy-preview**: Vercel preview deployments for PRs with comment bot
- **deploy-staging**: Vercel deployment to staging environment
- **deploy-production**: Vercel production deployment with Lighthouse CI

**Environments**:
- Preview: Dynamic URLs per PR
- Staging: `https://staging.goblin.fuaad.ai`
- Production: `https://goblin.fuaad.ai`

**Required Secrets**:
- `VERCEL_TOKEN`: Vercel CLI authentication
- `VERCEL_ORG_ID`: Organization identifier
- `VERCEL_PROJECT_ID`: Project identifier
- `VITE_API_URL`: Backend API endpoint (per environment)
- `CHROMATIC_PROJECT_TOKEN`: Visual regression testing
- `SLACK_WEBHOOK_URL`: Deployment notifications

---

### 3. Contracts Repository (`goblin-assistant-contracts`)

#### CI Workflow (`.github/workflows/ci.yml`)
**Triggers**: Push to `main`/`develop`, PRs
**Jobs**:
- **lint-typescript**: ESLint + TypeScript type checking
- **lint-python**: Black, Ruff, MyPy validation
- **test**: Vitest (TS) + PyTest (Python) with codecov
- **build**: TypeScript compilation with dist artifacts
- **schema-validation**: Cross-language schema synchronization check

**Purpose**: Ensure TypeScript and Python types stay in sync

#### Publish Workflow (`.github/workflows/publish.yml`)
**Triggers**: Tags `v*`, manual dispatch
**Jobs**:
- **publish-npm**: Build → test → publish to npm registry
- **publish-pypi**: Build Python package → publish to PyPI
- **notify**: Create GitHub Issues in dependent repos (`backend`, `frontend`)

**Packages**:
- npm: `@goblin/contracts` (TypeScript types)
- PyPI: `goblin-contracts` (Python Pydantic models)

**Required Secrets**:
- `NPM_TOKEN`: npm registry authentication
- `PYPI_TOKEN`: PyPI upload authentication

**Versioning**: Semantic versioning (major.minor.patch)

---

### 4. Infrastructure Repository (`goblin-assistant-infra`)

#### CI Workflow (`.github/workflows/ci.yml`)
**Triggers**: Push to `main`/`develop`, PRs
**Jobs**:
- **terraform-lint**: Format check, init, validate (backend/frontend/shared)
- **terraform-security**: tfsec vulnerability scanning
- **kubernetes-lint**: kubeval + kube-score validation
- **docker-lint**: hadolint Dockerfile linting
- **scripts-test**: shellcheck for bash scripts
- **cost-estimate**: Infracost PR comments for cloud spend

**Tools**:
- Terraform 1.6.0
- kubeval, kube-score
- tfsec, hadolint
- Infracost

#### Deploy Workflow (`.github/workflows/deploy.yml`)
**Triggers**: Push to `main` (terraform/** or k8s/**), manual dispatch
**Jobs**:
- **terraform-plan**: Generate plans for all components (staging + production)
- **terraform-apply-staging**: Apply shared → backend → frontend (sequential)
- **kubernetes-deploy-staging**: Apply K8s manifests, wait for rollout
- **terraform-apply-production**: Production infrastructure (manual approval)
- **kubernetes-deploy-production**: Production K8s deployment with smoke tests

**Environments**:
- Staging: Auto-deploy on `main` push
- Production: Manual approval required

**Required Secrets**:
- `AWS_ACCESS_KEY_ID`: AWS authentication
- `AWS_SECRET_ACCESS_KEY`: AWS authentication
- `KUBE_CONFIG_STAGING`: Kubernetes cluster config (staging)
- `KUBE_CONFIG_PRODUCTION`: Kubernetes cluster config (production)
- `INFRACOST_API_KEY`: Cost estimation service
- `SLACK_WEBHOOK_URL`: Deployment notifications

---

### 5. Dev Orchestration Repository (`goblin-assistant-dev`)

**No CI/CD workflows** - This repo contains:
- `docker-compose.yml` for local development
- Setup scripts (`setup-*.sh`)
- Local environment documentation

**Purpose**: Single command to spin up entire stack locally

---

## Cross-Repo Workflow Dependencies

### Contracts Package Updates

When `goblin-assistant-contracts` publishes a new version:

1. **GitHub Issues Created** in `backend` and `frontend` repos
2. **Labels Applied**: `dependencies`, `contracts-update`
3. **Manual Action Required**: Update `package.json` / `requirements.txt`

### Example Dependency Update Workflow:

```bash
# Backend
pip install goblin-contracts==1.2.3
pip freeze > requirements.txt

# Frontend
npm install @goblin/contracts@1.2.3
```

---

## Environment Configuration

### Staging Environment
- **Backend**: `https://staging-api.goblin.fuaad.ai` (Render)
- **Frontend**: `https://staging.goblin.fuaad.ai` (Vercel)
- **Auto-deploy**: On push to `develop` branch
- **Database**: PostgreSQL (Render managed)
- **Cache**: Redis (Render managed)

### Production Environment
- **Backend**: `https://api.goblin.fuaad.ai` (Render)
- **Frontend**: `https://goblin.fuaad.ai` (Vercel)
- **Deploy**: Manual approval required (GitHub Environments)
- **Database**: PostgreSQL (AWS RDS via Terraform)
- **Cache**: Redis (AWS ElastiCache via Terraform)
- **K8s**: AWS EKS cluster

---

## Security Best Practices

### Secrets Management
- ✅ All secrets stored in GitHub Secrets (org-level or repo-level)
- ✅ No secrets in code or logs
- ✅ Rotate secrets every 90 days
- ✅ Use GitHub Environments for approval gates

### Vulnerability Scanning
- **Backend**: Trivy (Docker images), Dependabot (Python)
- **Frontend**: npm audit, Dependabot (npm)
- **Infrastructure**: tfsec (Terraform), hadolint (Dockerfiles)

### Access Control
- **GitHub Environments**: Require reviewers for production
- **AWS IAM**: Least privilege policies
- **Kubernetes RBAC**: Service accounts per component

---

## Monitoring & Observability

### Deployment Notifications
- ✅ Slack webhook for production deployments
- ✅ GitHub PR comments for preview URLs
- ✅ GitHub Issues for contracts updates

### Health Checks
- Backend: `/health` endpoint (200 OK check)
- Frontend: Lighthouse CI (performance, accessibility)
- Infrastructure: Kubernetes rollout status

### Coverage Tracking
- Backend: Codecov (`backend` flag)
- Frontend: Codecov (`frontend` flag)
- Contracts: Codecov (`contracts` flag)

---

## Workflow Files Summary

| Repository | Workflow File | Purpose | Trigger |
|------------|---------------|---------|---------|
| `backend` | `ci.yml` | Lint, test, build, security | Push, PR |
| `backend` | `deploy.yml` | Docker build, Render deploy | Push to `main`, tags |
| `frontend` | `ci.yml` | Lint, test, Storybook, visual regression | Push, PR |
| `frontend` | `deploy-vercel.yml` | Vercel deployments | Push, PR |
| `contracts` | `ci.yml` | Lint, test, schema validation | Push, PR |
| `contracts` | `publish.yml` | npm/PyPI publish | Tags `v*` |
| `infra` | `ci.yml` | Terraform/K8s validation, cost estimate | Push, PR |
| `infra` | `deploy.yml` | Terraform apply, K8s deploy | Push to `main`, manual |

---

## Setup Checklist

Before running workflows, configure these secrets in GitHub:

### Organization-Level Secrets (Recommended)
```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
SLACK_WEBHOOK_URL
INFRACOST_API_KEY
```

### Backend Repo Secrets
```
RENDER_API_KEY
RENDER_STAGING_SERVICE_ID
RENDER_PRODUCTION_SERVICE_ID
```

### Frontend Repo Secrets
```
VERCEL_TOKEN
VERCEL_ORG_ID
VERCEL_PROJECT_ID
VITE_API_URL (per environment)
CHROMATIC_PROJECT_TOKEN
```

### Contracts Repo Secrets
```
NPM_TOKEN
PYPI_TOKEN
```

### Infrastructure Repo Secrets
```
KUBE_CONFIG_STAGING
KUBE_CONFIG_PRODUCTION
```

---

## Testing Workflows Locally

### Backend
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Build Docker image
docker build -t goblin-backend:test .
```

### Frontend
```bash
# Install dependencies
npm ci

# Run tests
npm run test:run

# Build Storybook
npm run build-storybook

# Build app
npm run build
```

### Contracts
```bash
# TypeScript
npm ci
npm run test
npm run build

# Python
pip install -r requirements-dev.txt
pytest python/tests/ -v
```

### Infrastructure
```bash
# Terraform validation
cd terraform/backend
terraform init -backend=false
terraform validate

# Kubernetes validation
kubeval k8s/*.yaml
```

---

## Deployment Flow

### Feature Development
```
1. Create branch from `develop`
2. Make changes, commit
3. Open PR → triggers CI workflows
4. Chromatic visual review (frontend)
5. Codecov coverage checks
6. PR approved → merge to `develop`
7. Auto-deploy to staging
```

### Production Release
```
1. Merge `develop` → `main`
2. Create tag: `git tag v1.2.3`
3. Push tag: `git push origin v1.2.3`
4. Backend: Docker build → Render deploy → health check
5. Frontend: Vercel production deploy → Lighthouse CI
6. Infrastructure: Manual approval → Terraform apply → K8s rollout
7. GitHub Release created with changelog
8. Slack notification sent
```

### Hotfix
```
1. Branch from `main`
2. Fix issue, commit
3. Open PR → CI checks
4. Emergency approval (skip staging)
5. Merge → tag → production deploy
```

---

## Troubleshooting

### Common Issues

**Docker build fails:**
```bash
# Check BuildKit cache
docker buildx prune -f

# Rebuild without cache
docker build --no-cache -t image:tag .
```

**Terraform apply fails:**
```bash
# Check state lock
terraform force-unlock LOCK_ID

# Re-init
terraform init -reconfigure
```

**Vercel deployment fails:**
```bash
# Check build logs
vercel logs <deployment-url>

# Verify env vars
vercel env ls
```

**Kubernetes rollout stuck:**
```bash
# Check pod status
kubectl get pods -n goblin-assistant

# View logs
kubectl logs -f deployment/backend -n goblin-assistant

# Rollback
kubectl rollout undo deployment/backend -n goblin-assistant
```

---

## Migration Checklist

After running `tools/migrate-to-multirepo.sh`:

- [ ] Create GitHub repos (5 repos)
- [ ] Push initial commits
- [ ] Configure branch protection rules
- [ ] Set up GitHub Environments (staging, production)
- [ ] Add all required secrets
- [ ] Configure Vercel project
- [ ] Configure Render services
- [ ] Set up AWS credentials
- [ ] Enable Dependabot
- [ ] Configure Codecov integrations
- [ ] Test staging deployments
- [ ] Test production deployments (with approval)
- [ ] Verify health checks
- [ ] Set up monitoring dashboards

---

## Next Steps

1. **Execute Migration**: `bash tools/migrate-to-multirepo.sh`
2. **Configure Secrets**: Add all required secrets to GitHub
3. **First Deploy**: Test staging deployment pipeline
4. **Verify**: Run smoke tests on all services
5. **Document**: Update team wiki with new workflow

---

**Author**: GoblinOS Migration Team
**Last Updated**: December 2025
**Migration Status**: ✅ Ready for execution
