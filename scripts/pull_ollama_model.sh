#!/usr/bin/env bash
# Pull a local model via Ollama. Intended for developer machines.
# Usage: ./scripts/pull_ollama_model.sh [model_name]
# Default: raptor-mini
set -euo pipefail
MODEL_NAME=${1:-raptor-mini}

# Check if ollama is installed
if ! command -v ollama >/dev/null 2>&1; then
  cat <<'EOF'
Ollama CLI not found. Please install Ollama first:
  brew install ollama

If you can't install via brew, visit: https://ollama.com/docs/install
EOF
  exit 1
fi

# Pull the model
echo "Pulling model: ${MODEL_NAME}"
ollama pull "${MODEL_NAME}"

# Verify model is present
echo "Verifying the model is available locally"
if ollama list | grep -q "${MODEL_NAME}"; then
  echo "✅ Model ${MODEL_NAME} available locally"
else
  echo "⚠️  Model ${MODEL_NAME} not found in 'ollama list' output"
  exit 1
fi

echo "Done. You can now run the local Ollama server and use the model."

# Show example of how to run the local API via ollama or raptor-mini service
cat <<'EOF'
Example usage:

# Run the Ollama server (if using OCI/ollama)
# Ollama runs as a local server; if you installed via brew you can check 'ollama run <model>' and the server should be live.

# Example curl request
curl -X POST "http://localhost:11434/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{"model":"${MODEL_NAME}","messages":[{"role":"user","content":"Hello world"}]}'

# Or use the raptor-mini endpoint if using the raptor-mini service on 8080
curl -X POST "http://127.0.0.1:8080/v1/generate" -H "Content-Type: application/json" -d '{"prompt":"Hello world", "max_tokens":50}'
EOF
