#!/bin/bash
# Ollama Remote VM Deployment Script
# Automates installation, model setup, and service configuration on remote VMs

set -euo pipefail

# Configuration
TARGET_HOST=${TARGET_HOST:-}
REMOTE_USER=${REMOTE_USER:-ubuntu}
OLLAMA_MODELS=${OLLAMA_MODELS:-"qwen2.5:3b,deepseek-coder:1.3b,gemma:2b,phi3:3.8b"}
USE_DRIVE_BACKUP=${USE_DRIVE_BACKUP:-true}  # Default to Google Drive backup
CREDENTIALS_FILE=${CREDENTIALS_FILE:-"credentials.json"}
SYSTEMD_SERVICE=${SYSTEMD_SERVICE:-true}
EXPOSE_PORT=${EXPOSE_PORT:-11434}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_usage() {
    cat <<EOF
Usage: TARGET_HOST=<host> [OPTIONS] $0 [command]

Commands:
  manual      Show manual setup instructions (default)
  install     Automated installation via SSH
  models      Pull models on remote host
  service     Configure systemd service
  full        Complete deployment (install + models + service)
  health      Check remote Ollama health
  cleanup     Remove Ollama from remote host

Options:
  TARGET_HOST=<host>           Remote host (required)
  REMOTE_USER=<user>           SSH user (default: ubuntu)
  OLLAMA_MODELS=<models>       Comma-separated model list (default: qwen2.5:3b,deepseek-coder:1.3b,gemma:2b,phi3:3.8b)
  USE_DRIVE_BACKUP=true        Use Google Drive backup instead of manual pulls (default: true)
  CREDENTIALS_FILE=<file>      Path to Google credentials (default: credentials.json)
  SYSTEMD_SERVICE=true         Install systemd service (default: true)
  EXPOSE_PORT=<port>           Port to expose Ollama on (default: 11434)

Examples:
  # Full automated deployment with Google Drive backup (default)
  TARGET_HOST=1.2.3.4 $0 full

  # Manual model pulling instead
  TARGET_HOST=1.2.3.4 USE_DRIVE_BACKUP=false $0 full

  # Install with custom models
  TARGET_HOST=1.2.3.4 OLLAMA_MODELS="llama3:8b,codellama:7b" $0 full
EOF
}

check_dependencies() {
    if ! command -v ssh >/dev/null 2>&1; then
        log_error "ssh command not found. Please install OpenSSH client."
        exit 1
    fi

    if ! command -v scp >/dev/null 2>&1; then
        log_error "scp command not found. Please install OpenSSH client."
        exit 1
    fi
}

check_target_host() {
    if [ -z "$TARGET_HOST" ]; then
        log_error "TARGET_HOST is required"
        show_usage
        exit 1
    fi

    log_info "Testing SSH connection to $REMOTE_USER@$TARGET_HOST..."
    if ! ssh -o ConnectTimeout=10 -o BatchMode=yes "$REMOTE_USER@$TARGET_HOST" "echo 'SSH connection successful'" >/dev/null 2>&1; then
        log_error "Cannot connect to $REMOTE_USER@$TARGET_HOST via SSH"
        log_error "Please ensure:"
        log_error "  1. SSH key is set up for passwordless authentication"
        log_error "  2. The target host is reachable"
        log_error "  3. The remote user '$REMOTE_USER' exists"
        exit 1
    fi
    log_success "SSH connection verified"
}

install_ollama() {
    log_info "Installing Ollama on remote host..."

    ssh "$REMOTE_USER@$TARGET_HOST" bash -c "
        set -e
        echo 'Installing Ollama...'

        # Install Ollama
        if ! command -v ollama >/dev/null 2>&1; then
            curl -fsSL https://ollama.ai/install.sh | sh
            echo 'Ollama installed successfully'
        else
            echo 'Ollama already installed'
        fi

        # Create models directory
        mkdir -p ~/.ollama/models
        echo 'Models directory created'

        # Verify installation
        ollama --version
    "

    log_success "Ollama installation completed"
}

setup_models() {
    if [ "$USE_DRIVE_BACKUP" = "true" ]; then
        setup_drive_backup
    else
        pull_models_manually
    fi
}

setup_drive_backup() {
    log_info "Setting up Google Drive backup on remote host..."

    # Check if credentials file exists locally
    if [ ! -f "$CREDENTIALS_FILE" ]; then
        log_error "Credentials file '$CREDENTIALS_FILE' not found locally"
        log_error "Please ensure Google Drive credentials are available"
        exit 1
    fi

    # Copy credentials to remote host
    log_info "Copying credentials to remote host..."
    scp "$CREDENTIALS_FILE" "$REMOTE_USER@$TARGET_HOST:~/" || {
        log_error "Failed to copy credentials file"
        exit 1
    }

    # Copy setup script to remote host
    log_info "Copying setup script to remote host..."
    scp "$REPO_ROOT/setup_ollama_from_drive.py" "$REMOTE_USER@$TARGET_HOST:~/" || {
        log_error "Failed to copy setup script"
        exit 1
    }

    # Run setup on remote host
    ssh "$REMOTE_USER@$TARGET_HOST" bash -c "
        set -e
        echo 'Running Google Drive setup...'

        # Ensure Python is available
        if ! command -v python3 >/dev/null 2>&1; then
            echo 'Installing Python...'
            # Try different package managers
            if command -v apt-get >/dev/null 2>&1; then
                sudo apt-get update && sudo apt-get install -y python3 python3-pip
            elif command -v yum >/dev/null 2>&1; then
                sudo yum install -y python3 python3-pip
            elif command -v dnf >/dev/null 2>&1; then
                sudo dnf install -y python3 python3-pip
            else
                echo 'Could not install Python. Please install python3 manually.'
                exit 1
            fi
        fi

        # Install required packages
        python3 -m pip install --user google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client

        # Run the setup script
        python3 setup_ollama_from_drive.py
    "

    log_success "Google Drive backup setup completed"
}

pull_models_manually() {
    log_info "Pulling models manually on remote host..."
    log_info "Models to pull: $OLLAMA_MODELS"

    # Convert comma-separated list to array
    IFS=',' read -ra MODELS <<< "$OLLAMA_MODELS"

    for model in "${MODELS[@]}"; do
        model=$(echo "$model" | xargs)  # Trim whitespace
        log_info "Pulling model: $model"

        ssh "$REMOTE_USER@$TARGET_HOST" bash -c "
            set -e
            echo \"Pulling $model...\"
            ollama pull '$model'
            echo \"$model pulled successfully\"
        "
    done

    log_success "All models pulled successfully"
}

setup_systemd_service() {
    if [ "$SYSTEMD_SERVICE" != "true" ]; then
        log_info "Skipping systemd service setup (SYSTEMD_SERVICE=$SYSTEMD_SERVICE)"
        return
    fi

    log_info "Setting up systemd service for Ollama..."

    ssh "$REMOTE_USER@$TARGET_HOST" bash -c "
        set -e

        # Check if systemd is available
        if ! command -v systemctl >/dev/null 2>&1; then
            echo 'systemd not available, skipping service setup'
            exit 0
        fi

        # Create systemd service file
        cat > /tmp/ollama.service << 'EOF'
[Unit]
Description=Ollama AI Model Server
After=network.target

[Service]
Type=simple
User=$USER
Environment=OLLAMA_HOST=0.0.0.0:$EXPOSE_PORT
ExecStart=/usr/local/bin/ollama serve
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

        # Move to system location
        sudo mv /tmp/ollama.service /etc/systemd/system/
        sudo systemctl daemon-reload
        sudo systemctl enable ollama
        sudo systemctl start ollama

        echo 'Systemd service created and started'
    "

    log_success "Systemd service configured"
}

check_health() {
    log_info "Checking Ollama health on remote host..."

    # First check if Ollama process is running
    ssh "$REMOTE_USER@$TARGET_HOST" bash -c "
        if pgrep -f 'ollama serve' >/dev/null; then
            echo 'Ollama process is running'
        else
            echo 'Ollama process is not running'
            exit 1
        fi
    "

    # Check if the API is responding
    local ollama_url=\"http://$TARGET_HOST:$EXPOSE_PORT\"
    log_info \"Testing API endpoint: \$ollama_url/v1/models\"

    if curl -s --max-time 10 \"\$ollama_url/v1/models\" >/dev/null 2>&1; then
        log_success \"Ollama API is responding\"
    else
        log_warning \"Ollama API is not responding on port $EXPOSE_PORT\"
        log_warning \"This might be normal if running behind a reverse proxy or firewall\"
    fi

    # List installed models
    log_info \"Installed models:\"
    ssh \"$REMOTE_USER@$TARGET_HOST\" \"ollama list\" 2>/dev/null || echo \"Could not list models\"
}

cleanup_remote() {
    log_warning "This will remove Ollama and all models from the remote host"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ ! \$REPLY =~ ^[Yy]$ ]]; then
        log_info "Cleanup cancelled"
        exit 0
    fi

    log_info "Cleaning up Ollama from remote host..."

    ssh "$REMOTE_USER@$TARGET_HOST" bash -c "
        set -e

        # Stop and disable service if it exists
        if command -v systemctl >/dev/null 2>&1; then
            sudo systemctl stop ollama 2>/dev/null || true
            sudo systemctl disable ollama 2>/dev/null || true
            sudo rm -f /etc/systemd/system/ollama.service
            sudo systemctl daemon-reload
        fi

        # Kill any running ollama processes
        pkill -f 'ollama serve' || true

        # Remove Ollama installation
        rm -rf ~/.ollama
        rm -f ~/setup_ollama_from_drive.py
        rm -f ~/credentials.json

        # Remove binary (if installed via official script)
        sudo rm -f /usr/local/bin/ollama

        echo 'Ollama cleanup completed'
    "

    log_success "Remote cleanup completed"
}

show_manual_instructions() {
    cat <<EOF
== Manual Ollama Remote Deployment Instructions ==
Target: $REMOTE_USER@$TARGET_HOST

1. SSH into the VM:
   ssh $REMOTE_USER@$TARGET_HOST

2. Install Ollama:
   curl -fsSL https://ollama.ai/install.sh | sh

3. Create models directory:
   mkdir -p ~/.ollama/models

4. Set up models:
   # Copy credentials and setup script (default method)
   scp $CREDENTIALS_FILE $REMOTE_USER@$TARGET_HOST:~/
   scp $REPO_ROOT/setup_ollama_from_drive.py $REMOTE_USER@$TARGET_HOST:~/

   # On remote host:
   python3 setup_ollama_from_drive.py

    cat <<EOF

5. Start Ollama server:
   ollama serve &

6. Configure systemd service (optional):
   # Create /etc/systemd/system/ollama.service with appropriate content
   sudo systemctl enable ollama
   sudo systemctl start ollama

7. Configure backend:
   export OLLAMA_HOST="http://$TARGET_HOST:$EXPOSE_PORT"

8. Test connection:
   curl "http://$TARGET_HOST:$EXPOSE_PORT/v1/models"
EOF
}

# Main script logic
COMMAND=${1:-manual}

case "$COMMAND" in
    manual)
        check_dependencies
        [ -n "$TARGET_HOST" ] && check_target_host
        show_manual_instructions
        ;;
    install)
        check_dependencies
        check_target_host
        install_ollama
        ;;
    models)
        check_dependencies
        check_target_host
        setup_models
        ;;
    service)
        check_dependencies
        check_target_host
        setup_systemd_service
        ;;
    full)
        check_dependencies
        check_target_host
        install_ollama
        setup_models
        setup_systemd_service
        check_health
        log_success "Full deployment completed!"
        log_info "Backend configuration:"
        log_info "  export OLLAMA_HOST=\"http://$TARGET_HOST:$EXPOSE_PORT\""
        ;;
    health)
        check_dependencies
        check_target_host
        check_health
        ;;
    cleanup)
        check_dependencies
        check_target_host
        cleanup_remote
        ;;
    *)
        log_error "Unknown command: $COMMAND"
        show_usage
        exit 1
        ;;
esac
