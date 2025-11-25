#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Refreshing workspace..."

if ! command -v pnpm >/dev/null 2>&1; then
  echo "pnpm not found. Please install pnpm to continue."
  exit 1
fi

cd "$REPO_ROOT"

echo "Installing workspace dependencies with pnpm..."
pnpm install

if [ -f "$REPO_ROOT/GoblinOS/scripts/generate-roles.js" ]; then
  echo "Regenerating GoblinOS roles from YAML..."
  node "$REPO_ROOT/GoblinOS/scripts/generate-roles.js"
else
  echo "No GoblinOS role generation script found; skipping."
fi

echo "Running workspace build (if applicable)..."
pnpm -w build || echo "Workspace build failed or no build script defined."

echo "Workspace refresh complete."
