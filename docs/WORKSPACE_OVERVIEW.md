---
description: "WORKSPACE_OVERVIEW"
---

# Workspace Overview

This monorepo contains GoblinOS (primary platform), infra tooling, utilities, and demo/portfolio projects.

## Structure

- `apps/` — Polyglot applications (currently `python/rizzk-calculator`).
- `GoblinOS/` — TypeScript/pnpm workspace for the Goblin platform, agents, and automation.
- `infra/` — Devcontainer, docker-compose, and deployment scaffolding.
- `tools/` — Dev scripts, release helpers, TUIs.
- `portfolio/` — Personal docs/assets (resume, project notes).
- `artifacts/` — Generated files (reports, SARIF, etc.).

## Conventions

- Node: pnpm + Node 20/22. Run commands within `GoblinOS/`.
- Python: Use venvs per project. Keep dependencies in `requirements.txt`.
- Naming: Future refactors will normalize folder names; avoid spaces in new folders.
- Ownership: See `CODEOWNERS`.

## Nested Git Repos

Some demo directories may contain a nested `.git` (legacy import). These can confuse tooling. Prefer:

1. Promote to a proper package in `GoblinOS/packages/` (Node) or a top-level `apps/` dir (Python), or
2. Convert to a formal git submodule if it must remain independent.

Propose changes via PR before moving directories.

## Getting Started (GoblinOS)

```bash
cd GoblinOS
pnpm install
pnpm build
pnpm test
```

For AI features (Ollama) and more, see `GoblinOS/README.md`.

## KPI test helpers (bridge)

The Overmind bridge package (`packages/goblins/overmind/bridge`) exposes a small in-memory mock KPI store when tests run with `OVERMIND_MOCK=1`. This is useful for asserting that KPI events and tool invocations are recorded during integration tests.

Key helpers (available in the bridge test harness):

- `kpiStore.getRecordedEvents()` — returns recorded KPI events (with timestamps).
- `kpiStore.getRecordedToolInvocations()` — returns recorded tool invocation records.
- `kpiStore.clear()` — clear recorded events (useful in `beforeEach`).

See `packages/goblins/overmind/bridge/README.md` for a short example test snippet showing usage.
