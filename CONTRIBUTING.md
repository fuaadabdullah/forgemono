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

