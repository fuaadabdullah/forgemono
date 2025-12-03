#!/usr/bin/env bash
set -euo pipefail

# Usage: ./colab_llamacpp_start.sh /path/to/model.gguf [threads] [port] [context]
MODEL_PATH=${1:-/content/drive/MyDrive/llama_models/tinyllama.gguf}
THREADS=${2:-4}
PORT=${3:-8080}
CONTEXT=${4:-2048}
MMAP=${5:-1}
CACHE_RAM=${6:-0}

# Derived directories
LOGDIR=${LOGDIR:-/content/llama_logs}
mkdir -p "$LOGDIR"

# Find the server binary (llama-server or main server)
if [ -x ./llama.cpp/llama-server ]; then
  SERVER_BIN=./llama.cpp/llama-server
elif [ -x ./llama.cpp/main ]; then
  # For older builds or if the server target is not separate
  SERVER_BIN=./llama.cpp/main
else
  echo "Could not find llama-server or main binary in ./llama.cpp. Build first with make." >&2
  exit 1
fi

# Start server with recommended options
MMAP_FLAG=""
if [ "$MMAP" -eq 1 ]; then
  MMAP_FLAG="--mmap"
fi

CACHE_FLAG=""
if [ "$CACHE_RAM" -ne 0 ]; then
  CACHE_FLAG="--cache-ram $CACHE_RAM"
fi

nohup $SERVER_BIN $MMAP_FLAG $CACHE_FLAG --model "$MODEL_PATH" --host 0.0.0.0 --port $PORT -c $CONTEXT --threads $THREADS > "$LOGDIR/llama_server.log" 2>&1 &

echo "Started llama-server ($SERVER_BIN) with model $MODEL_PATH on port $PORT using $THREADS threads; logs: $LOGDIR/llama_server.log"

echo "Use 'tail -f $LOGDIR/llama_server.log' to watch progress and `curl -X POST http://127.0.0.1:$PORT/completions -H 'Content-Type: application/json' -d '{\"prompt\":\"Test\", \"max_tokens\":32}'` to test."
