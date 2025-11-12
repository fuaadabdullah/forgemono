---
description: "README"
---

# ForgeMonorepo

Unified workspace for GoblinOS and related projects. This repo houses the GoblinOS platform, infrastructure assets, tools, and portfolio/demo projects.

## Project Map

- `apps/` — Polyglot applications (e.g., `python/rizzk-calculator`).
- `GoblinOS/` — Primary platform (pnpm workspace: packages, docs, CI). See `GoblinOS/README.md`.
- `infra/` — Devcontainer, docker-compose, and deployment scaffolding.
- `tools/` — Utility scripts, TUI helpers, release tools.
- `portfolio/` — Personal assets (resume, future project write-ups).
- `artifacts/` — Generated outputs (e.g., reports, SARIF).

### Key Docs

- Overmind Agent overview: `docs/agents/overmind.md`

## Quick Start

Prereqs: Node 20/22 + pnpm, Python 3.11+, Docker Desktop, Git.

```bash
# Clone and open
git clone <this-repo>
cd ForgeMonorepo

# GoblinOS
cd GoblinOS
pnpm install
pnpm build
pnpm test
```

For AI features (Ollama) and deeper commands, see `GoblinOS/README.md`.

## Onboarding

- Start with `docs/WORKSPACE_OVERVIEW.md` for structure and conventions.
- Follow `docs/ONBOARDING_TARIQ.md` for step-by-step setup to contribute to GoblinOS.
- See `CONTRIBUTING.md` for branch/PR standards and local checks.

## Notes

- Legacy demos may have shipped with their own `.git` history—these should be promoted into `apps/` or converted to submodules. See `docs/WORKSPACE_OVERVIEW.md` for guidance.
