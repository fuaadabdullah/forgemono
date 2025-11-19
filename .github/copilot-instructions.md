---
description: ForgeMonorepo development guidelines and AI assistant instructions
applyTo: "**"
---

# ForgeMonorepo — AI Assistant Instructions

## Project Overview

**ForgeMonorepo** is a unified development workspace for multiple products and tools managed by GoblinOS automation. Current active projects:

1. **ForgeTM Lite** (`apps/forge-lite/`) - Cross-platform trading cockpit for retail traders
2. **Fuaad Portfolio** (external) - Personal portfolio website managed via GoblinOS
3. **RizzK Calculator** (external) - Trading risk calculator (moved to dedicated repository)
4. **GoblinOS** (`GoblinOS/`) - Development automation and tooling framework

## Current Focus: ForgeTM Lite

### Product Definition

A **free, cross-platform trading cockpit** for retail traders and students:

- ✅ Watchlist + pre-trade planning + risk sizing
- ✅ Journaling + performance analytics
- ❌ NO broker execution, NO trading signals
- 🎯 Discipline > dopamine

**Core Philosophy:**

- Truth over vibes. Everything measured in R first, dollars second.
- Offline-first, sync later. App works on the train.
- Free forever core, monetize the edges.

See: `apps/forge-lite/PRODUCT_DEFINITION.md` for complete specification.

### Tech Stack

**Frontend:**

- **Framework**: Expo (React Native) for iOS, Android, Web
- **Language**: TypeScript (strict mode)
- **State Management**: TBD (likely Zustand or React Query)
- **Charts**: Victory Native or react-native-svg-charts

**Backend:**

- **Auth & DB**: Supabase (Postgres + Row Level Security)
- **API**: FastAPI for risk math and analytics
- **Market Data**: Alpha Vantage / Twelve Data / Finnhub (server-side only)

**Infrastructure:**

- **Hosting**: Fly.io/Render for FastAPI, Supabase free tier
- **CDN**: Cloudflare
- **Telemetry**: Sentry (crashes), PostHog (product analytics)

### Project Structure

```
apps/forge-lite/
├── PRODUCT_DEFINITION.md    # Complete product spec
├── README.md                 # Project overview
├── src/                      # Application source
│   ├── app/                 # Expo App Router screens
│   ├── components/          # Reusable UI components
│   ├── services/            # API clients
│   ├── utils/               # Utilities
│   └── types/               # TypeScript types
├── api/                      # FastAPI backend
│   ├── main.py              # FastAPI entry
│   ├── routers/             # API endpoints
│   └── services/            # Business logic
└── supabase/                # Supabase migrations & config
```

## Development Guidelines

### ForgeTM Lite Specific

#### Code Standards

1. **TypeScript**: Strict mode, no `any`, explicit return types
2. **Components**: Functional components with hooks
3. **API Calls**: Type-safe client generated from OpenAPI spec
4. **Risk Math**: ONLY in FastAPI backend, frontend displays only
5. **Testing**: Unit tests for risk calculations, E2E smoke tests

#### UX Principles

- **Dark mode first** - high contrast, readable at 6 a.m.
- **Three-tab navigation**: Cockpit, Plan, Journal
- **One CTA per screen** - clear action, clear progress
- **Offline-first** - local cache, sync when online

#### Compliance Requirements

- ⚠️ **NO financial advice** - "Educational only" disclaimers
- ⚠️ **NO execution** - This is NOT a broker
- ✅ **Data export** - Users can export trades as CSV
- ✅ **Privacy Policy** - Required for App Store
- ✅ **Sign in with Apple** - Required if offering social login

### General ForgeMonorepo Standards

#### File Organization

- `/apps` - Application projects (Forge Lite, Python tools)
- `/tools` - Bash scripts for automation
- `/GoblinOS` - Automation framework and guild config
- `/docs` - Monorepo documentation
- `/infra` - Infrastructure as code

### GoblinOS Guilds & Goblins

This roster is auto-generated from `GoblinOS/goblins.yaml`. Update the YAML and run `cd GoblinOS && node scripts/generate-roles.js` to refresh both this block and the full breakdown in `GoblinOS/docs/ROLES.md`.

<!-- GUILD_SUMMARY_START -->
### Forge ([full breakdown](../GoblinOS/docs/ROLES.md#forge))
- **Charter:** Core logic, build graph, performance budgets, break-glass fixes.
- **Toolbelt owners:** `forge-lite-build` (dregg-embercode), `forge-lite-release-build` (dregg-embercode), `forge-lite-release-submit` (dregg-embercode), `framework-migrator` (dregg-embercode)
- **Goblins:**
  - **Forge Master (`dregg-embercode`)** — Core logic and build graph management; Performance budgets and optimization. KPIs: `p95_build_time`, `hot_reload_time`, `failed_build_rate`. Tools: `forge-lite-build`, `forge-lite-release-build`, `forge-lite-release-submit`. Selection triggers: "build production bundle" → forge-lite-build, "optimize build performance" → forge-lite-build, "check build time" → forge-lite-build, "build for release" → forge-lite-release-build, "submit to app stores" → forge-lite-release-submit, "port framework" → framework-migrator, "upgrade libraries" → framework-migrator.

### Crafters ([full breakdown](../GoblinOS/docs/ROLES.md#crafters))
- **Charter:** UI systems, theme tokens, a11y, CLS/LCP budgets; APIs, schemas, queues, idempotency, error budgets.
- **Toolbelt owners:** `portfolio-dev` (vanta-lumin), `portfolio-build` (vanta-lumin), `forge-lite-bootstrap` (vanta-lumin), `repo-bootstrap` (vanta-lumin), `workspace-health` (vanta-lumin), `forge-smithy` (vanta-lumin), `forge-lite-dev` (vanta-lumin), `forge-lite-api-dev` (volt-furnace), `forge-lite-db-migrate` (volt-furnace), `forge-lite-rls-check` (volt-furnace), `forge-lite-auth-login` (volt-furnace), `forge-lite-market-data-fetch` (volt-furnace), `forge-lite-telemetry-check` (vanta-lumin), `forge-lite-export-data` (volt-furnace), `overmind` (volt-furnace)
- **Goblins:**
  - **Glyph Scribe (`vanta-lumin`)** — UI systems and component architecture; Theme tokens and design system management. KPIs: `cls`, `lcp`, `a11y_score`. Tools: `portfolio-dev`, `portfolio-build`, `forge-lite-bootstrap`, `repo-bootstrap`, `workspace-health`, `forge-smithy`, `forge-lite-dev`, `forge-lite-telemetry-check`. Selection triggers: "bootstrap forge lite repo" → forge-lite-bootstrap, "setup forge lite environment" → forge-lite-bootstrap, "initialize forge lite project" → forge-lite-bootstrap, "bootstrap repository" → repo-bootstrap, "setup development environment" → repo-bootstrap, "check workspace health" → workspace-health, "run health checks" → workspace-health, "setup python environment" → forge-smithy, "python development tooling" → forge-smithy, "start portfolio dev server" → portfolio-dev, "build portfolio" → portfolio-build, "start forge lite UI development" → forge-lite-dev, "test UI components" → forge-lite-dev, "check telemetry integration" → forge-lite-telemetry-check, "update documentation" → mages-guild-docs-update.
  - **Socketwright (`volt-furnace`)** — API design and implementation; Schema management and validation. KPIs: `p99_latency`, `error_rate`, `schema_drift`. Tools: `forge-lite-api-dev`, `forge-lite-db-migrate`, `forge-lite-rls-check`, `forge-lite-auth-login`, `forge-lite-market-data-fetch`, `forge-lite-export-data`, `overmind`. Selection triggers: "start API server" → forge-lite-api-dev, "test API endpoints" → forge-lite-api-dev, "debug backend logic" → forge-lite-api-dev, "run db migrations" → forge-lite-db-migrate, "check rls policies" → forge-lite-rls-check, "auth login" → forge-lite-auth-login, "fetch market data" → forge-lite-market-data-fetch, "export user data" → forge-lite-export-data, "AI trading assistance" → overmind, "LLM routing" → overmind.

### Huntress ([full breakdown](../GoblinOS/docs/ROLES.md#huntress))
- **Charter:** Flaky test hunts, regression triage, incident tagging; early-signal scouting, log mining, trend surfacing.
- **Toolbelt owners:** `huntress-guild-analyze-tests` (magnolia-nightbloom), `huntress-guild-triage-regression` (magnolia-nightbloom), `huntress-guild-scout-signals` (magnolia-nightbloom), `huntress-guild-report-incidents` (magnolia-nightbloom)
- **Goblins:**
  - **Vermin Huntress (`magnolia-nightbloom`)** — Flaky test identification and remediation; Regression triage and root cause analysis. KPIs: `flaky_rate`, `mttr_test_failures`. Tools: `huntress-guild-analyze-tests`, `huntress-guild-triage-regression`, `huntress-guild-scout-signals`, `huntress-guild-report-incidents`. Selection triggers: "analyze tests" → huntress-guild-analyze-tests, "identify flaky tests" → huntress-guild-analyze-tests, "triage regression" → huntress-guild-triage-regression, "regression check" → huntress-guild-triage-regression, "scout signals" → huntress-guild-scout-signals, "analyze logs" → huntress-guild-scout-signals, "report incidents" → huntress-guild-report-incidents, "analyze bug reports" → huntress-guild-report-incidents.
  - **Omenfinder (`mags-charietto`)** — Early-signal detection and alerting; Log mining and pattern recognition. KPIs: `valid_early_signals`, `false_positive_rate`. Tools: Brain workflows only. Selection triggers: "analyze logs" → Brain only (Uses brain for log analysis, no external tools).

### Keepers ([full breakdown](../GoblinOS/docs/ROLES.md#keepers))
- **Charter:** Secrets, licenses, SBOM, signatures, backups, attestations.
- **Toolbelt owners:** `keepers-guild-secrets-audit` (sentenial-ledgerwarden), `keepers-guild-security-scan` (sentenial-ledgerwarden), `keepers-guild-storage-cleanup` (sentenial-ledgerwarden), `keepers-guild-system-clean` (sentenial-ledgerwarden), `keepers-guild-digital-purge` (sentenial-ledgerwarden), `keepers-guild-device-purge` (sentenial-ledgerwarden)
- **Goblins:**
  - **Sealkeeper (`sentenial-ledgerwarden`)** — Secrets management and rotation; License compliance and tracking. KPIs: `secrets_rotated`, `sbom_drift`, `unsigned_artifacts`. Tools: `keepers-guild-secrets-audit`, `keepers-guild-security-scan`, `keepers-guild-storage-cleanup`, `keepers-guild-system-clean`, `keepers-guild-digital-purge`, `keepers-guild-device-purge`. Selection triggers: "audit secrets" → keepers-guild-secrets-audit, "check API key hygiene" → keepers-guild-secrets-audit, "run security scan" → keepers-guild-security-scan, "audit compliance" → keepers-guild-security-scan, "cleanup storage" → keepers-guild-storage-cleanup, "weekly cleanup" → keepers-guild-storage-cleanup, "system cleanup" → keepers-guild-system-clean, "clear caches" → keepers-guild-system-clean, "run digital purge" → keepers-guild-digital-purge, "audit my accounts" → keepers-guild-digital-purge, "clean my device" → keepers-guild-device-purge, "purge local data" → keepers-guild-device-purge, "rotate secrets" → Brain only (Uses brain + secrets_manage.sh script), "validate SBOM" → Brain only (Uses brain for analysis).

### Mages ([full breakdown](../GoblinOS/docs/ROLES.md#mages))
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

### When Working on ForgeTM Lite

1. **Read the spec first**: Check `apps/forge-lite/PRODUCT_DEFINITION.md`
2. **Follow the roadmap**: Reference the 6-week plan for priorities
3. **Respect guardrails**: No execution, no signals, education only
4. **Offline-first**: Design for local-first, sync second
5. **Type safety**: Generate API clients from OpenAPI specs

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

### Common Tasks

#### Scaffold New Feature

```bash
# Create component
src/components/NewFeature.tsx

# Create screen
src/app/(tabs)/new-feature.tsx

# Add API endpoint
api/routers/new_feature.py

# Add types
src/types/new-feature.ts
```

#### Add Risk Calculation

```python
# ALWAYS in FastAPI backend
# api/routers/risk.py

@router.post("/risk/calc")
def calculate_position_size(entry: float, stop: float, risk_pct: float):
    # Risk math here
    return {...}
```

#### Create Database Table

```sql
-- supabase/migrations/XXX_new_table.sql

CREATE TABLE trades (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users NOT NULL,
  ticker TEXT NOT NULL,
  status TEXT NOT NULL, -- PLANNED, ACTIVE, CLOSED
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE trades ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can only see their trades"
  ON trades FOR SELECT
  USING (auth.uid() = user_id);
```

## Documentation Standards

### When Creating Docs

- Use Markdown (.md)
- Include table of contents for docs > 200 lines
- Add last updated date at bottom
- While editing, also fix any pre-existing typos, formatting errors, or broken links you encounter.
- Keep language clear and direct

### File Headers

```markdown
# Title — Subtitle if needed

Brief description of what this document covers.

## Section 1

Content...
```

## GoblinOS Tooling

### Available Goblins

See `GoblinOS/goblins.yaml` for current guild configuration.

**Forge Guild** (`forge-guild`):

- `websmith` - Manages Next.js apps and portfolio deployments

### Adding New Tools

When creating automation for ForgeTM Lite, add to `goblins.yaml`:

```yaml
guilds:
  - id: forge-lite-guild
    name: Forge Lite Guild
    charter: "Manage ForgeTM Lite development lifecycle"
    toolbelt:
      - id: forge-lite-dev
        name: Forge Lite Dev Server
        summary: "Run Expo dev server"
        owner: mobilesmith
        command: cd apps/forge-lite && pnpm dev
```

## Important Reminders

### For AI Assistants

- ✅ Always check `PRODUCT_DEFINITION.md` before making changes
- ✅ Follow the 6-week roadmap for priorities
- ✅ Respect compliance requirements (no advice, no execution)
- ✅ Keep core features free, monetize edges
- ✅ Design offline-first, sync later
- ✅ Single source of truth for risk math (FastAPI)
- ✅ Test on all platforms (iOS, Android, Web)

### For Developers

- 🎯 **Focus**: Brutal simplicity. Three tabs, one CTA per screen.
- 🎯 **Metrics**: Everything in R first, dollars second.
- 🎯 **Growth**: Templates, shareable images, campus program.
- 🎯 **Quality**: Dark mode, high contrast, no gaslight error states.

## Links & Resources

- **Product Spec**: `apps/forge-lite/PRODUCT_DEFINITION.md`
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

**Last Updated**: November 9, 2025
**Active Projects**: ForgeTM Lite, Fuaad Portfolio, RizzK Calculator
**AI Assistant**: Follow these guidelines for all ForgeMonorepo work
