#!/usr/bin/env bash
set -euo pipefail

### Install llama-cpp-python into the venv and prepare model directory.
### Usage: sudo ./systemd/install_local_model.sh [--venv /opt/goblinmini-docqa/venv] [--user docqa] [--install-torch]

VENV_PATH="/opt/goblinmini-docqa/venv"
USER_NAME="docqa"
INSTALL_TORCH=false
MODELS_DIR="/opt/goblinmini-docqa/models"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --venv) VENV_PATH="$2"; shift 2;;
    --user) USER_NAME="$2"; shift 2;;
    --install-torch) INSTALL_TORCH=true; shift;;
    --models-dir) MODELS_DIR="$2"; shift 2;;
    -h|--help) echo "Usage: $0 [--venv path] [--user user] [--models-dir dir] [--install-torch]"; exit 0;;
    *) echo "Unknown arg: $1"; exit 1;;
  esac
done

if [[ ! -x "$VENV_PATH/bin/python" ]]; then
  echo "Error: Python venv not found at $VENV_PATH" 1>&2
  exit 1
fi

if ! id "$USER_NAME" >/dev/null 2>&1; then
  echo "User $USER_NAME does not exist, creating..."
  useradd --system --shell /bin/bash --home-dir /opt/goblinmini-docqa --create-home "$USER_NAME" || true
fi

echo "Using venv at $VENV_PATH, installing llama-cpp-python"
sudo -u "$USER_NAME" "$VENV_PATH/bin/python" -m pip install --upgrade pip
sudo -u "$USER_NAME" "$VENV_PATH/bin/python" -m pip install "llama-cpp-python"

if [[ "$INSTALL_TORCH" == "true" ]]; then
  echo "Installing PyTorch into venv (this can be heavy and platform-specific). Consider manual install for CUDA compatibility."
  sudo -u "$USER_NAME" "$VENV_PATH/bin/python" -m pip install "numpy<2" torch torchvision || true
fi

echo "Ensuring models dir exists and setting ownership"
mkdir -p "$MODELS_DIR"
chown -R "$USER_NAME":"$USER_NAME" "$MODELS_DIR"
chmod 750 "$MODELS_DIR"

echo "Installation complete. Place your GGUF or model weights in $MODELS_DIR and update /etc/default/goblin-docqa with MODEL_PATH, MODEL_NAME, DOCQA_ENABLE_LOCAL_MODEL=true"
