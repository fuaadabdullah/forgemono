#!/usr/bin/env bash
# Create production .env from .env.example and open it for editing
set -e
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
EXAMPLE="$ROOT/apps/goblin-assistant/.env.example"
TARGET="$ROOT/.env.production"

if [ ! -f "$EXAMPLE" ]; then
  echo ".env.example not found at $EXAMPLE"
  exit 1
fi

cp -n "$EXAMPLE" "$TARGET"
echo "Created $TARGET (existing file preserved). Opening for edit..."
${EDITOR:-vi} "$TARGET"
echo "Remember: DO NOT commit .env.production. Use secrets manager / Bitwarden for production keys."
