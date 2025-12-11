#!/bin/bash
# Kamatera LLM Infrastructure CLI Deployment Tool
# Complete automated deployment via SSH to both servers

set -e

# Configuration
SERVER1_IP="192.175.23.150"  # Inference Node (4 CPU, 24GB RAM)
SERVER2_IP="45.61.51.220"    # Router Node (2 CPU, 12GB RAM)
SSH_KEY_PATH="$HOME/.ssh/kamatera_raptor"
SSH_USER="root"
SSH_TIMEOUT="30"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
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

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if SSH key exists
    if [[ ! -f "$SSH_KEY_PATH" ]]; then
        log_error "SSH key not found at $SSH_KEY_PATH"
        log_info "Please ensure your SSH key is set up for Kamatera servers"
        log_info "Run: ssh-keygen -t rsa -b 4096 -f $SSH_KEY_PATH -C 'kamatera-deployment'"
        exit 1
    fi

    # Check if bootstrap scripts exist
    if [[ ! -f "bootstrap_inference.sh" ]]; then
        log_error "bootstrap_inference.sh not found in current directory"
        exit 1
    fi

    if [[ ! -f "bootstrap_router.sh" ]]; then
        log_error "bootstrap_router.sh not found in current directory"
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# Test SSH connection to server
test_ssh_connection() {
    local server_ip=$1
    local server_name=$2

    log_info "Testing SSH connection to $server_name ($server_ip)..."

    if ssh -i "$SSH_KEY_PATH" -o ConnectTimeout="$SSH_TIMEOUT" -o StrictHostKeyChecking=no -o PasswordAuthentication=no "$SSH_USER@$server_ip" "echo 'SSH connection successful'" 2>/dev/null; then
        log_success "SSH connection to $server_name successful"
        return 0
    else
        log_error "SSH connection to $server_name failed"
        log_info "Troubleshooting steps:"
        log_info "1. Ensure SSH key is added to server: ssh-copy-id -i $SSH_KEY_PATH $SSH_USER@$server_ip"
        log_info "2. Check if server is running: ping $server_ip"
        log_info "3. Verify firewall allows SSH: ufw allow ssh"
        return 1
    fi
}

# Run command on server with error handling
run_on_server() {
    local server_ip=$1
    local server_name=$2
    local command=$3
    local description=$4

    log_info "Running on $server_name: $description"

    if ssh -i "$SSH_KEY_PATH" -o ConnectTimeout="$SSH_TIMEOUT" -o StrictHostKeyChecking=no "$SSH_USER@$server_ip" "$command"; then
        log_success "Command completed successfully on $server_name"
    else
        log_error "Command failed on $server_name"
        return 1
    fi
}

# Copy file to server
copy_to_server() {
    local server_ip=$1
    local server_name=$2
    local file_path=$3
    local description=$4

    log_info "Copying $description to $server_name..."

    if scp -i "$SSH_KEY_PATH" -o ConnectTimeout="$SSH_TIMEOUT" -o StrictHostKeyChecking=no "$file_path" "$SSH_USER@$server_ip:~/$file_path"; then
        log_success "File copied successfully to $server_name"
    else
        log_error "Failed to copy file to $server_name"
        return 1
    fi
}

# Deploy bootstrap to server
deploy_bootstrap() {
    local server_ip=$1
    local server_name=$2
    local bootstrap_script=$3

    log_info "🚀 Starting bootstrap deployment on $server_name..."

    # Copy bootstrap script
    copy_to_server "$server_ip" "$server_name" "$bootstrap_script" "bootstrap script"

    # Make executable and run
    run_on_server "$server_ip" "$server_name" "chmod +x $bootstrap_script && ./$bootstrap_script" "bootstrap script execution"

    log_success "Bootstrap deployment completed on $server_name"
}

# Configure inference services
configure_inference_services() {
    local server_ip=$1
    local server_name=$2

    log_info "🔧 Configuring inference services on $server_name..."

    # Install Ollama
    run_on_server "$server_ip" "$server_name" "curl -fsSL https://ollama.ai/install.sh | sh" "Ollama installation"

    # Install rclone
    run_on_server "$server_ip" "$server_name" "curl https://rclone.org/install.sh | bash" "rclone installation"

    # Pull initial models
    run_on_server "$server_ip" "$server_name" "ollama pull phi3:3.8b && ollama pull gemma:2b" "model download"

    log_success "Inference services configured on $server_name"
}

# Setup cross-server communication
setup_cross_server_communication() {
    local inference_ip=$1
    local router_ip=$2

    log_info "🔗 Setting up cross-server communication..."

    # Get inference API key from Server 1
    log_info "Retrieving inference API key from Server 1..."
    INFERENCE_KEY=$(ssh -i "$SSH_KEY_PATH" -o ConnectTimeout="$SSH_TIMEOUT" -o StrictHostKeyChecking=no "$SSH_USER@$inference_ip" "grep 'LOCAL_LLM_API_KEY' /etc/systemd/system/local-llm-proxy.service | cut -d'=' -f2" 2>/dev/null || echo "")

    if [[ -z "$INFERENCE_KEY" ]]; then
        log_error "Failed to retrieve inference API key from Server 1"
        log_warning "You may need to manually configure the API key"
        return 1
    fi

    log_success "Retrieved inference API key"

    # Update router service on Server 2
    log_info "Updating router service configuration on Server 2..."
    ssh -i "$SSH_KEY_PATH" -o ConnectTimeout="$SSH_TIMEOUT" -o StrictHostKeyChecking=no "$SSH_USER@$router_ip" "
        sed -i 's|REPLACE_WITH_INFERENCE_KEY|$INFERENCE_KEY|g' /etc/systemd/system/goblin-router.service
        sed -i 's|INFERENCE_IP_REPLACE|$inference_ip|g' /etc/systemd/system/goblin-router.service
        systemctl daemon-reload
        systemctl restart goblin-router
    "

    log_success "Cross-server communication configured"
}

# Verify deployment
verify_deployment() {
    local server_ip=$1
    local server_name=$2
    local service_name=$3
    local health_endpoint=$4

    log_info "🔍 Verifying deployment on $server_name..."

    # Check service status
    if run_on_server "$server_ip" "$server_name" "systemctl is-active $service_name" "service status check"; then
        log_success "Service $service_name is running on $server_name"
    else
        log_warning "Service $service_name may not be running on $server_name"
    fi

    # Check health endpoint
    if run_on_server "$server_ip" "$server_name" "curl -f http://localhost$health_endpoint" "health check"; then
        log_success "Health endpoint $health_endpoint responding on $server_name"
    else
        log_warning "Health endpoint $health_endpoint not responding on $server_name"
    fi
}

# Main deployment function
main() {
    echo "🚀 Kamatera LLM Infrastructure CLI Deployment"
    echo "=============================================="
    log_info "Inference Node: $SERVER1_IP (4 CPU, 24GB RAM)"
    log_info "Router Node: $SERVER2_IP (2 CPU, 12GB RAM)"
    echo ""

    # Check prerequisites
    check_prerequisites

    # Test SSH connections
    if ! test_ssh_connection "$SERVER1_IP" "Server 1 (Inference)"; then
        log_error "Cannot proceed without SSH access to Server 1"
        exit 1
    fi

    if ! test_ssh_connection "$SERVER2_IP" "Server 2 (Router)"; then
        log_error "Cannot proceed without SSH access to Server 2"
        exit 1
    fi

    # Deploy bootstrap scripts
    log_info "📋 Step 1: Deploying bootstrap scripts..."
    deploy_bootstrap "$SERVER1_IP" "Server 1 (Inference)" "bootstrap_inference.sh"
    deploy_bootstrap "$SERVER2_IP" "Server 2 (Router)" "bootstrap_router.sh"

    # Configure inference services
    log_info "📋 Step 2: Configuring inference services..."
    configure_inference_services "$SERVER1_IP" "Server 1 (Inference)"

    # Setup cross-server communication
    log_info "📋 Step 3: Setting up cross-server communication..."
    setup_cross_server_communication "$SERVER1_IP" "$SERVER2_IP"

    # Verify deployment
    log_info "📋 Step 4: Verifying deployment..."
    verify_deployment "$SERVER1_IP" "Server 1 (Inference)" "local-llm-proxy" ":8002/health"
    verify_deployment "$SERVER2_IP" "Server 2 (Router)" "goblin-router" ":8000/health"

    # Final instructions
    echo ""
    log_success "🎉 CLI deployment completed!"
    echo ""
    log_info "Next steps:"
    log_info "1. Configure rclone Google Drive access on Server 1:"
    log_info "   ssh -i $SSH_KEY_PATH $SSH_USER@$SERVER1_IP"
    log_info "   rclone config"
    log_info ""
    log_info "2. Deploy models from Google Drive:"
    log_info "   ssh -i $SSH_KEY_PATH $SSH_USER@$SERVER1_IP"
    log_info "   rclone copy gdrive:models/llama_models /srv/models/active --progress"
    log_info ""
    log_info "3. Test end-to-end API:"
    log_info "   ssh -i $SSH_KEY_PATH $SSH_USER@$SERVER2_IP"
    log_info "   curl -H 'x-api-key: \$(grep PUBLIC_API_KEY /etc/systemd/system/goblin-router.service | cut -d'=' -f2)' \\"
    log_info "        -H 'Content-Type: application/json' \\"
    log_info "        -d '{\"model\": \"phi3:3.8b\", \"messages\": [{\"role\": \"user\", \"content\": \"Hello!\"}]}' \\"
    log_info "        http://localhost:8000/v1/chat/completions"
    echo ""
    log_info "4. Run local verification:"
    log_info "   ../../deployments/kamatera/verify_kamatera_deployment.sh"
}

# Handle command line arguments
case "${1:-}" in
    "test")
        log_info "Testing SSH connections only..."
        check_prerequisites
        test_ssh_connection "$SERVER1_IP" "Server 1 (Inference)" || exit 1
        test_ssh_connection "$SERVER2_IP" "Server 2 (Router)" || exit 1
        log_success "SSH connections successful!"
        ;;
    "deploy")
        main
        ;;
    "verify")
        log_info "Running verification only..."
        check_prerequisites
        verify_deployment "$SERVER1_IP" "Server 1 (Inference)" "local-llm-proxy" ":8002/health"
        verify_deployment "$SERVER2_IP" "Server 2 (Router)" "goblin-router" ":8000/health"
        ;;
    *)
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  deploy    - Full deployment (default)"
        echo "  test      - Test SSH connections only"
        echo "  verify    - Verify existing deployment"
        echo ""
        echo "Examples:"
        echo "  $0 deploy    # Full deployment"
        echo "  $0 test      # Test connections"
        echo "  $0 verify    # Check deployment status"
        ;;
esac
