# CI/CD Cost Avoidance Guide

This document outlines optimizations implemented to stay within free tier limits for CircleCI and GitHub Actions.

## Implemented Optimizations

### 1. Docker Layer Caching (CircleCI)

- **Location**: `goblin-infra/.circleci/config.yml` - `build-and-push-backend-image` job
- **Optimization**: Added `--cache-from` and `--build-arg BUILDKIT_INLINE_CACHE=1` to leverage previous builds
- **Impact**: Reduces build time by 60-80% for incremental changes

### 2. Visual Regression Frequency Reduction

- **Location**: `.github/workflows/visual-regression.yml`
- **Optimization**: Changed from running on every PR to only main branch pushes with path filtering
- **Impact**: ~90% reduction in Chromatic usage (expensive service)

### 3. Pre-commit Hooks

- **Location**: `.pre-commit-config.yaml`
- **Optimization**: Added local linting, formatting, and security checks
- **Tools**: Black, isort, ruff, ESLint, hadolint, detect-secrets
- **Impact**: Catches issues before CI runs, reducing failed builds

### 4. Enhanced Path Filtering

- **Location**: `.github/workflows/docker-ci.yml`
- **Optimization**: Added exclusions for docs, READMEs, and non-code files
- **Impact**: Prevents unnecessary Docker builds on documentation changes

### 5. CI Usage Monitoring

- **Location**: `.github/workflows/ci-usage-monitor.yml`
- **Optimization**: Daily monitoring with alerts at 80% usage threshold
- **Impact**: Proactive cost management and optimization triggers

### 6. Optimized Parallelization

- **Location**: `goblin-infra/.circleci/config.yml` - dev-pipeline workflow
- **Optimization**: Build/test and Terraform planning now run in parallel
- **Impact**: Faster feedback loops, better resource utilization

### 7. Script Organization & CI/CD Integration

- **Location**: `scripts/` directory with organized subdirectories
- **Optimization**: CI/CD workflows now call scripts instead of duplicating logic
- **Structure**:
  - `scripts/dev/` - Local development tools (start-dev.sh, lint_all.sh)
  - `scripts/deploy/` - Deployment automation (deploy-backend.sh, deploy-frontend.sh)
  - `scripts/ops/` - Operational tools (smoke.sh, supabase_rls_check.sh)
  - `scripts/monitoring/` - Performance monitoring scripts
- **Impact**: Single source of truth, reduced duplication, better maintainability

## Usage Monitoring

The CI usage monitor runs daily and will alert when approaching limits:

- **Warning**: 80% of monthly minutes used
- **Critical**: 90% of monthly minutes used

## Pre-commit Setup

To use pre-commit hooks locally:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run on all files
pre-commit run --all-files

# Run on staged files (automatic on commit)
pre-commit run
```

## Cost Savings Summary

| Optimization | Estimated Savings | Implementation |
|-------------|------------------|----------------|
| Docker Caching | 60-80% build time | CircleCI config |
| Visual Regression | ~90% Chromatic cost | GitHub Actions |
| Pre-commit Hooks | 30-50% failed builds | Local development |
| Path Filtering | 20-30% unnecessary runs | Workflow triggers |
| Parallel Jobs | 15-25% faster pipelines | CircleCI workflows |

## Monitoring Your Usage

### GitHub Actions
- Check: Settings → Billing & plans → GitHub Actions
- Free limit: 2,000 minutes/month
- Monitor via: `.github/workflows/ci-usage-monitor.yml`

### CircleCI
- Check: Plan → Usage
- Free limit: 6,000 credits/month (1 credit = ~1 minute)
- Monitor via: CircleCI dashboard

## Emergency Actions

If approaching limits:

1. **Disable expensive workflows temporarily**
2. **Move more checks to pre-commit hooks**
3. **Reduce test frequency on feature branches**
4. **Use path filtering more aggressively**
5. **Consider paid plans for critical projects**

## Best Practices

- Always use path filtering on workflows
- Cache dependencies and build artifacts
- Use pre-commit hooks for fast feedback
- Monitor usage regularly
- Optimize Docker builds with multi-stage builds
- Use matrix builds only when necessary
