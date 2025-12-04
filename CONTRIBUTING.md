---
description: "CONTRIBUTING"
---

# Contributing Guidelines

Thanks for contributing! This repo follows a monorepo workflow with clear ownership and consistent tooling.

## Workflow

- Use feature branches from `main`.
- Small, focused PRs with clear titles and descriptions.
- Include tests, lint fixes, and build checks before requesting review.
- Link issues and include screenshots or logs when relevant.
- CI: CircleCI runs on pushes and PRs; ensure your branch's CircleCI pipeline passes before requesting review.
- DB changes: If your PR changes the database schema, add Supabase migration SQL via the Supabase CLI and run the `supabase_rls_check.sh` script to ensure RLS is enabled and policies are present. For Goblin Assistant use: `apps/goblin-assistant/tools/supabase_rls_check.sh apps/goblin-assistant/supabase`.

## Local Checks

Run checks at the top of each major area:

- GoblinOS (pnpm workspace):

  ```bash
  cd GoblinOS
  pnpm lint:fix && pnpm test:coverage && pnpm build
  ```

  - Python projects:

  ```bash
  # Example
  python -m venv .venv && source .venv/bin/activate
  pip install -r requirements.txt
  pytest -q
  ```

## Commit Style

- Conventional commits are encouraged (e.g., `feat:`, `fix:`, `docs:`).
- Keep messages concise and meaningful.

## Code Review

- Be kind, constructive, and specific.
- Prefer suggestions over requests when possible.
- Reviews check: scope, tests, performance, security, readability.

## Security

- Do not commit secrets. Use `.env` files and local keychains.
- Report vulnerabilities privately.

## Ownership

See `CODEOWNERS` for default reviewers. If unclear, tag the component owner in your PR.

## Documentation & Canonical Locations

To avoid duplication and ensure a single source of truth, add frontend/backend/infra documentation to the canonical directories listed below. If you find duplicate content elsewhere, update the canonical location and replace the duplicate with a short link to the canonical file.

- Frontend canonical docs:
  - `apps/goblin-assistant/PRODUCTION_DEPLOYMENT.md` (frontend deploy, Vite, Storybook)
  - `apps/goblin-assistant/docs/` (all frontend how-tos, accessibility, UI testing)

- Backend canonical docs:
  - `apps/goblin-assistant/backend/docs/` (backend quickstarts, endpoint audits, monitoring)

- Infrastructure canonical docs:
  - `goblin-infra/projects/goblin-assistant/` and `apps/goblin-assistant/infra/` (symlink to canonical) for infra & deployment specifics (Terraform, Cloudflare, Fly.io)

Contributor checklist for docs:

1. Add or update content in the canonical directory above.
2. If you update API contracts or routes, also update `apps/goblin-assistant/backend/docs/ENDPOINT_AUDIT.md` and `ENDPOINT_SUMMARY.md` (backend) and the frontend API clients (`apps/goblin-assistant/src/api/*`) as needed.
3. Replace any duplicate content elsewhere with a short link to the canonical file and a one-line reason for the move.
4. Run docs lint and spellcheck (where available) and add an entry in `docs/CHANGELOG` if the change affects user-facing behavior.

If in doubt, ask in the repo or your component owner before moving large docs across folders.

