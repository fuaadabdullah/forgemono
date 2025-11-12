---
description: "REORG_PLAN"
---

# Monorepo Reorg Plan (Proposal)

Goal: world-class structure that’s easy to navigate, operate, and onboard.

## Phase 1 — Hygiene (Done / In PR)
- Add top-level README and onboarding docs
- Add CODEOWNERS, CONTRIBUTING, templates, editor/git configs
- Update infra docs to point to canonical docs

## Phase 2 — Structure (Proposed)
- Normalize folder names (avoid spaces and punctuation)
  - Example: `Fuaads-Portfolio/` → `portfolio/`
- Introduce clear top-level domains:
  - `apps/` (Python/TS apps)
  - `packages/` (shared libs; may keep inside `GoblinOS/` for Node)
  - `infra/`, `tools/`, `docs/`, `artifacts/`
- Decide on Python layout (src/ or flat) and testing standard

## Phase 3 — Nested Git Clean-up
- Convert nested `.git` directories in demos into:
  - Submodules (if independence is desired), or
  - Monorepo packages/apps (preferred)
- Add CI to prevent accidental nested repos

## Phase 4 — CI Enhancements
- Root-level CI to run:
  - `pnpm -C GoblinOS build && test`
  - Python test matrix for `apps/` and key demos
  - Lint/format/dep scans

## Phase 5 — Docs & Automation
- Generate a project index and ownership map
- Add workspace health gate (existing GoblinOS health package) to CI

Request approval before executing Phases 2–5 (destructive/moves).

