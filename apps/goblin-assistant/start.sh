#!/usr/bin/env bash
set -euo pipefail

echo "[$(date --iso-8601=seconds)] Starting Goblin backend entrypoint"
# Print a quick directory listing and python path for debugging
echo "Working dir: $(pwd)"
ls -la /app || true
if [ -d /app/backend ]; then
  echo "backend directory exists"
  ls -la /app/backend || true
else
  echo "WARNING: /app/backend not found"
fi
python -c 'import sys; print("PYTHONPATH:", sys.path)'
python -c 'import importlib, pkgutil; print("Installed packages sample:", [p.name for p in pkgutil.iter_modules()][:10])'

# Start uvicorn with the expected import
# NOTE: this uses uvicorn backend.main:app — change if your package name differs
cd /app
exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8001}
