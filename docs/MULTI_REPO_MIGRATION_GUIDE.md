# Goblin Assistant Multi-Repo Migration Guide

## 🎯 Architecture Overview

Migrating from monorepo to multi-repo architecture with:

1. **goblin-assistant-backend** - FastAPI Python backend
2. **goblin-assistant-frontend** - React + TypeScript frontend
3. **goblin-assistant-infra** - Terraform/K8s infrastructure
4. **goblin-assistant-dev** - Local development orchestration
5. **@goblin/contracts** - Shared TypeScript/Python type definitions

## 📊 Repository Structure

```
GitHub Organization: fuaadabdullah (or create goblin-assistant org)
├── goblin-assistant-backend/
│   ├── .github/workflows/
│   │   ├── ci.yml (test + build)
│   │   └── deploy.yml (push image + deploy)
│   ├── api/
│   ├── backend/
│   ├── tests/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── README.md
│
├── goblin-assistant-frontend/
│   ├── .github/workflows/
│   │   ├── ci.yml (test + build)
│   │   └── deploy-vercel.yml
│   ├── src/
│   ├── public/
│   ├── tests/
│   ├── Dockerfile (optional)
│   ├── package.json
│   └── README.md
│
├── goblin-assistant-infra/
│   ├── terraform/
│   │   ├── backend/
│   │   ├── frontend/
│   │   └── shared/
│   ├── k8s/
│   │   ├── backend-deployment.yaml
│   │   └── frontend-deployment.yaml
│   ├── scripts/
│   │   ├── deploy-backend.sh
│   │   └── deploy-frontend.sh
│   └── README.md
│
├── goblin-assistant-dev/
│   ├── docker-compose.yml
│   ├── .env.example
│   ├── scripts/
│   │   ├── setup.sh
│   │   └── start.sh
│   └── README.md
│
└── contracts/ (npm package @goblin/contracts)
    ├── src/
    │   ├── api.ts (TypeScript)
    │   └── api.py (Python stub)
    ├── package.json
    ├── setup.py
    └── README.md
```

## 🚀 Migration Steps

### Phase 1: Repository Creation (Day 1)

#### 1.1 Create GitHub Repositories

```bash
# Create repos via GitHub CLI or web UI
gh repo create fuaadabdullah/goblin-assistant-backend --public
gh repo create fuaadabdullah/goblin-assistant-frontend --public
gh repo create fuaadabdullah/goblin-assistant-infra --public
gh repo create fuaadabdullah/goblin-assistant-dev --public
gh repo create fuaadabdullah/goblin-contracts --public
```

#### 1.2 Extract Backend Code

```bash

cd /Users/fuaadabdullah/ForgeMonorepo

# Create backend repo structure
mkdir -p ../goblin-assistant-backend
cd ../goblin-assistant-backend
git init

# Copy backend files
cp -r /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/backend/* .
cp -r /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/api .
cp /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/Dockerfile .
cp /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/requirements.txt .

# Copy tests
cp -r /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/tests ./tests

# Initial commit
git add .
git commit -m "Initial backend extraction from monorepo"
git branch -M main
git remote add origin git@github.com:fuaadabdullah/goblin-assistant-backend.git
git push -u origin main
```

#### 1.3 Extract Frontend Code

```bash
cd /Users/fuaadabdullah/ForgeMonorepo

# Create frontend repo structure
mkdir -p ../goblin-assistant-frontend
cd ../goblin-assistant-frontend
git init

# Copy frontend files
cp -r /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/src .
cp -r /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/public .
cp -r /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/.storybook .
cp /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/package.json .
cp /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/tsconfig.json .
cp /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/vite.config.ts .
cp /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/vitest.config.ts .
cp /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/index.html .

# Copy deployment configs
cp /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/vercel.json .

# Initial commit
git add .
git commit -m "Initial frontend extraction from monorepo"
git branch -M main
git remote add origin git@github.com:fuaadabdullah/goblin-assistant-frontend.git
git push -u origin main
```

#### 1.4 Create Contracts Package

```bash

mkdir -p ../goblin-contracts
cd ../goblin-contracts
git init

# Will populate with shared types (see Phase 2)
```

### Phase 2: Shared Contracts Package (Day 1-2)

See: `contracts/README.md` in this guide for detailed setup.

Key files to create:

- `package.json` - npm package config
- `src/api.ts` - TypeScript type definitions
- `src/api.py` - Python type stubs (using Pydantic)
- `.github/workflows/publish.yml` - Auto-publish on version tag

### Phase 3: Infrastructure Setup (Day 2-3)

#### 3.1 Terraform Configuration

```bash
mkdir -p ../goblin-assistant-infra
cd ../goblin-assistant-infra
git init

# Create terraform structure (see infra/README.md)
```

#### 3.2 Kubernetes Manifests

Create K8s deployments for backend/frontend (optional, can use Fly.io/Vercel instead).

### Phase 4: Local Development Orchestration (Day 2)

```bash

mkdir -p ../goblin-assistant-dev
cd ../goblin-assistant-dev
git init

# Create docker-compose.yml that references backend/frontend images

# See dev/README.md for complete setup
```

### Phase 5: CI/CD Setup (Day 3-4)

#### 5.1 Backend CI/CD

Add to `goblin-assistant-backend/.github/workflows/`:

- `ci.yml` - Run tests on PR
- `deploy.yml` - Build Docker image, push to registry, deploy to Fly.io

#### 5.2 Frontend CI/CD

Add to `goblin-assistant-frontend/.github/workflows/`:

- `ci.yml` - Run tests, Storybook build
- `deploy-vercel.yml` - Deploy to Vercel

#### 5.3 Organization Secrets

Set in GitHub org or per-repo:

- `DOCKER_USERNAME`
- `DOCKER_PASSWORD`
- `FLY_API_TOKEN`
- `VERCEL_TOKEN`
- `CHROMATIC_PROJECT_TOKEN`

### Phase 6: Dependency Management (Day 4)

#### 6.1 Backend depends on contracts

```toml
# pyproject.toml
[project]
dependencies = [
    "goblin-contracts @ git+https://github.com/fuaadabdullah/goblin-contracts.git@v1.0.0",
]
```

#### 6.2 Frontend depends on contracts

```json
{
  "dependencies": {
    "@goblin/contracts": "github:fuaadabdullah/goblin-contracts#v1.0.0"
  }
}
```

### Phase 7: Versioning Strategy (Day 5)

#### Backend API Versioning

```python
# backend/main.py
app = FastAPI(
    title="Goblin Assistant API",
    version="1.0.0",  # Semantic versioning
    description="AI-powered development assistant"
)

# v1 routes
app.include_router(v1_router, prefix="/api/v1")
```

#### Changelog Management

Use [Keep a Changelog](https://keepachangelog.com/):

- `CHANGELOG.md` in each repo
- Update on every PR merge
- Tag releases: `v1.0.0`, `v1.1.0`, etc.

### Phase 8: Cross-Repo PR Workflow (Day 5)

#### PR Template Example

```markdown
## Description

<!-- What changed and why -->

## Related PRs

<!-- Link dependent PRs in other repos -->

- Backend: fuaadabdullah/goblin-assistant-backend#42
- Frontend: fuaadabdullah/goblin-assistant-frontend#17
- Contracts: fuaadabdullah/goblin-contracts#5

## Testing

- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Deployment Checklist

- [ ] Backend deployed
- [ ] Frontend deployed
- [ ] Database migrations run
- [ ] Environment variables updated
```

## 📋 Repository-Specific Guides

### Backend Repository

See: `backend-repo-setup.md` (next section)

### Frontend Repository

See: `frontend-repo-setup.md` (next section)

### Infrastructure Repository

See: `infra-repo-setup.md` (next section)

### Dev Repository

See: `dev-repo-setup.md` (next section)

### Contracts Package

See: `contracts-repo-setup.md` (next section)

## 🔄 Migration Timeline

| Phase                  | Duration | Tasks                                            |
| ---------------------- | -------- | ------------------------------------------------ |
| 1. Repository Creation | 4 hours  | Extract code, create repos, initial commits      |
| 2. Contracts Package   | 4 hours  | Define shared types, setup npm package           |
| 3. Infrastructure      | 8 hours  | Terraform configs, K8s manifests, deploy scripts |
| 4. Local Dev           | 4 hours  | Docker Compose, dev scripts                      |
| 5. CI/CD               | 8 hours  | GitHub Actions for all repos                     |
| 6. Dependencies        | 2 hours  | Update imports, install contracts package        |
| 7. Versioning          | 2 hours  | Changelogs, tagging strategy                     |
| 8. PR Workflow         | 2 hours  | Templates, branch protection                     |

**Total**: ~5 days for complete migration

## ⚠️ Migration Risks & Mitigation

### Risk 1: Breaking Changes During Migration

**Mitigation**:

- Keep monorepo running in parallel
- Use feature flags
- Gradual traffic shift (canary deployment)

### Risk 2: Dependency Hell

**Mitigation**:

- Pin exact versions in contracts package
- Use lockfiles (`package-lock.json`, `poetry.lock`)
- Test compatibility in CI

### Risk 3: Secret Management

**Mitigation**:

- Use GitHub org-level secrets
- Rotate all secrets during migration
- Document secret requirements in each repo

### Risk 4: Database Migrations

**Mitigation**:

- Run migrations before code deployment
- Use Alembic for versioned migrations
- Test rollback procedures

## 📝 Post-Migration Checklist

- [ ] All repos have CI/CD pipelines
- [ ] Contracts package published and installed
- [ ] Local dev environment works (docker-compose)
- [ ] Production deployments successful
- [ ] Documentation updated
- [ ] Team trained on new workflow
- [ ] Old monorepo archived (keep as backup for 3 months)

## 🚦 Go/No-Go Decision Points

Before migrating:

1. ✅ Backend tests pass in new repo
2. ✅ Frontend builds successfully
3. ✅ Docker images build and run
4. ✅ CI pipelines green
5. ✅ Team alignment on workflow

## 📚 Additional Resources

- [GitHub Actions Docs](https://docs.github.com/actions)
- [Docker Multi-Stage Builds](https://docs.docker.com/build/building/multi-stage/)
- [Semantic Versioning](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)

---

**Next**: See individual repo setup guides below.
