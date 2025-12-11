#!/usr/bin/env bash
set -euo pipefail

LOCKFILE="/var/lock/goblinmini-docqa.lock"
PIDFILE="/var/run/goblinmini-docqa.pid"
# Prefer venv in /opt if present (production default), otherwise fallback to system uvicorn
VENV_BIN="/opt/goblinmini-docqa/venv/bin/uvicorn"
if [ -x "$VENV_BIN" ]; then
  APP_CMD="$VENV_BIN app.server:app --uds /run/goblinmini-docqa.sock --workers 1"
else
  APP_CMD="uvicorn app.server:app --uds /run/goblinmini-docqa.sock --workers 1"
fi

# create lock dir if needed
sudo mkdir -p "$(dirname "$LOCKFILE")"
sudo chown "$(id -u -n)" "$(dirname "$LOCKFILE")" || true

# use flock to ensure single instance
exec 9>>"$LOCKFILE"
if ! flock -n 9; then
  echo "Another instance is running (lock held). Exiting." >&2
  exit 1
fi

# write pid
echo $$ > "$PIDFILE"
trap 'rm -f "$PIDFILE"; flock -u 9; exit' EXIT INT TERM

# start the app
exec $APP_CMD
