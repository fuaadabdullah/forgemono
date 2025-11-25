#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKFLOWS_DIR="$REPO_ROOT/.github/workflows"
BACKUP_DIR="$REPO_ROOT/.github/workflows/backups"

mkdir -p "$BACKUP_DIR"

if [ ! -d "$WORKFLOWS_DIR" ]; then
  echo "No GitHub workflows directory found at $WORKFLOWS_DIR"
  exit 0
fi

for file in "$WORKFLOWS_DIR"/*.yml "$WORKFLOWS_DIR"/*.yaml; do
  [ -e "$file" ] || continue
  echo "Processing $file"
  cp "$file" "$BACKUP_DIR/$(basename "$file").bak"
  # Comment out any lines containing 'forge-lite' or 'apps/forge-lite'
  awk '{ if (tolower($0) ~ /forge-lite/ ) { print "# " $0 } else { print $0 } }' "$file" > "$file.tmp"
  mv "$file.tmp" "$file"
  echo "Updated $file (backup saved)"
done

echo "Workflow modification complete."
