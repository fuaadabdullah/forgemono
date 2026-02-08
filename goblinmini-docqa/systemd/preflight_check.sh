#!/usr/bin/env bash
set -euo pipefail

echo "Running preflight checks for Goblin DocQA systemd deployment"

function check_systemd() {
  if ! command -v systemctl >/dev/null 2>&1; then
    echo "Error: systemctl not available. This host is not running systemd or not a Linux host." 1>&2
    exit 1
  fi
}

function check_venv() {
  if [[ ! -x "/opt/goblinmini-docqa/venv/bin/uvicorn" ]]; then
    echo "Warning: /opt/goblinmini-docqa/venv/bin/uvicorn not found. Ensure venv created or install uvicorn in system or venv." 1>&2
  else
    echo "OK: venv uvicorn found"
  fi
}

function check_user() {
  if ! id docqa >/dev/null 2>&1; then
    echo "Warning: user 'docqa' not found. The service expects an unprivileged 'docqa' user. Consider creating it with:"
    echo "  sudo useradd -r -s /bin/bash -m docqa"
  else
    echo "OK: user 'docqa' exists"
  fi
}

function check_envfile() {
  if [[ -f /etc/default/goblin-docqa ]]; then
    echo "OK: /etc/default/goblin-docqa exists"
  else
    echo "Warning: /etc/default/goblin-docqa not found. Create from systemd/goblin-docqa.env.example"
  fi
}

function check_local_inference() {
  PYTHON_BIN="/opt/goblinmini-docqa/venv/bin/python"
  if [[ ! -x "$PYTHON_BIN" ]]; then
    PYTHON_BIN="python3"
  fi

  # Read env settings
  MODEL_PATH="/models"
  MODEL_NAME=""
  DOCQA_ENABLE_LOCAL_MODEL=false
  if [[ -f /etc/default/goblin-docqa ]]; then
    source /etc/default/goblin-docqa
    # After source, variables may be set; fall back safely
    MODEL_PATH="${MODEL_PATH:-$MODEL_PATH}"
    MODEL_NAME="${MODEL_NAME:-$MODEL_NAME}"
    DOCQA_ENABLE_LOCAL_MODEL="${DOCQA_ENABLE_LOCAL_MODEL:-false}"
  fi

  echo "Checking local inference tooling (llama-cpp or torch) using $PYTHON_BIN"
  if "$PYTHON_BIN" -c 'import importlib,sys; importlib.import_module("llama_cpp")' >/dev/null 2>&1; then
    echo "OK: llama-cpp-python import available"
  elif "$PYTHON_BIN" -c 'import importlib,sys; importlib.import_module("torch")' >/dev/null 2>&1; then
    echo "OK: PyTorch import available"
    # check numpy version
    NUMPY_VER=$($PYTHON_BIN -c 'import numpy as np; print(np.__version__)' 2>/dev/null || echo "")
    if [[ -n "$NUMPY_VER" ]]; then
      echo "numpy version: $NUMPY_VER (recommended: <2 for some torch setups)"
    fi
  else
    echo "Warning: No local inference runtime detected (neither llama-cpp nor torch)." 1>&2
    echo "If you intend to enable local models, install llama-cpp-python (recommended for CPU) or PyTorch (with numpy<2)."
  fi

  # If local model enabled, check model path exists and contains files
  if [[ "$DOCQA_ENABLE_LOCAL_MODEL" == "true" ]]; then
    if [[ -d "$MODEL_PATH" ]] && ls -1A "$MODEL_PATH" | grep -q "\.gguf$\|\.pt$\|\.bin$" || true; then
      echo "OK: Model files found in $MODEL_PATH"
    else
      echo "Warning: DOCQA_ENABLE_LOCAL_MODEL=true but no model files found in $MODEL_PATH" 1>&2
      echo "Place GGUF or compatible model files in $MODEL_PATH or set MODEL_PATH in /etc/default/goblin-docqa"
    fi
  fi
}

check_systemd
check_venv
check_user
check_envfile
check_local_inference

echo "Preflight check complete. Resolve any warnings before running deploy_units.sh"
