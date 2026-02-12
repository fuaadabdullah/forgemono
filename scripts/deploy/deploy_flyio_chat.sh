#!/bin/bash
# Deploy Goblin Chat Backend to Fly.io
#
# Deploys a lightweight always-on chat service using TinyLlama.
# This provides fallback inference when cloud providers are unavailable.
#
# Usage:
#   ./deploy_flyio_chat.sh [--setup|--deploy|--download-model]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${SCRIPT_DIR}/../../apps/goblin-assistant"
FLY_CONFIG="${APP_DIR}/fly.chat.toml"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

# Model configuration
MODEL_NAME="TinyLlama-1.1B-Chat-v1.0.Q4_K_M.gguf"
MODEL_URL="https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/${MODEL_NAME}"
MODEL_SIZE="668M"

check_prerequisites() {
    log_step "Checking prerequisites..."
    
    if ! command -v flyctl &> /dev/null; then
        log_error "Fly.io CLI not found. Install from: https://fly.io/docs/getting-started/installing-flyctl/"
        exit 1
    fi
    
    if ! flyctl auth whoami &> /dev/null; then
        log_warn "Not logged in to Fly.io"
        log_info "Running: flyctl auth login"
        flyctl auth login
    fi
    
    log_info "Prerequisites OK"
}

setup_app() {
    log_step "Setting up Fly.io app..."
    
    cd "$APP_DIR"
    
    # Check if app exists
    if flyctl apps list | grep -q "goblin-chat"; then
        log_info "App 'goblin-chat' already exists"
    else
        log_info "Creating app 'goblin-chat'..."
        flyctl apps create goblin-chat --org personal
    fi
    
    # Create volume for model storage
    if flyctl volumes list -a goblin-chat | grep -q "models"; then
        log_info "Volume 'models' already exists"
    else
        log_info "Creating volume 'models'..."
        flyctl volumes create models --size 3 --region iad -a goblin-chat
    fi
    
    log_info "App setup complete"
}

download_model() {
    log_step "Downloading TinyLlama model..."
    
    local model_dir="${APP_DIR}/models"
    mkdir -p "$model_dir"
    
    if [[ -f "${model_dir}/${MODEL_NAME}" ]]; then
        log_info "Model already downloaded"
        return
    fi
    
    log_info "Downloading ${MODEL_NAME} (${MODEL_SIZE})..."
    curl -L -o "${model_dir}/${MODEL_NAME}" "$MODEL_URL"
    
    log_info "Model downloaded to ${model_dir}/${MODEL_NAME}"
}

set_secrets() {
    log_step "Setting secrets..."
    
    # Check for .env file
    if [[ -f "${APP_DIR}/.env" ]]; then
        log_info "Loading secrets from .env"
        
        # Read specific keys
        local openai_key
        openai_key=$(grep "^OPENAI_API_KEY=" "${APP_DIR}/.env" | cut -d= -f2 || echo "")
        
        local goblin_key
        goblin_key=$(grep "^GOBLIN_API_KEY=" "${APP_DIR}/.env" | cut -d= -f2 || echo "")
        
        if [[ -n "$openai_key" && "$openai_key" != "sk-..." ]]; then
            flyctl secrets set OPENAI_API_KEY="$openai_key" -a goblin-chat
            log_info "Set OPENAI_API_KEY"
        fi
        
        if [[ -n "$goblin_key" ]]; then
            flyctl secrets set GOBLIN_API_KEY="$goblin_key" -a goblin-chat
            log_info "Set GOBLIN_API_KEY"
        fi
    else
        log_warn "No .env file found. Set secrets manually:"
        log_warn "  flyctl secrets set OPENAI_API_KEY=sk-... -a goblin-chat"
        log_warn "  flyctl secrets set GOBLIN_API_KEY=your-key -a goblin-chat"
    fi
}

deploy_app() {
    log_step "Deploying to Fly.io..."
    
    cd "$APP_DIR"
    
    # Use the chat-specific config
    flyctl deploy --config fly.chat.toml --dockerfile Dockerfile.chat --remote-only
    
    log_info "Deployment complete!"
    log_info "App URL: https://goblin-chat.fly.dev"
}

upload_model() {
    log_step "Uploading model to Fly.io volume..."
    
    local model_path="${APP_DIR}/models/${MODEL_NAME}"
    
    if [[ ! -f "$model_path" ]]; then
        log_error "Model not found. Run: $0 --download-model"
        exit 1
    fi
    
    # Use flyctl SSH to copy model
    log_info "This may take a few minutes..."
    
    # Create a small container to upload the model
    flyctl ssh console -a goblin-chat -C "mkdir -p /app/models"
    
    # Use sftp to upload
    flyctl sftp shell -a goblin-chat << EOF
put ${model_path} /app/models/${MODEL_NAME}
EOF
    
    log_info "Model uploaded successfully"
}

show_status() {
    log_step "App Status"
    
    flyctl status -a goblin-chat
    
    echo ""
    log_info "Endpoints:"
    echo "  Health: https://goblin-chat.fly.dev/health"
    echo "  Chat:   https://goblin-chat.fly.dev/v1/chat/completions"
    echo "  Models: https://goblin-chat.fly.dev/v1/models"
}

show_logs() {
    flyctl logs -a goblin-chat
}

show_help() {
    cat << EOF
Goblin Chat Backend - Fly.io Deployment

Usage: $0 [command]

Commands:
  setup           Create app and volume
  download-model  Download TinyLlama GGUF model
  secrets         Set secrets from .env
  deploy          Build and deploy to Fly.io
  upload-model    Upload model to volume
  status          Show app status
  logs            View app logs
  full            Run complete setup + deploy
  
Examples:
  # First time setup
  $0 setup
  $0 download-model
  $0 secrets
  $0 deploy
  
  # Redeploy after changes
  $0 deploy
  
  # Full setup (first time)
  $0 full
EOF
}

main() {
    case "${1:-help}" in
        setup)
            check_prerequisites
            setup_app
            ;;
        download-model)
            download_model
            ;;
        secrets)
            check_prerequisites
            set_secrets
            ;;
        deploy)
            check_prerequisites
            deploy_app
            ;;
        upload-model)
            check_prerequisites
            upload_model
            ;;
        status)
            check_prerequisites
            show_status
            ;;
        logs)
            check_prerequisites
            show_logs
            ;;
        full)
            check_prerequisites
            setup_app
            download_model
            set_secrets
            deploy_app
            show_status
            ;;
        *)
            show_help
            ;;
    esac
}

main "$@"
