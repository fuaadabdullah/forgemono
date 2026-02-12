---
description: "README"
---

# Apps

Polyglot applications that live alongside GoblinOS. Each subdirectory contains active applications and projects.

Current applications:

- `goblin-assistant/` — AI-powered development assistant (Python FastAPI backend)
- `fuaad-portfolio/` — Personal portfolio website
- `gaslight/` — Additional applications
- `python/` — Python utilities and tools
- `raptor-mini/` — Raptor monitoring system components

Supplemental directories:

- `apps/Customer projects/` — Client-specific work (e.g., `Marcus's Website/`). These deliverables keep their own README, CI, and dependency tree and are intentionally excluded from the pnpm workspace.
- `archive/forge-lite/` — Forge Lite has been archived; the original `apps/forge-lite` workspace entry is removed. Use this archive folder (see `README.md` inside it) when you need to inspect or restore Forge Lite.


Conventions:

- Keep dependencies in local `requirements.txt`.
- Use virtual environments outside the repo (do not commit `.venv`).
- Add language-specific README files describing setup and deployment.
