#!/usr/bin/env bash
set -euo pipefail

# List the full paths for each basename conflict between root and apps goblin-assistant
TMP_CONFLICTS="/tmp/goblin_basename_conflicts.txt"

if [[ ! -f "$TMP_CONFLICTS" ]]; then
  echo "Conflict file $TMP_CONFLICTS not found. Run scripts/check-goblin-assistant-diffs.sh first."
  exit 1
fi

while read -r filename; do
  echo "\n== CONFLICT: $filename =="
  echo "Root occurrences:"; grep -RIn --line-number -- "\b$filename\b" goblin-assistant/ || true
  echo "Apps occurrences:"; grep -RIn --line-number -- "\b$filename\b" apps/goblin-assistant/ || true
done < "$TMP_CONFLICTS"

exit 0
