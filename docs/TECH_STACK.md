# Tech Stack (short summary)

A concise directory of the primary technologies, frameworks, and services used in this monorepo with a one-liner and evidence file links for each.

- macOS — Local dev OS (developer machine & devcontainer host)
  - Evidence: `README.md` (prereqs mention macOS and dev tooling)

- GitHub — Source control (and GHCR for images)
  - Evidence: `.circleci/config.yml` (GHCR push), `.github/workflows/`

- Jira — Project tracking and Mira Linker integration
  - Evidence: `configure_jira_keys.sh`, `mira-linker-config.yml`

- Obsidian — Local docs vault used for internal notes & templates
  - Evidence: `tools/validate_forge_vault.sh`, `.obsidian/` scripts referenced

- Node.js & pnpm — Monorepo tooling and frontend builds
  - Evidence: `package.json`, `pnpm-lock.yaml`, `README.md` (pnpm commands)

- TypeScript, React, Vite — Frontend microapps (goblin-assistant frontend)
  - Evidence: `apps/goblin-assistant/src/`, `apps/goblin-assistant/docs/ARCHITECTURE_OVERVIEW.md`

- Next.js — Fuaad portfolio frontend
  - Evidence: `apps/fuaad-portfolio/next.config.ts`, `apps/fuaad-portfolio/README.md`

- Python 3.11+ and FastAPI — Backend services / API
  - Evidence: `apps/goblin-assistant/backend/main.py`, `backend/.env.example`, `.circleci/config.yml` (pip installs)

- Streamlit — RIZZK risk calculator project
  - Evidence: `apps/fuaad-portfolio/data/projects.ts`, `apps/fuaad-portfolio` docs

- Rust — High-performance prototypes
  - Evidence: `README.md` mentions Rust; `archive/` contains examples

- Docker & docker-compose — Containerization and devcontainers
  - Evidence: `docker-compose.yml`, `infra/devcontainer.json`

- CI/CD: CircleCI (builds & deploys), GitHub Actions (auxiliary workflows)
  - Evidence: `.circleci/config.yml`, `.circleci/SETUP.md`, `.github/workflows/`

- Deploy targets: Fly.io (backend), Vercel (frontend), Kamatera (VPS local inference)
  - Evidence: `apps/goblin-assistant/deploy-fly.sh`, `apps/goblin-assistant/deploy-vercel-bw.sh`, `docs/systems/GOBLIN_AI_SYSTEM_DOCS.md`

- Terraform — IaC orchestration
  - Evidence: `.circleci/config.yml` (terraform executor), `infra/` folder

- Databases: Supabase / Postgres, SQLite, Chroma (vector DB)
  - Evidence: `backend/.env.example`, `scripts/ops/supabase_rls_check.sh`, `chroma_db/chroma.sqlite3`

- Local LLM runtimes: Ollama, LlamaCPP
  - Evidence: `apps/raptor-mini/README.md`, `apps/raptor-mini/start.sh`

- Cloud & AI providers: OpenAI, Anthropic, Grok, DeepSeek, ElevenLabs (TTS)
  - Evidence: `apps/goblin-assistant/backend/providers/`, `apps/goblin-assistant/backend/services/routing.py`, `deploy-with-bitwarden.sh`

- Secrets & vaults: Bitwarden, SOPS, HashiCorp Vault references
  - Evidence: `apps/goblin-assistant/.circleci/fetch_secrets.sh`, `apps/goblin-assistant/scripts/setup_bitwarden.sh`, `infra/secrets/.sops.yaml`

- Observability: Sentry, OpenTelemetry, Prometheus, Grafana, Tempo, Datadog
  - Evidence: `apps/goblin-assistant/docs/ARCHITECTURE_OVERVIEW.md`, `GoblinOS/SOURCE_OF_TRUTH.md`, `tools/telemetry/`

- Monitoring & Dashboards: Grafana / Prometheus / Tempo
  - Evidence: `docs/systems/GOBLIN_AI_SYSTEM_DOCS.md`, `docker-compose.yml` monitoring stack setup

- Testing: pytest, pytest-asyncio, ruff, ESLint/Prettier
  - Evidence: `.circleci/config.yml` (pip install pytest), `tests/` where available

- Trading & Market Data integrations: Polygon, Benzinga, TradingView, trade logs
  - Evidence: `apps/fuaad-portfolio/content/resume.md`, `apps/forge-lite/` connectors

## Notes

- This file is a compact “tech stack” reference. See detailed architecture docs and app README for full context:
  - `apps/goblin-assistant/docs/ARCHITECTURE_OVERVIEW.md`
  - `docs/systems/GOBLIN_AI_SYSTEM_DOCS.md`
  - `*.README.md` files in each app folder

