#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────
# gcp-llm.sh — Start / Stop / Status for GCP LLM servers
# ─────────────────────────────────────────────────────────────────
# Usage:
#   bash tools/gcp-llm.sh start        # Start both VMs + update Fly secrets
#   bash tools/gcp-llm.sh stop         # Stop both VMs (save $$$)
#   bash tools/gcp-llm.sh status       # Check VM & service health
#   bash tools/gcp-llm.sh start ollama # Start only Ollama VM
#   bash tools/gcp-llm.sh start llama  # Start only llama.cpp VM
#   bash tools/gcp-llm.sh restart      # Stop + Start both
# ─────────────────────────────────────────────────────────────────
set -euo pipefail

# ── Config ──────────────────────────────────────────────────────
PROJECT="goblin-assistant-479511"
ZONE="us-central1-a"
FLY_APP="goblin-backend"

OLLAMA_VM="goblin-ollama-server"
OLLAMA_PORT=11434

LLAMACPP_VM="goblin-llamacpp-server"
LLAMACPP_PORT=8000

# Resolve gcloud
GCLOUD="${GCLOUD:-}"
if [[ -z "$GCLOUD" ]]; then
  if command -v gcloud &>/dev/null; then
    GCLOUD="gcloud"
  elif [[ -x "$HOME/google-cloud-sdk/bin/gcloud" ]]; then
    GCLOUD="$HOME/google-cloud-sdk/bin/gcloud"
  else
    echo "❌ gcloud CLI not found. Install it or set GCLOUD=/path/to/gcloud"
    exit 1
  fi
fi

# ── Helpers ─────────────────────────────────────────────────────
_vm_status() {
  local vm="$1"
  $GCLOUD compute instances describe "$vm" \
    --zone="$ZONE" --project="$PROJECT" \
    --format="value(status)" 2>/dev/null || echo "NOT_FOUND"
}

_vm_ip() {
  local vm="$1"
  $GCLOUD compute instances describe "$vm" \
    --zone="$ZONE" --project="$PROJECT" \
    --format="value(networkInterfaces[0].accessConfigs[0].natIP)" 2>/dev/null || echo ""
}

_start_vm() {
  local vm="$1"
  local status
  status=$(_vm_status "$vm")
  if [[ "$status" == "RUNNING" ]]; then
    echo "  ✅ $vm already running"
  else
    echo "  ⏳ Starting $vm..."
    $GCLOUD compute instances start "$vm" \
      --zone="$ZONE" --project="$PROJECT" --quiet
    echo "  ✅ $vm started"
  fi
}

_stop_vm() {
  local vm="$1"
  local status
  status=$(_vm_status "$vm")
  if [[ "$status" == "TERMINATED" || "$status" == "STOPPED" ]]; then
    echo "  ✅ $vm already stopped"
  else
    echo "  ⏳ Stopping $vm..."
    $GCLOUD compute instances stop "$vm" \
      --zone="$ZONE" --project="$PROJECT" --quiet
    echo "  ✅ $vm stopped"
  fi
}

_wait_for_service() {
  local ip="$1" port="$2" name="$3" path="$4"
  local max_attempts=12  # 60s total
  local attempt=0

  echo "  ⏳ Waiting for $name at $ip:$port..."
  while (( attempt < max_attempts )); do
    if curl -s --connect-timeout 3 --max-time 5 "http://${ip}:${port}${path}" &>/dev/null; then
      echo "  ✅ $name is ready"
      return 0
    fi
    (( attempt++ ))
    sleep 5
  done
  echo "  ⚠️  $name did not respond after 60s (may still be loading)"
  return 1
}

_update_fly_secrets() {
  local ollama_ip="$1"
  local llamacpp_ip="$2"

  if ! command -v fly &>/dev/null; then
    echo "  ⚠️  fly CLI not found — update secrets manually:"
    [[ -n "$ollama_ip" ]] && echo "    OLLAMA_GCP_URL=http://${ollama_ip}:${OLLAMA_PORT}"
    [[ -n "$llamacpp_ip" ]] && echo "    LLAMACPP_GCP_URL=http://${llamacpp_ip}:${LLAMACPP_PORT}"
    return
  fi

  local args=()
  [[ -n "$ollama_ip" ]] && args+=("OLLAMA_GCP_URL=http://${ollama_ip}:${OLLAMA_PORT}")
  [[ -n "$llamacpp_ip" ]] && args+=("LLAMACPP_GCP_URL=http://${llamacpp_ip}:${LLAMACPP_PORT}")

  if [[ ${#args[@]} -gt 0 ]]; then
    echo "  ⏳ Updating Fly.io secrets..."
    fly secrets set "${args[@]}" -a "$FLY_APP" --stage
    echo "  ✅ Fly secrets staged (deploy to apply, or they apply on next deploy)"
  fi
}

# ── Commands ────────────────────────────────────────────────────
cmd_start() {
  local target="${1:-all}"
  echo "🚀 Starting GCP LLM servers..."

  local ollama_ip="" llamacpp_ip=""

  if [[ "$target" == "all" || "$target" == "ollama" ]]; then
    _start_vm "$OLLAMA_VM"
    ollama_ip=$(_vm_ip "$OLLAMA_VM")
    echo "  📍 Ollama IP: $ollama_ip"
  fi

  if [[ "$target" == "all" || "$target" == "llama" || "$target" == "llamacpp" ]]; then
    _start_vm "$LLAMACPP_VM"
    llamacpp_ip=$(_vm_ip "$LLAMACPP_VM")
    echo "  📍 Llama.cpp IP: $llamacpp_ip"
  fi

  # Wait for services to come online
  echo ""
  echo "🔍 Waiting for services to come online..."
  if [[ -n "$ollama_ip" ]]; then
    _wait_for_service "$ollama_ip" "$OLLAMA_PORT" "Ollama" "/api/tags" || true
  fi
  if [[ -n "$llamacpp_ip" ]]; then
    _wait_for_service "$llamacpp_ip" "$LLAMACPP_PORT" "llama.cpp" "/v1/models" || true
  fi

  # Update Fly.io secrets with new IPs
  echo ""
  echo "🔑 Updating Fly.io backend secrets..."
  _update_fly_secrets "$ollama_ip" "$llamacpp_ip"

  echo ""
  echo "✅ Done! GCP LLM servers are ready."
  echo ""
  echo "   Test with:"
  echo "   curl -X POST https://${FLY_APP}.fly.dev/api/generate \\"
  echo "     -H 'Content-Type: application/json' \\"
  echo "     -d '{\"prompt\":\"hello\",\"model\":\"gemma:2b\"}'"
}

cmd_stop() {
  local target="${1:-all}"
  echo "🛑 Stopping GCP LLM servers..."

  if [[ "$target" == "all" || "$target" == "ollama" ]]; then
    _stop_vm "$OLLAMA_VM"
  fi

  if [[ "$target" == "all" || "$target" == "llama" || "$target" == "llamacpp" ]]; then
    _stop_vm "$LLAMACPP_VM"
  fi

  echo ""
  echo "✅ Servers stopped. Cascade will fall through to cloud providers."
}

cmd_status() {
  echo "📊 GCP LLM Server Status"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  for vm in "$OLLAMA_VM" "$LLAMACPP_VM"; do
    local status ip port path label
    status=$(_vm_status "$vm")
    ip=$(_vm_ip "$vm")

    if [[ "$vm" == "$OLLAMA_VM" ]]; then
      port=$OLLAMA_PORT; path="/api/tags"; label="Ollama"
    else
      port=$LLAMACPP_PORT; path="/v1/models"; label="llama.cpp"
    fi

    printf "  %-25s " "$label ($vm)"
    if [[ "$status" == "RUNNING" ]]; then
      printf "VM: 🟢 RUNNING  IP: %-16s " "$ip"
      if curl -s --connect-timeout 3 --max-time 5 "http://${ip}:${port}${path}" &>/dev/null; then
        echo "Service: 🟢 UP"
      else
        echo "Service: 🔴 DOWN"
      fi
    else
      echo "VM: 🔴 $status"
    fi
  done

  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  # Show current Fly secrets
  if command -v fly &>/dev/null; then
    echo ""
    echo "  Current Fly.io secrets:"
    local ollama_digest llamacpp_digest
    ollama_digest=$(fly secrets list -a "$FLY_APP" 2>/dev/null | grep OLLAMA_GCP_URL | awk '{print $2}' || echo "not set")
    llamacpp_digest=$(fly secrets list -a "$FLY_APP" 2>/dev/null | grep LLAMACPP_GCP_URL | awk '{print $2}' || echo "not set")
    echo "    OLLAMA_GCP_URL  digest: $ollama_digest"
    echo "    LLAMACPP_GCP_URL digest: $llamacpp_digest"
  fi
}

cmd_restart() {
  local target="${1:-all}"
  cmd_stop "$target"
  echo ""
  cmd_start "$target"
}

# ── Main ────────────────────────────────────────────────────────
case "${1:-help}" in
  start)   cmd_start "${2:-all}" ;;
  stop)    cmd_stop "${2:-all}" ;;
  status)  cmd_status ;;
  restart) cmd_restart "${2:-all}" ;;
  *)
    echo "Usage: bash tools/gcp-llm.sh {start|stop|status|restart} [ollama|llama|all]"
    echo ""
    echo "Commands:"
    echo "  start   Start VM(s), wait for service, update Fly.io secrets"
    echo "  stop    Stop VM(s) to save costs"
    echo "  status  Show VM and service health"
    echo "  restart Stop then start VM(s)"
    echo ""
    echo "Targets:"
    echo "  all     Both Ollama and llama.cpp (default)"
    echo "  ollama  Only Ollama server"
    echo "  llama   Only llama.cpp server"
    exit 1
    ;;
esac
