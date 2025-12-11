---title: Tools
type: reference
project: ForgeMonorepo
status: draft
owner: GoblinOS
description: "README"

---

Cross-repository scripts, generators, and utilities. Ownership per guild/goblin is tracked in `tools/AGENT_TOOLS.md` under the Guild Tool Ownership Matrix.

## Contents

- `lint_all.sh` - Run linters across all projects
- `mac-undervolt.sh` - Safe temporary undervolting tool for Intel Macs (requires VoltageShift)
- `setup-voltageshift.sh` - Downloads and sets up VoltageShift for mac-undervolt.sh
- `smoke.sh` - Health check for all services
- `forge-new/` - Scaffolding tool for new packages
- `templates/` - Reusable templates
- `vscode_cleanup.sh` - Helper to inspect/archive/remove local VS Code workspace/global storage and extensions (opt-in, conservative)
- `archive-forge-lite.sh` - Archive the apps/forge-lite directory and update workspace manifests.
- `refresh-workspace.sh` - Install dependencies, regenerate GoblinOS roles, and perform a workspace build.
- `find-forge-lite-references.sh` - Search the repo for all 'forge-lite' references and save them to tools/forge-lite-references.txt.
- `comment-out-forge-lite-in-workflows.sh` - Comment out any lines that reference 'forge-lite' in .github/workflows to prevent CI from running on archived content (backs up files).
- `safe-remove-forge-lite-references.sh` - Conservative, backup-first tool to comment out and/or sanitize remaining references in non-workflow files; review backups before committing.

## AI Tools

Specialized AI-powered tools for development automation and analysis.

### Documentation Quality (`doc-quality/`)
AI-powered documentation quality analysis and automated checking.

**Features:**

- Automated quality scoring using advanced language models
- CI/CD integration with quality gates
- Batch processing for large documentation sets
- Detailed reporting and improvement suggestions

**Quick Start:**

```bash
cd doc-quality
python3 doc_quality_check.py --ci --min-score 70
```

### Raptor Mini (`raptor-mini/`)
Lightweight AI analysis and diagnostics system.

**Features:**
- FastAPI-based document analysis API
- Local deployment with ngrok tunneling
- CPU/memory monitoring and exception tracing
- Google Colab integration for cloud deployment

**Quick Start:**
```bash

cd raptor-mini
python3 raptor_mini_local.py
```

## Usage

Scripts should be run from the repository root:

```bash
bash tools/lint_all.sh
bash tools/smoke.sh
```

### Mac Undervolting

The `mac-undervolt.sh` script provides a safe interface for temporary undervolting on Intel Macs using VoltageShift.

**Setup (one-time):**

```bash

# Download and build VoltageShift
bash tools/setup-voltageshift.sh
```

**Usage:**

```bash
# Interactive menu for safe undervolting
bash tools/mac-undervolt.sh
```

⚠️ **Safety Note**: This tool applies temporary undervolts that reset on reboot. Always test conservatively and monitor temperatures.

## Workspace Maintenance

This directory contains helper scripts for workspace maintenance.

### How to refresh the workspace

```bash

# From repo root
bash tools/refresh-workspace.sh
```

### How to archive Forge Lite (if not already done)

```bash
bash tools/archive-forge-lite.sh
```

If you need to reverse an archive, restore the files from Git history and re-add the workspace entries to pnpm-workspace.yaml/package.json.

### How to find and remove 'forge-lite' references

```bash

# Run the find script to generate a report
bash tools/find-forge-lite-references.sh

# Comment out forge-lite references in GitHub workflows (creates backups in .github/workflows/backups)
bash tools/comment-out-forge-lite-in-workflows.sh

# Optionally run the safe remove script to comment out references across repo (backups created per file)
bash tools/safe-remove-forge-lite-references.sh
```

Review backups before committing any changes.
