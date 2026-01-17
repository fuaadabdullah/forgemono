#!/bin/sh
# husky
# v4.3.8 linux

# Hook created by Husky
#   https://typicode.github.io/husky/#/

# This file is automatically created by Husky
# It should not be edited manually

# For more information, see:
#   https://typicode.github.io/husky/#/

set -e

# Skip husky if HUSKY_SKIP_HOOKS is set
if [ "$HUSKY_SKIP_HOOKS" = "1" ]; then
  exit 0
fi

# Skip husky if HUSKY_SKIP_INIT is set
if [ "$HUSKY_SKIP_INIT" = "1" ]; then
  exit 0
fi

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Change to the repository root
cd "$(git rev-parse --show-toplevel)"

# Run the hook
HOOK_NAME=$(basename "$0" .sh)
HOOK_FILE="$SCRIPT_DIR/../$HOOK_NAME"
if [ -f "$HOOK_FILE" ]; then
  exec "$HOOK_FILE" "$@"
else
  echo "Hook file not found: $HOOK_FILE"
  exit 1
fi
