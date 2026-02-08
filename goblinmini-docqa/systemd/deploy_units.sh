#!/usr/bin/env bash
set -euo pipefail

# Deploy systemd unit files for Goblin DocQA
# Usage: sudo ./systemd/deploy_units.sh

SERVICE_DIR="/etc/systemd/system"
UNIT_FILES=(
  goblin-docqa.socket
  goblin-docqa.service
  goblin-docqa-worker.service
)
DROPINS_DIR="$(dirname "$0")/dropins"

function ensure_systemd() {
  if ! command -v systemctl >/dev/null 2>&1; then
    echo "systemctl not found on this machine. This script must be run on a Linux host with systemd."
    exit 1
  fi
}

function deploy_files() {
  echo "Deploying systemd unit files to ${SERVICE_DIR}"
  for uf in "${UNIT_FILES[@]}"; do
    src="$(dirname "$0")/$uf"
    if [[ ! -f "$src" ]]; then
      echo "Warning: unit file $src does not exist. Skipping." 1>&2
      continue
    fi
    echo "  -> copying $src to ${SERVICE_DIR}/$uf"
    cp "$src" "${SERVICE_DIR}/$uf"
    chmod 644 "${SERVICE_DIR}/$uf"
  done

  # Deploy drop-in files if present
  if [[ -d "$DROPINS_DIR" ]]; then
    echo "Deploying systemd drop-in files from $DROPINS_DIR"
    for df in "$DROPINS_DIR"/*.conf; do
      [[ -f "$df" ]] || continue
      base=$(basename -- "$df")
      # derive unit base name: goblin-docqa(-worker).conf -> goblin-docqa(.service)
      unit_key=$(echo "$base" | sed -E 's/-(timeout|startlimit)\.conf$//')
      unit_name="$unit_key.service"
      dst_dir="${SERVICE_DIR}/${unit_name}.d"
      mkdir -p "$dst_dir"
      echo "  -> copying drop-in $df to $dst_dir/$(basename $df)"
      cp "$df" "$dst_dir/$(basename "$df")"
      chmod 644 "$dst_dir/$(basename "$df")"
    done
  fi
}

function systemd_reload_enable() {
  echo "Reloading systemd daemon and enabling socket + services"
  systemctl daemon-reload
  # Always enable socket first (socket-activation style)
  systemctl enable --now goblin-docqa.socket
  # Now enable the service and worker
  systemctl enable --now goblin-docqa.service
  systemctl enable --now goblin-docqa-worker.service
}

function main() {
  ensure_systemd
  if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root (sudo)" 1>&2
    exit 1
  fi

  echo "Deploying Goblin DocQA systemd units"
  if [[ "${ENSURE_USER:-false}" == "true" ]]; then
    echo "Ensuring system user 'docqa' exists and setting ownership"
    if ! id docqa >/dev/null 2>&1; then
      echo "Creating user 'docqa'"
      useradd --system --shell /bin/bash --home-dir /opt/goblinmini-docqa --create-home docqa || true
    fi
    chown -R docqa:docqa /opt/goblinmini-docqa || true
  fi
  # Optionally create models dir
  if [[ "${ENSURE_MODELS_DIR:-false}" == "true" ]]; then
    echo "Ensuring models directory exists and setting ownership"
    mkdir -p /opt/goblinmini-docqa/models
    chown -R docqa:docqa /opt/goblinmini-docqa/models || true
  fi
  # Optionally install requirements in venv (idempotent - pip will skip if done)
  if [[ "${ENSURE_PIP_INSTALL:-false}" == "true" ]]; then
    VENV_BIN="/opt/goblinmini-docqa/venv/bin/python"
    if [[ -x "$VENV_BIN" ]]; then
      echo "Installing Python requirements into venv"
      sudo -u docqa $VENV_BIN -m pip install --upgrade pip
      sudo -u docqa $VENV_BIN -m pip install -r /opt/goblinmini-docqa/requirements.txt
    else
      echo "No venv found at $VENV_BIN, skipping pip install" 1>&2
    fi
  fi
  deploy_files
  systemd_reload_enable
  if [[ "${RUN_POST_DEPLOY_TEST:-false}" == "true" ]]; then
    POSTDEPLOY_SCRIPT="$(dirname "$0")/post_deploy_test.sh"
    if [[ -x "$POSTDEPLOY_SCRIPT" ]]; then
      echo "Running post-deploy tests..."
      chmod +x "$POSTDEPLOY_SCRIPT" || true
      chmod +x "$(dirname "$0")/llm_test.py" || true
      if [[ "${POST_DEPLOY_MODEL_NAME:-}" != "" ]]; then
        $POSTDEPLOY_SCRIPT --venv /opt/goblinmini-docqa/venv --socket /run/goblinmini-docqa.sock --model-name "$POST_DEPLOY_MODEL_NAME" --run-model-load || true
      else
        $POSTDEPLOY_SCRIPT --venv /opt/goblinmini-docqa/venv --socket /run/goblinmini-docqa.sock || true
      fi
    else
      echo "Post-deploy test script not found or not executable: $POSTDEPLOY_SCRIPT" 1>&2
    fi
  fi
  echo "Deployment finished. Check service status with: sudo systemctl status goblin-docqa.service"
}

main "$@"
