#!/usr/bin/env bash
set -euo pipefail

# Small helper to start the ForgeTM backend with sanity checks.
# Run this from the repo root: bash ./tools/dev-backend.sh

# Move to backend dir
cd "$(dirname "$0")/.."
cd ForgeTM/apps/backend || { echo "Error: backend directory not found: ForgeTM/apps/backend"; exit 1; }

export PYTHONPATH=src

PY_CMD=""
if command -v python3 >/dev/null 2>&1; then
  PY_CMD=python3
elif command -v python >/dev/null 2>&1; then
  PY_CMD=python
else
  echo
  echo "Error: Python not found. Install Python 3.11+ and try again."
  exit 1
fi

if ! $PY_CMD -m uvicorn --help >/dev/null 2>&1; then
  echo
  echo "uvicorn not found in the selected Python environment ($PY_CMD). Attempting to install project requirements..."
  if $PY_CMD -m pip install -r requirements.txt >/dev/null 2>&1; then
    echo "requirements installed (attempt)."
  else
    echo "Attempt to install requirements failed; please install uvicorn manually: $PY_CMD -m pip install \"uvicorn[standard]\""
    exit 1
  fi
  # re-check
  if ! $PY_CMD -m uvicorn --help >/dev/null 2>&1; then
    echo
    echo "Error: uvicorn still not available after installing requirements. Install it manually: $PY_CMD -m pip install \"uvicorn[standard]\""
    exit 1
  fi
fi

echo "Starting backend: $PY_CMD -m uvicorn forge.main:app --reload --host 127.0.0.1 --port 8000"
exec $PY_CMD -m uvicorn forge.main:app --reload --host 127.0.0.1 --port 8000
