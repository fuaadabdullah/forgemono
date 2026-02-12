---
description: ForgeMonorepo development guidelines and AI assistant instructions
applyTo: '**'
---

# ForgeMonorepo — AI Assistant Instructions

## Project Overview

**ForgeMonorepo** is a unified development workspace for multiple products and tools managed by
GoblinOS automation. Current active projects:

1. **GoblinOS Assistant** (goblin-assistant) - AI assistant for development automation

### Infrastructure

#### Cloudflare Edge (goblin-assistant)

All Goblin Assistant services are protected and accelerated by Cloudflare:

**Location**: `goblin-infra/projects/goblin-assistant/infra/cloudflare/`

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
- **Analytics Engine**: Free observability (fallback for Datadog in dev/non-production)
  - Latency insights (p50, p95, p99 by endpoint)
  - Error maps (4xx/5xx rates, failure patterns)
  - Geographic heatmaps (user distribution, datacenter performance)
  - Cache hit ratios (KV, R2, edge cache effectiveness)
  - LLM performance (provider latency, token usage, model comparison)
  - **Free tier**: 10M data points/month (then $0.25 per 1M)
  - **Cost savings**: $50-200/month vs Datadog

Note: In production we use Datadog as our canonical observability platform for the Goblin Assistant
backend: metrics, traces, logs, SLOs, and monitors are defined and managed in Datadog. The Analytics
Engine is a lower-cost fallback for local development or low-volume environments. See
`apps/goblin-assistant/datadog/DATADOG_SLOS.md` and `apps/goblin-assistant/PRODUCTION_MONITORING.md`
for Datadog-specific configuration, SLOs, and monitors.

**Documentation**: See `goblin-infra/projects/goblin-assistant/infra/cloudflare/README.md` for
complete setup and operations guide.

**Key Commands**:

```bash
# Deploy Worker
cd goblin-infra/projects/goblin-assistant/infra/cloudflare && wrangler deploy

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

This roster is auto-generated from `GoblinOS/goblins.yaml`. Update the YAML and run
`cd GoblinOS && node scripts/generate-roles.js` to refresh both this block and the full breakdown in
`GoblinOS/docs/ROLES.md`.

<!-- GUILD_SUMMARY_START -->

### Crafters

- **Charter:** UI systems, theme tokens, a11y, CLS/LCP budgets; APIs, schemas, queues, idempotency,
  error budgets.
- **Toolbelt owners:** `portfolio-dev` (vanta-lumin), `portfolio-build` (vanta-lumin),
  `repo-bootstrap` (vanta-lumin), `workspace-health` (vanta-lumin), `forge-smithy` (vanta-lumin),
  `overmind` (volt-furnace)
- **Goblins:**
  - **Glyph Scribe (`vanta-lumin`)** — UI systems and component architecture; Theme tokens and
    design system management. KPIs: `cls`, `lcp`, `a11y_score`. Tools: `portfolio-dev`,
    `portfolio-build`, `repo-bootstrap`, `workspace-health`, `forge-smithy`, `overmind`. Selection
    triggers: # "bootstrap forge lite repo" → forge-lite-bootstrap, # "setup forge lite environment"
    → forge-lite-bootstrap, # "initialize forge lite project" → forge-lite-bootstrap, "bootstrap
    repository" → repo-bootstrap, "setup development environment" → repo-bootstrap, "check workspace
    health" → workspace-health, "run health checks" → workspace-health, "setup python environment" →
    forge-smithy, "python development tooling" → forge-smithy, "start portfolio dev server" →
    portfolio-dev, "build portfolio" → portfolio-build, # "start forge lite UI development" →
    forge-lite-dev, # "test UI components" → forge-lite-dev, # "check telemetry integration" →
    forge-lite-telemetry-check, "update documentation" → mages-guild-docs-update.
  - **Socketwright (`volt-furnace`)** — API design and implementation; Schema management and
    validation. KPIs: `p99_latency`, `error_rate`, `schema_drift`. Tools: # `forge-lite-api-dev`, #
    `forge-lite-db-migrate`, # `forge-lite-rls-check`, # `forge-lite-auth-login`, #
    `forge-lite-market-data-fetch`, # `forge-lite-export-data`, `overmind`. Selection triggers: #
    "start API server" → forge-lite-api-dev, # "test API endpoints" → forge-lite-api-dev, # "debug
    backend logic" → forge-lite-api-dev, # "run db migrations" → forge-lite-db-migrate, # "check rls
    policies" → forge-lite-rls-check, # "auth login" → forge-lite-auth-login, # "fetch market data"
    → forge-lite-market-data-fetch, # "export user data" → forge-lite-export-data, "AI trading
    assistance" → overmind, "LLM routing" → overmind.
- **Goblins:**
  - **Vermin Huntress (`magnolia-nightbloom`)** — Flaky test identification and remediation;
    Regression triage and root cause analysis. KPIs: `flaky_rate`, `mttr_test_failures`. Tools:
    `huntress-guild-analyze-tests`, `huntress-guild-triage-regression`,
    `huntress-guild-scout-signals`, `huntress-guild-report-incidents`. Selection triggers: "analyze
    tests" → huntress-guild-analyze-tests, "identify flaky tests" → huntress-guild-analyze-tests,
    "triage regression" → huntress-guild-triage-regression, "regression check" →
    huntress-guild-triage-regression, "scout signals" → huntress-guild-scout-signals, "analyze logs"
    → huntress-guild-scout-signals, "report incidents" → huntress-guild-report-incidents, "analyze
    bug reports" → huntress-guild-report-incidents.
  - **Omenfinder (`mags-charietto`)** — Early-signal detection and alerting; Log mining and pattern
    recognition. KPIs: `valid_early_signals`, `false_positive_rate`. Tools: Brain workflows only.
    Selection triggers: "analyze logs" → Brain only (Uses brain for log analysis, no external
    tools).

### Keepers

- **Charter:** Secrets, licenses, SBOM, signatures, backups, attestations.
- **Toolbelt owners:** `keepers-guild-secrets-audit` (sentenial-ledgerwarden),
  `keepers-guild-security-scan` (sentenial-ledgerwarden), `keepers-guild-storage-cleanup`
  (sentenial-ledgerwarden), `keepers-guild-system-clean` (sentenial-ledgerwarden),
  `keepers-guild-digital-purge` (sentenial-ledgerwarden), `keepers-guild-device-purge`
  (sentenial-ledgerwarden)
- **Goblins:**
  - **Sealkeeper (`sentenial-ledgerwarden`)** — Secrets management and rotation; License compliance
    and tracking. KPIs: `secrets_rotated`, `sbom_drift`, `unsigned_artifacts`. Tools:
    `keepers-guild-secrets-audit`, `keepers-guild-security-scan`, `keepers-guild-storage-cleanup`,
    `keepers-guild-system-clean`, `keepers-guild-digital-purge`, `keepers-guild-device-purge`.
    Selection triggers: "audit secrets" → keepers-guild-secrets-audit, "check API key hygiene" →
    keepers-guild-secrets-audit, "run security scan" → keepers-guild-security-scan, "audit
    compliance" → keepers-guild-security-scan, "cleanup storage" → keepers-guild-storage-cleanup,
    "weekly cleanup" → keepers-guild-storage-cleanup, "system cleanup" → keepers-guild-system-clean,
    "clear caches" → keepers-guild-system-clean, "run digital purge" → keepers-guild-digital-purge,
    "audit my accounts" → keepers-guild-digital-purge, "clean my device" →
    keepers-guild-device-purge, "purge local data" → keepers-guild-device-purge, "rotate secrets" →
    Brain only (Uses brain + secrets_manage.sh script), "validate SBOM" → Brain only (Uses brain for
    analysis).

### Mages

- **Charter:** Forecasting, anomaly detection, and quality gates for releases.
- **Goblins:**
  - **Forecasting Fiend (`hex-oracle`)** — Release risk scoring and prediction; Incident likelihood
    forecasting. KPIs: `forecast_mae`, `forecast_mape`, `release_risk_auc`. Tools:
    `mages-guild-forecast-risk`. Selection triggers: "forecast release risk" →
    mages-guild-forecast-risk, "assess deployment safety" → mages-guild-forecast-risk, "predict
    incident likelihood" → mages-guild-forecast-risk, "capacity planning" → Brain only (Uses brain
    for predictive modeling).
  - **Glitch Whisperer (`grim-rune`)** — Anomaly detection on metrics, logs, and traces; Auto-ticket
    creation for detected issues. KPIs: `anomalies_preprod`, `alert_precision`, `alert_recall`.
    Tools: `mages-guild-anomaly-detect`. Selection triggers: "detect anomalies" →
    mages-guild-anomaly-detect, "analyze metrics" → mages-guild-anomaly-detect, "check system
    performance" → mages-guild-anomaly-detect, "auto-ticket creation" → Brain only (Uses brain for
    anomaly detection).

#### GoblinOS Integration

All projects should integrate with GoblinOS automation where applicable:

```bash

PORTFOLIO_DIR=/path/to/project bash tools/portfolio_env.sh dev
```

#### Naming Conventions

- **Folders**: kebab-case (`forge-lite`, `rizzk-calculator`)
- **TypeScript/React**: PascalCase for components, camelCase for utilities
- **Config files**: lowercase with dots (`.gitignore`, `tsconfig.json`)

### Quality Standards

#### Before Committing

- [ ] TypeScript/ESLint passes without errors
- [ ] Unit tests pass (if applicable)
- [ ] Code formatted (Prettier/Black)
- [ ] No console.logs or debug statements
- [ ] README updated if adding new features
- [ ] Documentation quality checked with `doc_quality_check.py` (if docs changed)
- [ ] CircleCI pipelines pass on the PR (CI checks green)
- [ ] DB migrations included & RLS checked (if the PR changes database schema)

### Security

- ❌ NEVER commit API keys or secrets
- ✅ Use environment variables for sensitive data
- ✅ Server-side only for market data keys
- ✅ Use `.env.local` for local dev (gitignored)
- ✅ We use Bitwarden as the team's primary vault for storing and rotating secrets (Bitwarden or
  equivalent vaults like 1Password, HashiCorp Vault, AWS Secrets Manager may be used when
  appropriate). Follow `docs/SECRETS_HANDLING.md` and `infra/secrets/README.md` for access patterns
  and automation.

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
- ✅ Documentation quality assessment and improvement suggestions
- ✅ Running documentation quality checks with `doc_quality_check.py`

## CI / CD (CircleCI)

We use CircleCI as our canonical CI/CD provider across the monorepo. CircleCI pipelines are defined
in the repo root under `.circleci/config.yml` with per-app overrides when needed (e.g.,
`apps/goblin-assistant/.circleci/config.yml`). CircleCI orchestrates build, tests, secret fetching
(Bitwarden integration), and production deployments (e.g., Fly.io), and runs on pushes to `main` and
on PR validation workflows.

- CircleCI setup and onboarding: `.circleci/SETUP.md` — follow this to register the repo, configure
  contexts, and validate local pipelines.

- Deploy and secret handling: for Goblin Assistant the pipeline uses
  `apps/goblin-assistant/.circleci/fetch_secrets.sh` (Bitwarden) and
  `apps/goblin-assistant/.circleci/config.yml` to fetch secrets and deploy to Fly.io per
  `apps/goblin-assistant/docs/PRODUCTION_PIPELINE.md`.

- Validation: Use `circleci config validate` and `circleci pipeline trigger --branch main` for
  testing pipelines locally.

- Secret management: Use Bitwarden + CircleCI contexts. Do NOT commit secrets into the repo; follow
  `docs/SECRETS_HANDLING.md`.

Note: If you require heavy Docker builds in CI, we recommend CircleCI self-hosted runners (see
`.circleci/SETUP.md`) instead of public runners.

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

## Database (Supabase)

We use Supabase (Postgres) as our canonical persistent data store and Auth provider for several apps
(e.g. Goblin Assistant, Forge Lite, Gaslight). Key notes and best practices:

- Core uses: Postgres storage for users, sessions, inference logs, feature flags, and other business
  data - not for large vector embeddings (see `chroma_db` for vectors).

- Authentication & Authorization: Use Supabase Auth for signups/logins (client libraries in
  `apps/gaslight` and others). For tenant or user-scoped data, always use Row Level Security (RLS)
  policies and a minimal set of Postgres roles.

- Migrations: Use the Supabase CLI to create and apply migrations (`supabase migration new <name>`).
  Commit SQL migration files. Keep migrations idempotent where possible and include RLS enable
  statements:
  - `ALTER TABLE public.<table> ENABLE ROW LEVEL SECURITY;`

- RLS Audit: Run the repository's simple RLS audit script before merging DB migrations:
  `scripts/ops/supabase_rls_check.sh` (or pass the Supabase folder when relevant). This checks that
  `CREATE TABLE` statements are accompanied by explicit RLS enablement and flags missing policies.

- Local dev: Use `supabase start` (Supabase CLI) for a local Postgres instance for development, or
  connect to staging Supabase project for testing. The Supabase CLI is mentioned in
  `apps/goblin-assistant/backend/README.md`.

- Secrets: Never commit `service_role` keys or admin keys. Store them securely in Bitwarden and pass
  to CI via CircleCI contexts. Use `apps/goblin-assistant/.circleci/fetch_secrets.sh` to populate
  environment variables in pipelines.

- CI: CI pipelines should validate database migrations and run the RLS audit as part of PR checks.
  Add migration and policy review to PRs that change DB schemas.

- Backups & compliance: Ensure regular database backups and export paths for compliance requests. If
  using Supabase hosted plans, use their snapshot/backups. For self-managed Postgres, use
  `pg_dump`/`pg_restore` or managed snapshots.

- Data privacy: Do not store PII in vector stores or logs without consent; enforce data deletion and
  TTLs where required.

Matching files: See `apps/goblin-assistant/backend/README.md` (Supabase CLI install),
`scripts/ops/supabase_rls_check.sh` (RLS audit), and `docs/backend/DATA_FLOW_DIAGRAM.md` (where
Supabase fits in the architecture).

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
    charter: 'Manage project development lifecycle'
    toolbelt:
      - id: project-dev
        name: Project Dev Server
        summary: 'Run dev server'
        owner: owner
        command: cd apps/project && pnpm dev
```

## Documentation Quality Checker

The ForgeMonorepo includes an automated documentation quality analysis tool powered by the Raptor
Mini API. This tool helps maintain high-quality documentation standards across the codebase.

### Tool Location

- **Script**: `tools/doc-quality/doc_quality_check.py`
- **Configuration**: `tools/doc-quality/doc_quality_config.yaml`
- **Documentation**: `docs/DOC_QUALITY_AUTOMATION.md`

### Usage Examples

**Basic Quality Check:**

```bash

# Check all documentation files
python3 tools/doc-quality/doc_quality_check.py

# Check specific files
python3 tools/doc-quality/doc_quality_check.py docs/README.md docs/WORKSPACE_OVERVIEW.md

# CI mode with quality gates
python3 tools/doc-quality/doc_quality_check.py --ci --min-score 70
```

**Debug and Development:**

```bash
# Full debug mode
python3 tools/doc-quality/doc_quality_check.py --debug --debug-api --debug-timing

# Save API responses for analysis
python3 tools/doc-quality/doc_quality_check.py --save-responses ./debug_logs

# Environment-based debugging
DOC_QUALITY_DEBUG_API=true python3 tools/doc-quality/doc_quality_check.py
```

### Quality Metrics

The tool analyzes documentation for:

- **Clarity**: Clear, understandable content
- **Completeness**: Comprehensive coverage of topics
- **Structure**: Well-organized sections and headings
- **Accuracy**: Technically correct information
- **Readability**: Appropriate language and formatting

**Scoring Scale:**

- **High Quality**: ≥80/100
- **Medium Quality**: 60-79/100
- **Low Quality**: <60/100

### Integration Points

**Git Pre-commit Hook:**

```bash

# Install hook to check docs before commits
cp pre-commit-doc-check.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

## -**CI/CD Pipeline:**

- GitHub Actions workflow: `.github/workflows/docs-ci.yml`
- Runs on documentation changes
- Fails CI if quality standards aren't met
- Comments on pull requests with results

**When to Use:**

- ✅ Before committing documentation changes
- ✅ In CI/CD pipelines for quality gates
- ✅ During development to check documentation quality
- ✅ For bulk analysis of existing documentation

### AI Assistant Integration

When working with documentation in the ForgeMonorepo:

1. **Always run quality checks** before committing documentation changes
2. **Use debug mode** when troubleshooting quality analysis issues
3. **Check CI results** to ensure documentation meets standards
4. **Review improvement suggestions** provided by the tool

The tool is particularly useful for:

- Ensuring consistent documentation quality across the monorepo
- Catching documentation issues before they reach production
- Providing actionable feedback for documentation improvements
- Maintaining high standards for user-facing and developer documentation

## Important Reminders

### For AI Assistants

- ✅ Always check product definition before making changes
- ✅ Follow project roadmaps for priorities
- ✅ Respect compliance requirements
- ✅ Keep core features free, monetize edges
- ✅ Design offline-first, sync later
- ✅ Single source of truth for business logic in backend
- ✅ Test on all platforms
- ✅ Primary CDN/Edge provider: Cloudflare — use Cloudflare Workers, KV, D1, R2, Cloudflare Tunnel,
  and Turnstile for edge functionality; consult
  `goblin-infra/projects/goblin-assistant/infra/cloudflare/README.md` and Cloudflare docs when
  authoring edge/traffic/CDN-related code.

### Data & Privacy (Goblin Assistant Backend)

- Purpose: The Goblin Assistant backend processes and stores conversational context, user
  preferences, telemetry, inference logs, and optional RAG sources. All code suggestions and
  generated changes must treat this data as sensitive and follow the rules below.

- Data categories:
  - Conversation context (KV/short-lived storage), session metadata, and user preferences.
  - Inference logs (provider, model, cost, latency) and audit logs.
  - Vector DB / embeddings used for RAG (Chroma or other vector stores).
  - Telemetry and observability data (aggregated metrics, traces, alerts).
- Safety rules (must follow):
  - Minimize: Use only the minimum data needed in prompts and code paths. Avoid including entire
    transcripts unless necessary.

  - Sanitize: Remove PII, secrets, API keys, tokens, and other sensitive identifiers before sending
    data to external providers, saving to logs, or adding to embeddings.

  - Embeddings / Vector DB: Do NOT embed documents that include PII or secrets. Add a
    sanitization/consent check before creating embeddings. Store a document metadata flag for
    sensitivity and apply a TTL or explicit deletion policy.

  - Conversation TTL: Keep conversation context ephemeral. Use Cloudflare KV with a short TTL (e.g.,
    1h) by default. For persistent chat history, obtain explicit user consent and store encrypted
    server-side with strict RBAC and audit logs.

  - Supabase RLS & retention: When storing user/tenant-scoped data in Supabase/Postgres, always
    enable Row Level Security and define minimal `CREATE POLICY` statements; use TTL policies where
    needed for retention/deletion. Run `scripts/ops/supabase_rls_check.sh` before merging DB
    changes.

  - Logging & telemetry: Do not log raw messages or secrets. Track inference metrics (model,
    provider, latency, cost) while redacting or hashing message content. In production, these
    metrics and traces are ingested into Datadog — follow
    `apps/goblin-assistant/backend/docs/MONITORING_IMPLEMENTATION.md` for data retention,
    redact/sampling practices, and `apps/goblin-assistant/PRODUCTION_MONITORING.md` for how we
    configure Datadog (agents, API keys, SLOs). Also see
    `apps/goblin-assistant/datadog/DATADOG_SLOS.md` for the canonical SLO and monitor examples.

  - Access Control & Encryption: Use RBAC and least-privilege for all storage; encrypt data at rest
    and in transit, and store keys in Bitwarden or a managed secrets store (see
    `docs/SECRETS_HANDLING.md`).

  - RAG / Sources: When returning generated answers with citations, only include permitted data and
    add `source` metadata. If a source is flagged as restricted, avoid showing it in answers or
    embedding it.

  - Data Deletion / Retention: Implement TTLs and retention schedules (inference logs, vector DB
    TTLs) and support data export/delete workflows for user requests; reference
    `MONITORING_IMPLEMENTATION.md`.

  - Compliance: Follow local legal/regulatory requirements (GDPR/CCPA) for data processing, export,
    and deletion. When proposing code for handling user data, include data export and erasure
    functionality.

- Developer guidance for Copilot & code generation:
  - Don’t include real secrets or emails in examples; use placeholders like `REDACTED` or
    `example@domain.com`.

  - If generating code that persists user data, include a sanitization step and explicit consent
    check: `sanitize_input_for_model()`, `is_sensitive_content()`, or `mask_sensitive()` (suggest
    these helpers and add tests if not present).

  - To create embeddings or long-term storage, add a pre-check to ensure content is not PII, and
    implement a TTL or a deletion path for removal on user request.

  - For logging, add redaction (e.g., `redactSensitiveFields()`), and ensure logs sent to telemetry
    providers are stripped of PII and sensitive tokens.

  - For telemetry sampling: use aggregated metrics for analytics and alerts; don’t send raw user
    messages.

  - When suggesting architecture or implementation changes, include instructions for monitoring,
    retention, and privacy checks required to push the change to production.

See `apps/goblin-assistant/backend/docs/MONITORING_IMPLEMENTATION.md`,
`apps/goblin-assistant/backend/docs/PRODUCTION_MONITORING.md`, and `docs/SECRETS_HANDLING.md` for
canonical patterns and retention/rotation schedules.

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

Note: A lightweight `goblin-cli` scaffold will be added to `GoblinOS/` to validate and safely
execute goblins. See `GoblinOS/goblins.yaml` for the canonical manifest.

---

## Test Migration Assistant (Enzyme → Testing Library)

When converting Enzyme tests to Testing Library, follow these guidelines:

### Always:

- Use `screen.getByRole()` over other queries when possible
- Use `userEvent` over `fireEvent` for user interactions
- Test behavior, not implementation details
- Remove all Enzyme imports (`import { shallow, mount } from 'enzyme'`)
- Add `@testing-library/react` and `@testing-library/user-event` imports
- Prefer async/await for user interactions

### Migration Patterns:

#### Component Rendering:

```javascript
// ❌ Enzyme:
const wrapper = shallow(<Component />);
const wrapper = mount(<Component />);

// ✅ Testing Library:
import { render, screen } from '@testing-library/react';
render(<Component />);
```

#### Element Queries:

```javascript
// ❌ Enzyme:
wrapper.find('button').simulate('click');
wrapper.find('.my-class');
expect(wrapper.find('span').text()).toBe('text');

// ✅ Testing Library:
const button = screen.getByRole('button');
const element = screen.getByText('text');
const styledElement = screen.getByTestId('my-element');
```

#### User Interactions:

```javascript
// ❌ Enzyme:
wrapper.find('button').simulate('click');
wrapper.find('input').simulate('change', { target: { value: 'new value' } });

// ✅ Testing Library:
import userEvent from '@testing-library/user-event';
const user = userEvent.setup();
await user.click(button);
await user.type(input, 'new value');
```

#### State/Props Testing:

```javascript
// ❌ Enzyme (don't do this):
expect(wrapper.state('count')).toBe(1);
expect(wrapper.prop('disabled')).toBe(true);

// ✅ Testing Library (test what user sees):
expect(screen.getByText('Count: 1')).toBeInTheDocument();
expect(button).toBeDisabled();
```

### Common Conversion Examples:

#### Button Component Test:

```javascript
// Before (Enzyme):
import { shallow } from 'enzyme';

it('calls onClick when clicked', () => {
  const mockOnClick = jest.fn();
  const wrapper = shallow(<Button onClick={mockOnClick} />);
  wrapper.find('button').simulate('click');
  expect(mockOnClick).toHaveBeenCalled();
});

// After (Testing Library):
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

it('calls onClick when clicked', async () => {
  const mockOnClick = jest.fn();
  const user = userEvent.setup();
  render(<Button onClick={mockOnClick} />);

  const button = screen.getByRole('button');
  await user.click(button);
  expect(mockOnClick).toHaveBeenCalled();
});
```

#### Form Input Test:

```javascript
// Before (Enzyme):
it('updates value on change', () => {
  const wrapper = shallow(<Input />);
  const input = wrapper.find('input');
  input.simulate('change', { target: { value: 'new value' } });
  expect(input.prop('value')).toBe('new value');
});

// After (Testing Library):
it('updates value on change', async () => {
  const user = userEvent.setup();
  render(<Input />);

  const input = screen.getByRole('textbox');
  await user.type(input, 'new value');
  expect(input).toHaveValue('new value');
});
```

### AI Assistant Prompt Template:

When asked to convert Enzyme tests, use this prompt:

```
I'm migrating React tests from Enzyme to Testing Library. Convert this test:

[PASTE ENZYME TEST HERE]

Guidelines:
1. Use Testing Library queries (getByRole preferred)
2. Use userEvent for interactions
3. Test behavior, not implementation
4. Keep the same test descriptions
5. Add proper async/await for user events

Provide ONLY the converted test code, no explanations.
```

### Migration Priority:

1. **High Priority**: Simple component tests with basic interactions
2. **Medium Priority**: Form components, data display components
3. **Low Priority**: Complex components with heavy state management
4. **Skip**: Tests that are already well-covered by integration tests

---

**Last Updated**: December 9, 2025 **Active Projects**: GoblinOS Assistant, Documentation Quality
Checker **AI Assistant**: Follow these guidelines for all ForgeMonorepo work
