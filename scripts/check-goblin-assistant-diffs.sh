#!/usr/bin/env bash
set -euo pipefail

# Script: scripts/check-goblin-assistant-diffs.sh
# Purpose: Print differences between root `goblin-assistant/` and `apps/goblin-assistant/`.
# - Excludes common noisy directories like node_modules, .git, venv, __pycache__
# - Outputs 3 files under /tmp for manual review:
#   - /tmp/goblin_root_filelist.txt
#   - /tmp/goblin_apps_filelist.txt
#   - /tmp/goblin_basename_conflicts.txt

ROOT_DIR="goblin-assistant"
APPS_DIR="apps/goblin-assistant"
TMP_ROOT="/tmp/goblin_root_filelist.txt"
TMP_APPS="/tmp/goblin_apps_filelist.txt"
TMP_ROOT_BASENAME="/tmp/goblin_root_basenames.txt"
TMP_APPS_BASENAME="/tmp/goblin_apps_basenames.txt"
TMP_CONFLICTS="/tmp/goblin_basename_conflicts.txt"

echo "Scanning: $ROOT_DIR -> $APPS_DIR"

find "$ROOT_DIR" -type f \
  -not -path "*/node_modules/*" \
  -not -path "*/.git/*" \
  -not -path "*/venv/*" \
  -not -path "*/.venv/*" \
  -not -path "*/__pycache__/*" \
  | sort > "$TMP_ROOT"

find "$APPS_DIR" -type f \
  -not -path "*/node_modules/*" \
  -not -path "*/.git/*" \
  -not -path "*/venv/*" \
  -not -path "*/.venv/*" \
  -not -path "*/__pycache__/*" \
  | sort > "$TMP_APPS"

echo "Counts:"
wc -l "$TMP_ROOT" || true
wc -l "$TMP_APPS" || true

awk -F/ '{print $NF}' "$TMP_ROOT" | sort | uniq > "$TMP_ROOT_BASENAME"
awk -F/ '{print $NF}' "$TMP_APPS" | sort | uniq > "$TMP_APPS_BASENAME"

echo "Conflicting file basenames (present in both):"
comm -12 "$TMP_ROOT_BASENAME" "$TMP_APPS_BASENAME" | tee "$TMP_CONFLICTS"

echo
echo "Unique to root goblin-assistant (by basename):"
comm -23 "$TMP_ROOT_BASENAME" "$TMP_APPS_BASENAME" | sed -n '1,200p'

echo
echo "Unique to apps/goblin-assistant (by basename):"
comm -13 "$TMP_ROOT_BASENAME" "$TMP_APPS_BASENAME" | sed -n '1,200p'

echo
echo "Detailed file lists saved to:"
echo "  $TMP_ROOT"
echo "  $TMP_APPS"
echo "  $TMP_CONFLICTS"

exit 0
