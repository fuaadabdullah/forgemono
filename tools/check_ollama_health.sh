#!/usr/bin/env bash
# Simple check script for Ollama server health
set -euo pipefail

HOST=${1:-${OLLAMA_HOST:-http://127.0.0.1:11434}}
echo "Checking Ollama host: $HOST"

if [[ "$HOST" != http*://* ]]; then
  HOST="http://$HOST"
fi

echo "Fetching models from $HOST/v1/models"
curl -sS "$HOST/v1/models" | jq '.'

echo "If you see model listings above, the remote Ollama server is reachable."

exit 0
