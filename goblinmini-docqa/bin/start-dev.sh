#!/usr/bin/env bash
set -euo pipefail

# Development startup script for Goblin DocQA
# Binds to TCP port 8000 for local development and testing

LOCKFILE="/tmp/goblin-docqa-dev.lock"
PIDFILE="/tmp/goblin-docqa-dev.pid"
APP_CMD="uvicorn app.server:app --host 0.0.0.0 --port 9000 --workers 1 --log-level info"

# Create lock dir if needed
mkdir -p "$(dirname "$LOCKFILE")"

# Simple lock check (macOS compatible)
if [ -f "$LOCKFILE" ]; then
  LOCK_PID=$(cat "$LOCKFILE" 2>/dev/null || echo "")
  if [ -n "$LOCK_PID" ] && kill -0 "$LOCK_PID" 2>/dev/null; then
    echo "Another development instance is running (PID: $LOCK_PID). Exiting." >&2
    exit 1
  else
    echo "Cleaning up stale lock file"
    rm -f "$LOCKFILE"
  fi
fi

# Write PID to lock file
echo $$ > "$LOCKFILE"
trap 'rm -f "$PIDFILE" "$LOCKFILE"; exit' EXIT INT TERM

echo "Starting Goblin DocQA in development mode on http://localhost:8000"
echo "Metrics available at: http://localhost:8000/metrics"
echo "Press Ctrl+C to stop"

# Start the app
exec $APP_CMD
