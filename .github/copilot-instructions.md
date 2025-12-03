---
description: ForgeMonorepo development guidelines and AI assistant instructions
applyTo: "**"
---

# ForgeMonorepo — AI Assistant Instructions

## Project Overview

**ForgeMonorepo** is a unified development workspace for multiple products and tools managed by GoblinOS automation. Current active projects:

1. **GoblinOS Assistant** (goblin-assistant demo) - AI assistant for development automation

### Infrastructure

#### Cloudflare Edge (goblin-assistant)

All Goblin Assistant services are protected and accelerated by Cloudflare:

**Location**: `apps/goblin-assistant/infra/cloudflare/`

**Production URLs**:

- **Frontend**: <https://goblin.fuaad.ai>
- **Backend API**: <https://api.goblin.fuaad.ai>
- **Brain (LLM Gateway)**: <https://brain.goblin.fuaad.ai>
- **Ops (Admin)**: <https://ops.goblin.fuaad.ai> (Zero Trust protected)
- **Worker (dev)**: <https://goblin-assistant-edge.fuaadabdullah.workers.dev>

**Components**:

- **Edge Workers**: Serverless logic with intelligent LLM routing
  - **Turnstile Bot Protection** - Blocks bot spam, saves ~$70/day
  - **Model Gateway** - Local-first routing (Ollama/llama.cpp → Groq → OpenAI/Anthropic)
  - Rate limiting (100 req/60s per IP)
  - Prompt sanitization (blocks jailbreaks)
  - Session validation (edge-level auth)
  - Response caching (5min TTL)
  - Analytics logging
  - Feature flags
- **KV Storage**: Distributed memory (namespace: `9e1c27d3eda84c759383cb2ac0b15e4c`)
  - Rate limit buckets, sessions, conversation context, cache
- **D1 Database**: SQLite at edge (db: `goblin-assistant-db`)
  - User preferences, audit logs, feature flags, API usage
  - Inference logs (provider, model, cost, latency tracking)
  - Provider health monitoring
- **Cloudflare Tunnel**: Secure backend access (tunnel: `9c780bd1-ac63-4d6c-afb1-787a2867e5dd`)
- **Zero Trust Access**: Identity-based protection (group: `1eac441b-55ad-4be9-9259-573675e2d993`)
  - Goblin Admins group: `Fuaadabdullah@gmail.com`
  - Protects `ops.goblin.fuaad.ai` admin panel
- **Turnstile**: Bot verification for API protection
  - Managed widget: `0x4AAAAAACEUKA3R8flZ2Ig0` (login/signup forms)
  - Invisible widget: `0x4AAAAAACEUKak3TnCntrFv` (API calls)
  - Protected endpoints: `/api/chat`, `/api/inference`, `/api/auth/*`
- **R2 Storage**: Cheap object storage (86% cheaper than S3!)
  - `goblin-audio` - Audio files (TTS, recordings) - 100GB
  - `goblin-logs` - Application logs - 50GB
  - `goblin-uploads` - User files - 500GB
  - `goblin-training` - Model artifacts - 2TB
  - `goblin-cache` - LLM response cache - 200GB
  - **Free egress** (S3 charges $90/TB!)
  - **Cost savings**: $279/month vs S3 ($42.75 vs $322)
- **Analytics Engine**: Free observability (fallback for Datadog)
  - Latency insights (p50, p95, p99 by endpoint)
  - Error maps (4xx/5xx rates, failure patterns)
  - Geographic heatmaps (user distribution, datacenter performance)
  - Cache hit ratios (KV, R2, edge cache effectiveness)
  - LLM performance (provider latency, token usage, model comparison)
  - **Free tier**: 10M data points/month (then $0.25 per 1M)
  - **Cost savings**: $50-200/month vs Datadog

**Documentation**: See `apps/goblin-assistant/infra/cloudflare/README.md` for complete setup and operations guide.

**Key Commands**:

```bash
# Deploy Worker
cd apps/goblin-assistant/infra/cloudflare && wrangler deploy

# Query D1
wrangler d1 execute goblin-assistant-db --remote --command "SELECT * FROM feature_flags"

# Start Tunnel
cloudflared tunnel --config tunnel-config.yml run

# Setup Turnstile
./setup_turnstile.sh

# View Turnstile Dashboard
open https://dash.cloudflare.com/a9c52e892f7361bab3bfd084c6ffaccb/turnstile

# Setup R2 Buckets
./setup_r2_buckets.sh

# Deploy with R2
wrangler deploy
```

## Development Guidelines

### General ForgeMonorepo Standards

#### File Organization

- `/apps` - Application projects (Python tools)
- `/tools` - Bash scripts for automation
- `/GoblinOS` - Automation framework and guild config
- `/docs` - Monorepo documentation
- `/infra` - Infrastructure as code

### GoblinOS Guilds & Goblins

This roster is auto-generated from `GoblinOS/goblins.yaml`. Update the YAML and run `cd GoblinOS && node scripts/generate-roles.js` to refresh both this block and the full breakdown in `GoblinOS/docs/ROLES.md`.

<!-- GUILD_SUMMARY_START -->

### Crafters

- **Charter:** UI systems, theme tokens, a11y, CLS/LCP budgets; APIs, schemas, queues, idempotency, error budgets.
- **Toolbelt owners:** `portfolio-dev` (vanta-lumin), `portfolio-build` (vanta-lumin), `repo-bootstrap` (vanta-lumin), `workspace-health` (vanta-lumin), `forge-smithy` (vanta-lumin), `overmind` (volt-furnace)
- **Goblins:**
  - **Glyph Scribe (`vanta-lumin`)** — UI systems and component architecture; Theme tokens and design system management. KPIs: `cls`, `lcp`, `a11y_score`. Tools: `portfolio-dev`, `portfolio-build`, `repo-bootstrap`, `workspace-health`, `forge-smithy`, `overmind`. Selection triggers: # "bootstrap forge lite repo" → forge-lite-bootstrap, # "setup forge lite environment" → forge-lite-bootstrap, # "initialize forge lite project" → forge-lite-bootstrap, "bootstrap repository" → repo-bootstrap, "setup development environment" → repo-bootstrap, "check workspace health" → workspace-health, "run health checks" → workspace-health, "setup python environment" → forge-smithy, "python development tooling" → forge-smithy, "start portfolio dev server" → portfolio-dev, "build portfolio" → portfolio-build, # "start forge lite UI development" → forge-lite-dev, # "test UI components" → forge-lite-dev, # "check telemetry integration" → forge-lite-telemetry-check, "update documentation" → mages-guild-docs-update.
  - **Socketwright (`volt-furnace`)** — API design and implementation; Schema management and validation. KPIs: `p99_latency`, `error_rate`, `schema_drift`. Tools: # `forge-lite-api-dev`, # `forge-lite-db-migrate`, # `forge-lite-rls-check`, # `forge-lite-auth-login`, # `forge-lite-market-data-fetch`, # `forge-lite-export-data`, `overmind`. Selection triggers: # "start API server" → forge-lite-api-dev, # "test API endpoints" → forge-lite-api-dev, # "debug backend logic" → forge-lite-api-dev, # "run db migrations" → forge-lite-db-migrate, # "check rls policies" → forge-lite-rls-check, # "auth login" → forge-lite-auth-login, # "fetch market data" → forge-lite-market-data-fetch, # "export user data" → forge-lite-export-data, "AI trading assistance" → overmind, "LLM routing" → overmind.

### Huntress

- **Charter:** Flaky test hunts, regression triage, incident tagging; early-signal scouting, log mining, trend surfacing.
- **Toolbelt owners:** `huntress-guild-analyze-tests` (magnolia-nightbloom), `huntress-guild-triage-regression` (magnolia-nightbloom), `huntress-guild-scout-signals` (magnolia-nightbloom), `huntress-guild-report-incidents` (magnolia-nightbloom)
- **Goblins:**
  - **Vermin Huntress (`magnolia-nightbloom`)** — Flaky test identification and remediation; Regression triage and root cause analysis. KPIs: `flaky_rate`, `mttr_test_failures`. Tools: `huntress-guild-analyze-tests`, `huntress-guild-triage-regression`, `huntress-guild-scout-signals`, `huntress-guild-report-incidents`. Selection triggers: "analyze tests" → huntress-guild-analyze-tests, "identify flaky tests" → huntress-guild-analyze-tests, "triage regression" → huntress-guild-triage-regression, "regression check" → huntress-guild-triage-regression, "scout signals" → huntress-guild-scout-signals, "analyze logs" → huntress-guild-scout-signals, "report incidents" → huntress-guild-report-incidents, "analyze bug reports" → huntress-guild-report-incidents.
  - **Omenfinder (`mags-charietto`)** — Early-signal detection and alerting; Log mining and pattern recognition. KPIs: `valid_early_signals`, `false_positive_rate`. Tools: Brain workflows only. Selection triggers: "analyze logs" → Brain only (Uses brain for log analysis, no external tools).

### Keepers

- **Charter:** Secrets, licenses, SBOM, signatures, backups, attestations.
- **Toolbelt owners:** `keepers-guild-secrets-audit` (sentenial-ledgerwarden), `keepers-guild-security-scan` (sentenial-ledgerwarden), `keepers-guild-storage-cleanup` (sentenial-ledgerwarden), `keepers-guild-system-clean` (sentenial-ledgerwarden), `keepers-guild-digital-purge` (sentenial-ledgerwarden), `keepers-guild-device-purge` (sentenial-ledgerwarden)
- **Goblins:**
  - **Sealkeeper (`sentenial-ledgerwarden`)** — Secrets management and rotation; License compliance and tracking. KPIs: `secrets_rotated`, `sbom_drift`, `unsigned_artifacts`. Tools: `keepers-guild-secrets-audit`, `keepers-guild-security-scan`, `keepers-guild-storage-cleanup`, `keepers-guild-system-clean`, `keepers-guild-digital-purge`, `keepers-guild-device-purge`. Selection triggers: "audit secrets" → keepers-guild-secrets-audit, "check API key hygiene" → keepers-guild-secrets-audit, "run security scan" → keepers-guild-security-scan, "audit compliance" → keepers-guild-security-scan, "cleanup storage" → keepers-guild-storage-cleanup, "weekly cleanup" → keepers-guild-storage-cleanup, "system cleanup" → keepers-guild-system-clean, "clear caches" → keepers-guild-system-clean, "run digital purge" → keepers-guild-digital-purge, "audit my accounts" → keepers-guild-digital-purge, "clean my device" → keepers-guild-device-purge, "purge local data" → keepers-guild-device-purge, "rotate secrets" → Brain only (Uses brain + secrets_manage.sh script), "validate SBOM" → Brain only (Uses brain for analysis).

### Mages

- **Charter:** Forecasting, anomaly detection, and quality gates for releases.
- **Toolbelt owners:** `mages-guild-quality-lint` (launcey-gauge), `mages-guild-vault-validate` (launcey-gauge), `mages-guild-anomaly-detect` (grim-rune), `mages-guild-forecast-risk` (hex-oracle), `mages-guild-docs-update` (launcey-gauge)
- **Goblins:**
  - **Forecasting Fiend (`hex-oracle`)** — Release risk scoring and prediction; Incident likelihood forecasting. KPIs: `forecast_mae`, `forecast_mape`, `release_risk_auc`. Tools: `mages-guild-forecast-risk`. Selection triggers: "forecast release risk" → mages-guild-forecast-risk, "assess deployment safety" → mages-guild-forecast-risk, "predict incident likelihood" → mages-guild-forecast-risk, "capacity planning" → Brain only (Uses brain for predictive modeling).
  - **Glitch Whisperer (`grim-rune`)** — Anomaly detection on metrics, logs, and traces; Auto-ticket creation for detected issues. KPIs: `anomalies_preprod`, `alert_precision`, `alert_recall`. Tools: `mages-guild-anomaly-detect`. Selection triggers: "detect anomalies" → mages-guild-anomaly-detect, "analyze metrics" → mages-guild-anomaly-detect, "check system performance" → mages-guild-anomaly-detect, "auto-ticket creation" → Brain only (Uses brain for anomaly detection).
  - **Fine Spellchecker (`launcey-gauge`)** — Lint and code quality enforcement; Test coverage and quality gates. KPIs: `pr_gate_pass_rate`, `violations_per_kloc`. Tools: `mages-guild-quality-lint`, `mages-guild-docs-update`. Selection triggers: "run linters" → mages-guild-quality-lint, "check code quality" → mages-guild-quality-lint, "validate PR" → mages-guild-quality-lint, "update documentation" → mages-guild-docs-update, "generate API docs" → mages-guild-docs-update.
  <!-- GUILD_SUMMARY_END -->

#### GoblinOS Integration

All projects should integrate with GoblinOS automation where applicable:

```bash
# Example: Portfolio dev server via GoblinOS
PORTFOLIO_DIR=/path/to/project bash tools/portfolio_env.sh dev
```

#### Naming Conventions

- **Folders**: kebab-case (`forge-lite`, `rizzk-calculator`)
- **TypeScript/React**: PascalCase for components, camelCase for utilities
- **Python**: snake_case
- **Config files**: lowercase with dots (`.gitignore`, `tsconfig.json`)

### Quality Standards

#### Before Committing

- [ ] TypeScript/ESLint passes without errors
- [ ] Unit tests pass (if applicable)
- [ ] Code formatted (Prettier/Black)
- [ ] No console.logs or debug statements
- [ ] README updated if adding new features

#### Security

- ❌ NEVER commit API keys or secrets
- ✅ Use environment variables for sensitive data
- ✅ Server-side only for market data keys
- ✅ Use `.env.local` for local dev (gitignored)

## AI Assistant Workflow

### Tool Selection Preferences

**Use Continue Extension for:**

- ✅ Multi-repo operations (bulk workflow management, cross-repo cleanup)
- ✅ Complex GitHub API operations (disabling workflows, bulk repo management)
- ✅ Long-running terminal commands and scripts
- ✅ Bulk file operations across multiple projects
- ✅ Tasks requiring persistent state and extensive context
- ✅ Operations needing more control and transparency

**Use GitHub Copilot Chat for:**

- ✅ Code review and explanation
- ✅ Single-file edits and refactoring
- ✅ Documentation generation
- ✅ Quick architecture questions
- ✅ Debugging specific issues
- ✅ Writing tests for existing code

### When Adding Features

1. **Check product definition** for alignment with goals
2. **Follow monetization strategy** - keep core free
3. **Implement gates** - each week has success metrics
4. **Test offline mode** - app must work without network
5. **Add telemetry** - track for product analytics

### When Asked About Architecture

- **Frontend**: Expo (React Native) is the recommended path
- **Backend**: FastAPI for all risk math and calculations
- **Database**: Supabase with Row Level Security
- **Market Data**: Server-side only, rate-limited, cached

## GoblinOS Tooling

### Available Goblins

See `GoblinOS/goblins.yaml` for current guild configuration.

**Forge Guild** (`forge-guild`):

- `websmith` - Manages Next.js apps and portfolio deployments

### Adding New Tools

When creating automation for projects, add to `goblins.yaml`:

```yaml
guilds:
  - id: project-guild
    name: Project Guild
    charter: "Manage project development lifecycle"
    toolbelt:
      - id: project-dev
        name: Project Dev Server
        summary: "Run dev server"
        owner: owner
        command: cd apps/project && pnpm dev
```

## Important Reminders

### For AI Assistants

- ✅ Always check product definition before making changes
- ✅ Follow project roadmaps for priorities
- ✅ Respect compliance requirements
- ✅ Keep core features free, monetize edges
- ✅ Design offline-first, sync later
- ✅ Single source of truth for business logic in backend
- ✅ Test on all platforms

### For Developers

- 🎯 **Focus**: Brutal simplicity. Clear UX, one CTA per screen.
- 🎯 **Metrics**: Measure what matters.
- 🎯 **Quality**: High contrast, no gaslight error states.

## Links & Resources

- **GoblinOS Config**: `GoblinOS/goblins.yaml`
- **Monorepo Docs**: `docs/WORKSPACE_OVERVIEW.md`

---

## GoblinOS Quickstart

- List available goblins (reads `GoblinOS/goblins.yaml`):
  - bash GoblinOS/goblin-cli.sh list
- Dry-run a goblin (safe):
  - bash GoblinOS/goblin-cli.sh run --dry <goblin-id>
- Full run (owners only for destructive tasks):
  - bash GoblinOS/goblin-cli.sh run <goblin-id>

Note: A lightweight `goblin-cli` scaffold will be added to `GoblinOS/` to validate and safely execute goblins. See `GoblinOS/goblins.yaml` for the canonical manifest.

---

**Last Updated**: December 1, 2025
**Active Projects**: GoblinOS Assistant
**AI Assistant**: Follow these guidelines for all ForgeMonorepo work
