#!/usr/bin/env bash

# Import infra artifacts into goblin-infra/projects/goblin-assistant/
# Usage: ./import_infra.sh --dry-run  (shows what would be copied)
#        ./import_infra.sh --apply    (copy files)

set -eo pipefail

DRY_RUN=true

usage() {
  echo "Usage: $0 [--dry-run|--apply]"
  exit 1
}

if [[ $1 == "--apply" ]]; then
  DRY_RUN=false
elif [[ $1 == "--dry-run" || -z $1 ]]; then
  DRY_RUN=true
else
  usage
fi

ROOT_DIR=$(cd "$(dirname "$0")/../../.." && pwd)
SRC_DIR="$ROOT_DIR/apps/goblin-assistant/infra"
DEST_DIR="$ROOT_DIR/goblin-infra/projects/goblin-assistant/infra"

mkdir -p "$DEST_DIR"

echo "Source: $SRC_DIR"
echo "Destination: $DEST_DIR"

FILES=(
  "$SRC_DIR/deployments"
  "$SRC_DIR/charts"
  "$SRC_DIR/overlays"
  "$SRC_DIR/gitops"
  "$SRC_DIR/observability"
  "$SRC_DIR/secrets"
)

for f in "${FILES[@]}"; do
  if [[ -e "$f" ]]; then
    if [[ "$DRY_RUN" == true ]]; then
      echo "DRY RUN: would copy $f -> $DEST_DIR/$(basename "$f")"
    else
      echo "Copying $f -> $DEST_DIR/$(basename "$f")"
      rsync -av --delete --exclude ".git" "$f" "$DEST_DIR/"
    fi
  fi
done

# Fly / Fly.toml / Terraform references
echo "\nCopying helper top-level infra files (fly.toml, deploy scripts)"
if [[ "$DRY_RUN" == true ]]; then
  echo "DRY RUN: would copy apps/goblin-assistant/fly.toml -> $ROOT_DIR/goblin-infra/projects/goblin-assistant/fly.toml"
  echo "DRY RUN: would copy apps/goblin-assistant/deploy-fly.sh -> $ROOT_DIR/goblin-infra/projects/goblin-assistant/deploy-fly.sh"
else
  cp -v "$ROOT_DIR/apps/goblin-assistant/fly.toml" "$ROOT_DIR/goblin-infra/projects/goblin-assistant/" 2>/dev/null || true
  cp -v "$ROOT_DIR/apps/goblin-assistant/deploy-fly.sh" "$ROOT_DIR/goblin-infra/projects/goblin-assistant/" 2>/dev/null || true
  cp -v "$ROOT_DIR/apps/goblin-assistant/deploy-backend.sh" "$ROOT_DIR/goblin-infra/projects/goblin-assistant/" 2>/dev/null || true
fi

if [[ "$DRY_RUN" == true ]]; then
  echo "\nDry-run complete. Use --apply to copy files. No files were modified."
else
  echo "\nImport complete. You should now update references in CI and apps/goblin-assistant/ to use goblin-infra/projects/goblin-assistant/ as the canonical infra repo."
fi

exit 0
