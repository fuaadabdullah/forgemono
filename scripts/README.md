# Scripts Directory

This directory contains all operational scripts for the ForgeMonorepo, organized by purpose. These scripts provide flexibility and portability that CI/CD platforms can't fully replace.

## Directory Structure

```
scripts/
├── dev/                    # Local development tools
│   ├── start-dev.sh       # Start local development servers
│   └── lint_all.sh        # Run all linting checks locally
├── deploy/                # Deployment automation
│   ├── deploy-backend.sh  # Multi-platform backend deployment
│   ├── deploy-frontend.sh # Frontend deployment
│   ├── deploy-fly.sh      # Fly.io specific deployment
│   ├── deploy-vercel.sh   # Vercel deployment
│   └── deploy-render-prep.sh # Render preparation
├── ops/                   # Operational tools
│   ├── smoke.sh          # Health checks and smoke tests
│   ├── supabase_rls_check.sh # Database security audit
│   ├── sanity_checks.sh  # General sanity validation
│   └── security_check.sh # Security scanning
└── monitoring/           # Performance monitoring
    ├── benchmark_llamacpp.py    # LLM performance benchmarking
    ├── test_llamacpp_server.py # LLM server testing
    ├── test_send_llamacpp_kpi.py # KPI monitoring
    └── diagnose_terminal.sh     # Terminal diagnostics
```

## Usage Guidelines

### When to Use Scripts vs CI/CD

 | Use Case | Use Scripts | Use CI/CD | 
|----------|-------------|-----------|
 | Local development | ✅ Scripts | ❌ CI/CD | 
 | Emergency deployments | ✅ Scripts | ❌ CI/CD | 
 | Manual testing/debugging | ✅ Scripts | ❌ CI/CD | 
 | Automated PR checks | ❌ Scripts | ✅ CI/CD | 
 | Scheduled deployments | ❌ Scripts | ✅ CI/CD | 
 | Multi-environment testing | ❌ Scripts | ✅ CI/CD | 

### CI/CD Integration Pattern

CI/CD should **call these scripts** rather than duplicate logic:

```yaml
# GitHub Actions example
- name: Run Security Audit
  run: ./scripts/ops/supabase_rls_check.sh

# CircleCI example
- run:
    name: Deploy Backend
    command: ./scripts/deploy/deploy-backend.sh --platform flyio --env production
```

## Script Categories

### Development Scripts (`dev/`)

#### `start-dev.sh`
- **Purpose**: Start local development servers (backend + frontend)
- **Usage**: `./scripts/dev/start-dev.sh`
- **CI/CD**: Not used in CI/CD - local development only
- **Dependencies**: Python venv, Node.js

#### `lint_all.sh`
- **Purpose**: Run comprehensive linting across the entire repository
- **Usage**: `./scripts/dev/lint_all.sh`
- **CI/CD**: Called by GitHub Actions backend-ci workflow
- **Dependencies**: pnpm, various linting tools

### Deployment Scripts (`deploy/`)

#### `deploy-backend.sh`
- **Purpose**: Multi-platform backend deployment (Fly.io, Render)
- **Usage**: `./scripts/deploy/deploy-backend.sh --platform flyio --env production`
- **CI/CD**: Called by CircleCI production pipeline
- **Dependencies**: Platform CLIs (flyctl, render)

#### `deploy-frontend.sh`
- **Purpose**: Frontend deployment orchestration
- **Usage**: `./scripts/deploy/deploy-frontend.sh --platform vercel`
- **CI/CD**: Called by GitHub Actions frontend-deploy-vercel workflow
- **Dependencies**: Vercel CLI

### Operational Scripts (`ops/`)

#### `smoke.sh`
- **Purpose**: Health checks and smoke tests for deployed services
- **Usage**: `./scripts/ops/smoke.sh`
- **CI/CD**: Called after deployments in staging/production pipelines
- **Dependencies**: kubectl, curl

#### `supabase_rls_check.sh`
- **Purpose**: Database security audit for Row Level Security policies
- **Usage**: `./scripts/ops/supabase_rls_check.sh [supabase_dir]`
- **CI/CD**: Called by GitHub Actions terraform-security workflow
- **Dependencies**: sed, ripgrep (optional)

#### `sanity_checks.sh`
- **Purpose**: General sanity validation for the application
- **Usage**: `./scripts/ops/sanity_checks.sh`
- **CI/CD**: Called by CircleCI build-and-test-backend job
- **Dependencies**: Various application dependencies

#### `security_check.sh`
- **Purpose**: Security scanning and vulnerability checks
- **Usage**: `./scripts/ops/security_check.sh`
- **CI/CD**: Called by GitHub Actions gitleaks workflow
- **Dependencies**: Security scanning tools

### Monitoring Scripts (`monitoring/`)

#### `benchmark_llamacpp.py`
- **Purpose**: Performance benchmarking for LLM operations
- **Usage**: `python scripts/monitoring/benchmark_llamacpp.py`
- **CI/CD**: Called by scheduled performance monitoring jobs
- **Dependencies**: Python, llama.cpp

#### `test_llamacpp_server.py`
- **Purpose**: Test LLM server connectivity and basic functionality
- **Usage**: `python scripts/monitoring/test_llamacpp_server.py`
- **CI/CD**: Called by health check workflows
- **Dependencies**: Python, requests

## Development Workflow

### Local Development
```bash

# Start development servers
./scripts/dev/start-dev.sh

# Run linting before committing
./scripts/dev/lint_all.sh
```

### Pre-commit Hook Setup

```bash
# Install pre-commit hook
echo "#!/bin/bash
./scripts/dev/lint_all.sh" > .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### Emergency Operations
```bash

# Manual deployment
./scripts/deploy/deploy-backend.sh --platform flyio --env production

# Health check
./scripts/ops/smoke.sh

# Security audit
./scripts/ops/supabase_rls_check.sh
```

## CI/CD Integration Examples

### GitHub Actions Backend CI

```yaml
- name: Run Linting
  run: ./scripts/dev/lint_all.sh

- name: Security Audit
  run: ./scripts/ops/supabase_rls_check.sh
```

### CircleCI Deployment
```yaml

- run:
    name: Deploy Backend
    command: ./scripts/deploy/deploy-backend.sh --platform flyio --env $CIRCLE_TAG

- run:
    name: Health Check
    command: ./scripts/ops/smoke.sh
```

## Script Standards

### CI/CD Integration Flags

All scripts support the `--ci` flag for non-interactive CI/CD usage:

```bash
# CI/CD usage (non-interactive, structured output)
./scripts/dev/lint_all.sh --ci
./scripts/deploy/deploy-backend.sh --platform flyio --env production --ci
./scripts/ops/supabase_rls_check.sh --ci apps/goblin-assistant

# Local development usage (interactive, verbose output)
./scripts/dev/lint_all.sh
./scripts/deploy/deploy-backend.sh --platform flyio --env production
./scripts/ops/supabase_rls_check.sh apps/goblin-assistant
```

### Performance Monitoring

Scripts automatically integrate with the CI/CD performance monitoring system:

- Execution times are tracked
- Success/failure rates are monitored
- Performance reports are available via `./scripts/monitoring/monitor_ci_performance.sh --report`

### Error Handling

All scripts follow these standards:
- Exit with appropriate codes (0 = success, non-zero = failure)
- Provide clear error messages
- Support `--help` flag where applicable
- Log output to stderr for errors, stdout for normal output

### Testing Scripts
- Scripts should be testable in isolation
- Include usage examples in comments
- Test both success and failure scenarios
- Validate in CI/CD before production use

## Benefits of This Organization

✅ **Single source of truth** - No duplication between CI/CD and scripts
✅ **Local development parity** - Developers can run identical logic locally
✅ **CI/CD portability** - Scripts work with any CI/CD platform
✅ **Emergency operations** - Manual operations when CI/CD is unavailable
✅ **Comprehensive tooling** - Scripts for every operational need
✅ **Maintainable** - Clear organization and documentation

## Consolidation & housekeeping scripts

### `check-goblin-assistant-diffs.sh`
- **Purpose**: Detect potential duplicates and filename collisions between the root `goblin-assistant/` and `apps/goblin-assistant/` directories
- **Usage**: `./scripts/check-goblin-assistant-diffs.sh` — writes conflict and file lists to `/tmp/`

### `consolidate-goblin-assistant.sh`
- **Purpose**: Merge unique files from root `goblin-assistant/` into `apps/goblin-assistant/` safely using `rsync` and back up the root folder
- **Usage**: `./scripts/consolidate-goblin-assistant.sh` — runs the check script, asks for confirmation, copies files and backs up root

### `consolidate-data.sh`
- **Purpose**: Consolidate and reorganize on-disk data into `data/` folder (vector DBs, sqlite files, logs) and create backups with `.moved-<date>` suffix.
- **Usage**: `./scripts/consolidate-data.sh` — non-destructive, creates `.moved-` backups and copies

