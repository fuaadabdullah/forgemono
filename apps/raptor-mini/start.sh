#!/usr/bin/env bash
set -euo pipefail
echo "[$(date --iso-8601=seconds)] Starting raptor-mini server"
echo "MODEL_NAME=${MODEL_NAME:-raptor-mini}"
echo "PORT=${PORT:-8080}"
echo "API_KEY set: ${API_KEY:+yes}"

# Check if Ollama is available and model exists
if command -v ollama &> /dev/null; then
    echo "Ollama found, checking model..."
    if ! ollama list | grep -q "${MODEL_NAME:-raptor-mini}"; then
        echo "WARNING: Model ${MODEL_NAME:-raptor-mini} not found in Ollama"
        echo "Run: ollama pull ${MODEL_NAME:-raptor-mini}"
    fi
else
    echo "WARNING: Ollama not found in PATH"
fi

exec uvicorn server.app:app --host 0.0.0.0 --port ${PORT}
