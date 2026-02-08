---
description: "ONBOARDING_TARIQ"
---

# Onboarding: Tariq Fletcher → GoblinOS

Welcome! This guide gets your environment ready to contribute to GoblinOS inside the ForgeMonorepo.

## 1) Prerequisites

- macOS or Linux recommended
- Node 20 or 22 + pnpm (`corepack enable && corepack prepare pnpm@latest --activate`)
- Python 3.11+
- Docker Desktop
- Git + GitHub access to this repo
- VS Code (recommended) with extensions:
  - ESLint/Biome, EditorConfig, Prettier
  - Python, Pytest, Docker

## 2) Clone and First Build

```bash
git clone <repo-url>
cd ForgeMonorepo/GoblinOS
pnpm install
pnpm build
pnpm test
```

## 3) AI Features (Ollama)

Option A — Docker (recommended):

```bash

cd GoblinOS/packages/goblins/overmind
docker-compose up -d ollama
```

Option B — Local:

```bash
brew install ollama
ollama serve
ollama pull qwen2.5:3b
```

Set `OLLAMA_BASE_URL` in `GoblinOS/.env` if not default.

## 4) Environment Variables

```bash

cd GoblinOS
cp .env.example .env

# Fill in any required keys
```

See `docs/API_KEYS_MANAGEMENT.md` for guidance.

## 5) Daily Dev Loop

```bash
pnpm -C GoblinOS dev        # if applicable to the package you’re working on
pnpm -C GoblinOS lint:fix
pnpm -C GoblinOS test:coverage
pnpm -C GoblinOS build
```

## 6) PR Flow

- Branch from `main`: `feat/…` or `fix/…`
- Keep PRs focused and < 300 lines where possible
- Include tests + docs updates
- Request review from owners (see `CODEOWNERS`)

## 7) Notes on Portfolio Projects

Polyglot apps live under `apps/` (Python apps moved to dedicated repositories). Run them in isolated venvs. If you need to modernize or integrate with GoblinOS, propose a refactor first.

## 8) First Tickets

- Run workspace health checks (if available) and fix any low-hanging issues in `GoblinOS/packages/goblins/workspace-health`.
- Add yourself to `CODEOWNERS` once your GitHub handle is confirmed.

If anything is unclear, ping Fuaad for context and next steps.
