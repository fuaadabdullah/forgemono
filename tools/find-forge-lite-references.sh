#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$REPO_ROOT/tools/forge-lite-references.txt"

echo "Searching for 'forge-lite' references across the repository..."

# Use ripgrep if available, fall back to grep
if command -v rg >/dev/null 2>&1; then
  rg --hidden --no-ignore --line-number "forge-lite" "$REPO_ROOT" || true
  rg --hidden --no-ignore --line-number "forge-lite" "$REPO_ROOT" > "$OUT" || true
else
  grep -R --line-number --exclude-dir=.git --exclude-dir=node_modules "forge-lite" "$REPO_ROOT" | tee "$OUT" || true
fi

if [ -s "$OUT" ]; then
  echo "References saved to $OUT"
else
  echo "No references found. $OUT is empty."
fi
