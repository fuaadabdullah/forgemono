#!/usr/bin/env bash
set -euo pipefail

# Script: scripts/consolidate-goblin-assistant.sh
# Purpose: Merge unique files from root `goblin-assistant/` into `apps/goblin-assistant/` safely.
# Usage: Run locally, validate the conflict list before proceeding, then run this script.

ROOT_DIR="goblin-assistant"
APPS_DIR="apps/goblin-assistant"
BACKUP_DIR="goblin-assistant-legacy-backup-$(date +%Y%m%d)"

if [ ! -d "$ROOT_DIR" ]; then
  echo "Root directory '$ROOT_DIR' not found. Aborting."
  exit 1
fi

if [ ! -d "$APPS_DIR" ]; then
  echo "Apps directory '$APPS_DIR' not found. Aborting."
  exit 1
fi

echo "Running detection of conflicts and unique files..."
scripts/check-goblin-assistant-diffs.sh

echo
echo "The conflict list has been saved in /tmp/goblin_basename_conflicts.txt"
echo "Please review the file contents before proceeding (files with the same basename may still be different)."
read -p "Continue with copying unique (non-conflicting) files from $ROOT_DIR to $APPS_DIR? (y/N): " -r
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Aborting consolidation. No files were changed."
  exit 0
fi

DRY_RUN=0
if [[ ${1:-} == "--dry-run" ]]; then
  DRY_RUN=1
fi

echo "Copying unique files (non-existing in destination) with rsync..."
RSYNC_FLAGS=("-av" "--ignore-existing" "--exclude" "node_modules" "--exclude" ".git" "--exclude" "venv" "--exclude" ".venv" "--exclude" "__pycache__")
if [[ $DRY_RUN -eq 1 ]]; then
  RSYNC_FLAGS+=("--dry-run")
  echo "Dry-run mode enabled; no files will be changed."
fi

rsync "${RSYNC_FLAGS[@]}" "$ROOT_DIR/" "$APPS_DIR/"

if [[ $DRY_RUN -eq 0 ]]; then
  echo "Creating a backup of root $ROOT_DIR to $BACKUP_DIR"
  mv "$ROOT_DIR" "$BACKUP_DIR"
else
  echo "Dry-run: would backup root directory to $BACKUP_DIR"
fi

echo "Consolidation complete. Root directory moved to $BACKUP_DIR"
echo "Please manually inspect both directories and run the conflict resolution plan where required."

echo "To rollback, you can move $BACKUP_DIR back to \"$ROOT_DIR\" and remove transferred files from $APPS_DIR if needed."

exit 0
