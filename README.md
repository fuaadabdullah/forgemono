---
description: "README"
---

# ForgeMonorepo

Unified workspace for GoblinOS and related projects. This repo houses the GoblinOS platform, infrastructure assets, tools, and portfolio/demo projects.

## Project Map

- `apps/` — Active polyglot applications and projects (Python, Node.js, etc.)
- `GoblinOS/` — Primary platform (pnpm workspace: packages, docs, CI). See `GoblinOS/README.md`.
- `infra/` — Devcontainer, docker-compose, and deployment scaffolding.
- `tools/` — Utility scripts, TUI helpers, release tools.
- `portfolio/` — Personal assets (resume, future project write-ups).
- `artifacts/` — Generated outputs (e.g., reports, SARIF).

### Key Docs

- Overmind Agent overview: `docs/agents/overmind.md`
- GoblinOS Assistant Architecture: `apps/goblin-assistant/docs/ARCHITECTURE_OVERVIEW.md`
- GoblinOS Assistant Core Identity: `apps/goblin-assistant/docs/CORE_IDENTITY.md`
- Repository docs: `docs/` (top-level canonical docs)

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

## Documentation System

Complete documentation pipeline with AI analysis, diagram generation, and CI validation.

### Setup

```bash
# Install dependencies
pip install frontmatter click requests
npm install -g markdownlint-cli markdown-link-check prettier @mermaid-js/mermaid-cli

# Configure Raptor Mini (Colab deployment)
cp .env.example .env
# Edit .env with your Colab Raptor endpoint URL
```

### Usage

```bash
# Create new document
python scripts/doc_cli.py new docs/my-feature.md --type feature

# Validate document
python scripts/doc_cli.py validate docs/my-feature.md

# Generate diagrams from code comments
python scripts/doc_cli.py diagrams apps/my-app/src/

# AI analysis with Colab-deployed Raptor Mini
python scripts/doc_cli.py analyze docs/my-feature.md --url https://your-colab-endpoint.ngrok.io

# Full audit
python scripts/doc_cli.py audit docs/
```

### Features

- **Standardized Templates**: Frontmatter-based document structure
- **AI Quality Analysis**: Raptor Mini integration for scoring and suggestions
- **Automatic Diagrams**: Mermaid diagram extraction and rendering from code
- **CI/CD Validation**: GitHub Actions for automated quality checks
- **Resource Efficient**: Uses Colab-deployed Raptor Mini instead of local Ollama

## Onboarding

- Start with `docs/WORKSPACE_OVERVIEW.md` for structure and conventions.
- Follow `docs/ONBOARDING_TARIQ.md` for step-by-step setup to contribute to GoblinOS.
- See `CONTRIBUTING.md` for branch/PR standards and local checks.

## Notes

- Legacy demos may have shipped with their own `.git` history—these should be promoted into `apps/` or converted to submodules. See `docs/WORKSPACE_OVERVIEW.md` for guidance.

**Active Projects**: GoblinOS Assistant
