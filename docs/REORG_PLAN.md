## Repo Reorganization Plan (short-term)

This document records the initial changes performed to consolidate the monorepo and improve security and stability.

What was done (2025-12-11):

- Added .gitignore patterns to ignore database files, redis dumps, logs, and backups.
- Archived sensitive files into `.archive/removed-secrets/` and removed them from Git tracking.
- Created `docs/` structure and moved a subset of root-level documentation into the canonical `docs/` folders (deployments, automation, integrations, systems).
- Consolidated deployment scripts by moving root-level deploy scripts into `scripts/deploy/`.
- Archived `apps/goblin-assistant/backend-api/` to `apps/goblin-assistant/backend-api-archive-20251211/` and added a README redirect to the canonical `backend/` folder.
- Archived `apps/goblin-assistant/backend-api/` to `apps/goblin-assistant/backend-api-archive-20251211/` and added a README redirect to the canonical `backend/` folder.
- Added an archival README to `apps/goblin-assistant/api/`, updated startup scripts (`start_server.sh`, `start_server_script.sh`) to point to `apps/goblin-assistant/backend/`, and removed the legacy `api/` copy step from `tools/migrate-to-multirepo.sh`.

Next steps / Recommendations:

1. ✅ **Completed**: Performed duplicate-content review between `backend/` and the archived `api/` folder. No functional differences found to migrate — `backend/` already contains the consolidated and updated FastAPI code, while `api/` contains legacy Flask mocks and stubs. No code migration needed.
2. Update any CI/CD references or environment configurations that point to `backend-api` to use `backend/`.
3. Migrate any required deploy scripts into `infra/deployments/*` or `scripts/deploy/` with clear platform-level directories (e.g. `scripts/deploy/kamatera`, `scripts/deploy/fly`, `scripts/deploy/vercel`).
4. Schedule a Git history cleaning (BFG/git-filter-repo) to remove secrets that were previously committed. This is a sensitive operation and must be handled carefully.
5. Add more symbolic redirect stubs at the old locations during a 2-week migration window.

If you need assistance executing steps 1 or 4 above, ask for a separate migration plan and we'll implement it with tests to confirm nothing breaks.

---

This is a living document. Update as the reorganization progresses.
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

