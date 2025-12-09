#!/bin/bash
# SSH Key Setup for Kamatera Deployment
# Run this first to set up SSH access to your Kamatera servers

set -e

# Configuration
SSH_KEY_PATH="$HOME/.ssh/kamatera_raptor"
SERVER1_IP="192.175.23.150"
SERVER2_IP="45.61.51.220"
SSH_USER="root"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

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

# Create SSH key if it doesn't exist
create_ssh_key() {
    if [[ -f "$SSH_KEY_PATH" ]]; then
        log_info "SSH key already exists at $SSH_KEY_PATH"
        return 0
    fi

    log_info "Creating SSH key for Kamatera deployment..."
    ssh-keygen -t rsa -b 4096 -f "$SSH_KEY_PATH" -C "kamatera-deployment" -N ""

    log_success "SSH key created at $SSH_KEY_PATH"
    log_info "Public key: $SSH_KEY_PATH.pub"
}

# Copy SSH key to server
copy_key_to_server() {
    local server_ip=$1
    local server_name=$2

    log_info "Copying SSH key to $server_name ($server_ip)..."

    # First try passwordless (if key already copied)
    if ssh -i "$SSH_KEY_PATH" -o ConnectTimeout=10 -o StrictHostKeyChecking=no -o PasswordAuthentication=no "$SSH_USER@$server_ip" "echo 'SSH key already configured'" 2>/dev/null; then
        log_success "SSH key already configured on $server_name"
        return 0
    fi

    # Try ssh-copy-id
    if command -v ssh-copy-id >/dev/null 2>&1; then
        log_info "Using ssh-copy-id to copy key..."
        ssh-copy-id -i "$SSH_KEY_PATH" -o ConnectTimeout=10 -o StrictHostKeyChecking=no "$SSH_USER@$server_ip"
    else
        # Manual method
        log_info "Manual SSH key copy (ssh-copy-id not available)..."
        log_warning "Please run this command manually:"
        echo "ssh-copy-id -i $SSH_KEY_PATH $SSH_USER@$server_ip"
        log_info "Or manually append this to $SSH_USER@$server_ip:~/.ssh/authorized_keys:"
        cat "$SSH_KEY_PATH.pub"
        echo ""
        read -p "Press Enter after you've copied the SSH key manually..."
    fi

    # Verify connection
    if ssh -i "$SSH_KEY_PATH" -o ConnectTimeout=10 -o StrictHostKeyChecking=no -o PasswordAuthentication=no "$SSH_USER@$server_ip" "echo 'SSH connection successful'"; then
        log_success "SSH key successfully configured on $server_name"
    else
        log_error "Failed to configure SSH key on $server_name"
        return 1
    fi
}

# Test SSH connections
test_connections() {
    log_info "Testing SSH connections..."

    local success=true

    if ssh -i "$SSH_KEY_PATH" -o ConnectTimeout=10 -o StrictHostKeyChecking=no -o PasswordAuthentication=no "$SSH_USER@$SERVER1_IP" "echo 'Server 1 connection OK'" 2>/dev/null; then
        log_success "SSH connection to Server 1 (Inference) successful"
    else
        log_error "SSH connection to Server 1 failed"
        success=false
    fi

    if ssh -i "$SSH_KEY_PATH" -o ConnectTimeout=10 -o StrictHostKeyChecking=no -o PasswordAuthentication=no "$SSH_USER@$SERVER2_IP" "echo 'Server 2 connection OK'" 2>/dev/null; then
        log_success "SSH connection to Server 2 (Router) successful"
    else
        log_error "SSH connection to Server 2 failed"
        success=false
    fi

    if $success; then
        log_success "All SSH connections successful!"
        return 0
    else
        log_error "Some SSH connections failed"
        return 1
    fi
}

# Main function
main() {
    echo "🔑 Kamatera SSH Key Setup"
    echo "========================="
    log_info "This script will set up SSH key authentication for your Kamatera servers"
    log_info "Server 1 (Inference): $SERVER1_IP"
    log_info "Server 2 (Router): $SERVER2_IP"
    echo ""

    # Create SSH key
    create_ssh_key

    # Copy keys to servers
    copy_key_to_server "$SERVER1_IP" "Server 1 (Inference)"
    copy_key_to_server "$SERVER2_IP" "Server 2 (Router)"

    # Test connections
    test_connections

    echo ""
    log_success "SSH setup complete!"
    echo ""
    log_info "You can now run the deployment:"
    log_info "./deploy_kamatera_cli.sh deploy"
    echo ""
    log_info "Or test connections only:"
    log_info "./deploy_kamatera_cli.sh test"
}

# Run main function
main
