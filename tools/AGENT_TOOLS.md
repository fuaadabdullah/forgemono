---
description: "AGENT_TOOLS"
---

# Agent Tooling Quick Reference

This reference documents the tools agents should use in ForgeMonorepo. Prefer these over ad-hoc commands and route ownership through the guild that stewards each workflow. Guild metadata, LiteBrain routing, and toolbelt assignments now live in `goblins.yaml` and are served programmatically via `@goblinos/registry`.

All guilds report to **Overmind**. Guild masters are the first line of escalation; unresolved blockers, KPI breaches, or cross-guild work must be raised to Overmind with telemetry attached.

## Guild Tool Ownership Matrix

 | Tool | Purpose / When to Run | Guild | Primary Goblin | 
 | --- | --- | --- | --- | 
 | `pnpm forge-guild <command>` | Core forge automation (doctor/check/biome/deps/secrets) | Forge | Dregg Embercode | 
 | `pnpm -C GoblinOS crafters-guild <command>` | Unified UI/backend command surface (guard, deploy, maintain) | Crafters | Vanta Lumin / Volt Furnace | 
 | `pnpm -C GoblinOS huntress-guild <command>` | Smoke probes and signal-scouting orchestration | Huntress | Magnolia Nightbloom | 
 | `pnpm -C GoblinOS keepers-guild <command>` | Secrets, compliance, and storage hygiene playbooks | Keepers | Sentenial Ledgerwarden | 
 | `pnpm -C GoblinOS mages-guild <command>` | Quality gate + vault validation automation | Mages | Launcey Gauge / Hex Oracle | 
 | `tools/scripts/kill-port.sh <port>` | Break-glass: clear hung dev servers fast | Forge | Dregg Embercode | 
 | `backend/scripts/config_backend.sh` | Update/manage ForgeTM backend `.env` values | Crafters | Volt Furnace | 
 | `backend/scripts/deploy_backend.sh [local | docker]` | Deploy ForgeTM backend with env checks & migrations | Crafters | Volt Furnace | 
 | `backend/scripts/maintain_backend.sh <task>` | Backups, migrations, cache/log cleanup for backend | Crafters | Volt Furnace | 
 | `tools/scripts/ensure-pnpm.sh` | Frontend guard: verify pnpm present before builds | Crafters | Vanta Lumin | 
 | `tools/smoke.sh` | Kubecost / platform smoke probe | Huntress | Magnolia Nightbloom | 
 | `tools/lint_all.sh` | Monorepo lint umbrella (Biome, mypy, security) | Mages | Launcey Gauge | 
 | `tools/validate_forge_vault.sh` | Obsidian vault sanity (dashboards, templates) | Mages | Hex Oracle | 
 | `tools/api_keys_check.sh` | Ensure `.env.example` + docs list required secrets | Keepers | Sentenial Ledgerwarden | 
 | `tools/security_check.sh` | Verify Trivy/Cosign/SOPS tooling & scan Dockerfiles | Keepers | Sentenial Ledgerwarden | 
 | `tools/secrets_manage.sh` | Smithy secret handling playbook | Keepers | Sentenial Ledgerwarden | 
 | `tools/disk_consolidation.sh` | Backup + disk resize checklist | Keepers | Sentenial Ledgerwarden | 
 | `tools/space_saver.sh` | Archive heavy caches / venvs to external storage | Keepers | Sentenial Ledgerwarden | 
 | `tools/system_clean.sh` | System-level cache purge with archival safety | Keepers | Sentenial Ledgerwarden | 
 | `tools/storage_cleanup.sh` | Lightweight weekly cache cleanup | Keepers | Sentenial Ledgerwarden | 
 | `tools/mac-undervolt.sh` | Safe temporary CPU undervolting for Intel Macs (requires VoltageShift) | Keepers | Sentenial Ledgerwarden | 
 | `tools/setup-voltageshift.sh` | Downloads and builds VoltageShift for mac-undervolt.sh | Keepers | Sentenial Ledgerwarden | 

## Forge Guild – Dregg Embercode

Run from repo root unless noted.

- `pnpm forge-guild doctor` — environment diagnostics
- `pnpm forge-guild check` — Biome auto‑fix (write/unsafe) + clean pass + `pip check`
- `pnpm forge-guild biome-check | fix | format | imports` — code hygiene in `GoblinOS/`
- `pnpm forge-guild deps update | resolve | audit | sync` — Python deps for `ForgeTM/apps/backend`
- `pnpm forge-guild secrets …` — secret ops (delegates to Python automation)

Environment

- `FORGE_GUILD_PYTHON` — optional, preferred Python (e.g., `python3.11`)
- `tools/scripts/kill-port.sh <port>` — emergency stop for runaway services during break-glass fixes

## Crafters Guild – Vanta Lumin & Volt Furnace

- **CLI**: `pnpm -C GoblinOS crafters-guild --help`
- **Vanta Lumin (frontend)**: `tools/scripts/ensure-pnpm.sh` guards UI builds; pair with Biome commands above for styling.
- **Volt Furnace (backend sockets/schemas)**:
  - `backend/scripts/config_backend.sh` — edit & validate ForgeTM backend configuration
  - `backend/scripts/deploy_backend.sh [local | docker]` — provision app, migrations, Docker workflow refresh
  - `backend/scripts/maintain_backend.sh <db_backup | db_migrate | cleanup_cache | ...>` — lifecycle/backup utilities

## Huntress Guild – Magnolia Nightbloom

- **CLI**: `pnpm -C GoblinOS huntress-guild --help`
- `tools/smoke.sh` — Kubecost/cluster smoke probe; logs incidents to router audit if availability drops.

## Keepers Guild – Sentenial Ledgerwarden

- **CLI**: `pnpm -C GoblinOS keepers-guild --help`
- `tools/api_keys_check.sh` — verifies `.env.example`, `Obsidian/API_KEYS_MANAGEMENT.md`, and `.gitignore` hygiene
- `tools/security_check.sh` — confirms Trivy/Cosign/SOPS/age install and scans Docker artifacts
- `tools/secrets_manage.sh` — smithy usage primer for secrets
- `tools/disk_consolidation.sh` / `tools/space_saver.sh` / `tools/system_clean.sh` / `tools/storage_cleanup.sh` — storage hygiene playbook (archive then prune caches/venvs)

## Mages Guild – Hex Oracle, Grim Rune, Launcey Gauge

- **CLI**: `pnpm -C GoblinOS mages-guild --help`
- `tools/lint_all.sh` — Launcey’s monorepo quality gate (Biome, security, backend lint hooks)
- `tools/validate_forge_vault.sh` — Hex ensures knowledge vault dashboards, templates, and templater scripts stay intact
- Pair with `pnpm forge-guild biome-*` (for command details see Forge section) when closing regressions.

## Overmind Dashboard (Guild UI)

```bash
pnpm -C GoblinOS/packages/goblins/overmind/dashboard dev
# .env.local
VITE_API_URL=http://127.0.0.1:8000
VITE_GOBLINS_CONFIG=../../../../goblins.yaml
```yaml

Routes: `/forge`, `/crafters`, `/huntress`, `/keepers`, `/mages`.

## Bridge / Service Endpoints

- Forge Guild Admin via bridge (dev): `POST http://localhost:3030/forge-guild/{doctor | bootstrap | sync-config | check}`
- Router audit: `POST /v1/router-audit`, `GET /v1/router-audit`

## Model Routing (LiteBrain)

- Code gen/refactor → `ollama-coder`, escalate `deepseek-r1` on complexity
- Reasoning/forecast → `deepseek-r1` primary; `openai` fallback; `gemini` exploratory
- UI copy/micro‑UX → `openai`, then `gemini`
- RAG over ForgeVault → `nomic-embed-text` + rerank; cite sources strictly

Log router decisions to `goblinos.overmind.router-audit`. If it’s not logged, it didn’t happen.

## Secrets

- Never hardcode secrets. Use env vars or Vault.
- Keep `.env.example` in sync and run `pnpm forge-guild check` / `tools/api_keys_check.sh` to verify.

## Confirmation Checklist

- [ ] Dregg Embercode: review Forge section & new VS Code task `🔥 Dregg: kill port 8000`
- [ ] Vanta Lumin: confirm frontend guard usage (`ensure-pnpm.sh`) and add notes if additional UI tasks needed
- [ ] Volt Furnace: run `⚙️ Volt: backend config wizard`, `🚀 Volt: backend deploy (local)`, `🧰 Volt: backend full check` to validate workflow coverage
- [ ] Magnolia Nightbloom: run `🎯 Magnolia: Kubecost smoke test` to confirm Huntress coverage
- [ ] Sentenial Ledgerwarden: execute `🛡️` tasks (API audit / security / storage) and update secrets playbook if gaps remain
- [ ] Hex Oracle / Grim Rune / Launcey Gauge: ensure `🧙 Mages: lint all` plus vault validation cover quality gates; note follow-ups in Mages runbook
