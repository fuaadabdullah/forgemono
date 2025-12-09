#!/bin/bash
# Create systemd service for AI resource management

set -e

echo "🔧 Creating AI Resource Management systemd service"

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

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    log_error "This script must be run as root"
    exit 1
fi

# Create resource management service
create_resource_service() {
    log_info "Creating AI resource management service..."

    cat > /etc/systemd/system/ai-resource-manager.service << 'EOF'
[Unit]
Description=AI Resource Manager
After=network.target local-fs.target
Wants=network.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/ai-resource-manager.sh
RemainAfterExit=yes
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    log_success "AI resource management service created"
}

# Create resource manager script
create_resource_manager_script() {
    log_info "Creating resource manager script..."

    cat > /usr/local/bin/ai-resource-manager.sh << 'EOF'
#!/bin/bash
# AI Resource Manager - Manages swap, zram, and resource isolation

set -e

LOG_FILE="/var/log/ai-resource-manager.log"
SCRIPT_DIR="/usr/local/bin"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" | tee -a "$LOG_FILE"
}

# Setup swap and zram
setup_swap_zram() {
    log "Setting up swap and zram..."

    # Create swapfile if it doesn't exist
    if [[ ! -f /swapfile ]]; then
        log "Creating 16GB swapfile..."
        dd if=/dev/zero of=/swapfile bs=1M count=16384 status=progress
        chmod 600 /swapfile
        mkswap /swapfile
        swapon /swapfile

        if ! grep -q "/swapfile" /etc/fstab; then
            echo '/swapfile none swap sw 0 0' >> /etc/fstab
        fi
        log "Swapfile created and enabled"
    fi

    # Setup zram if not already configured
    if ! systemctl is-active --quiet zramswap.service 2>/dev/null && ! pgrep -f "zram" > /dev/null; then
        log "Setting up zram..."
        apt update && apt install -y zram-tools

        cat > /etc/default/zramswap << EOF
ZRAM_COMPRESSION=lz4
ZRAM_SIZE_GB=8
EOF

        systemctl enable zramswap.service
        systemctl start zramswap.service
        log "zram configured"
    fi

    # Configure swappiness
    sysctl -w vm.swappiness=10
    if ! grep -q "vm.swappiness" /etc/sysctl.conf; then
        echo "vm.swappiness=10" >> /etc/sysctl.conf
    fi

    log "Swap and zram setup complete"
}

# Configure systemd resource accounting
configure_systemd_resources() {
    log "Configuring systemd resource accounting..."

    mkdir -p /etc/systemd/system.conf.d

    cat > /etc/systemd/system.conf.d/resource-accounting.conf << 'EOF'
[Manager]
DefaultMemoryAccounting=yes
DefaultCPUAccounting=yes
DefaultIOAccounting=yes
DefaultBlockIOAccounting=yes
DefaultTasksAccounting=yes
DefaultLimitNOFILE=1024:524288
DefaultLimitNPROC=512
EOF

    cat > /etc/systemd/system.conf.d/cgroup-delegation.conf << 'EOF'
[Manager]
Delegate=yes
EOF

    systemctl daemon-reload
    log "Systemd resource accounting configured"
}

# Setup earlyoom for OOM protection
setup_oom_protection() {
    log "Setting up OOM protection..."

    if ! command -v earlyoom &> /dev/null; then
        apt install -y earlyoom
    fi

    cat > /etc/default/earlyoom << 'EOF'
EARLYOOM_ARGS="-m 10 -s 99 -r 60 -n"
EOF

    systemctl enable earlyoom.service
    systemctl start earlyoom.service
    log "OOM protection configured"
}

# Verify AI services are running with proper limits
verify_services() {
    log "Verifying AI services..."

    local services=("ollama" "llamacpp" "local-llm-proxy")
    local failed_services=()

    for service in "${services[@]}"; do
        if systemctl is-active --quiet "$service" 2>/dev/null; then
            log "$service: RUNNING"

            # Check if resource limits are applied
            local mem_limit
            mem_limit=$(systemctl show "$service" -p MemoryLimit --value 2>/dev/null)
            if [[ -n "$mem_limit" && "$mem_limit" != "0" ]]; then
                log "  Memory limit: $((mem_limit / 1024 / 1024))MB"
            fi
        else
            log "$service: NOT RUNNING"
            failed_services+=("$service")
        fi
    done

    if [[ ${#failed_services[@]} -gt 0 ]]; then
        log "WARNING: Some services are not running: ${failed_services[*]}"
    fi
}

# Main execution
main() {
    log "=== AI Resource Manager Starting ==="

    setup_swap_zram
    configure_systemd_resources
    setup_oom_protection
    verify_services

    log "=== AI Resource Manager Complete ==="

    # Run resource monitor once
    if [[ -x /usr/local/bin/ai-resource-monitor.sh ]]; then
        /usr/local/bin/ai-resource-monitor.sh --collect
    fi
}

main "$@"
EOF

    chmod +x /usr/local/bin/ai-resource-manager.sh
    log_success "Resource manager script created"
}

# Create timer for periodic resource management
create_resource_timer() {
    log_info "Creating resource management timer..."

    cat > /etc/systemd/system/ai-resource-manager.timer << 'EOF'
[Unit]
Description=Run AI resource manager daily
Requires=ai-resource-manager.service

[Timer]
OnBootSec=5min
OnUnitActiveSec=24h
AccuracySec=1h

[Install]
WantedBy=timers.target
EOF

    systemctl daemon-reload
    systemctl enable ai-resource-manager.timer
    systemctl start ai-resource-manager.timer

    log_success "Resource management timer created"
}

# Main execution
main() {
    log_info "Starting AI resource management service creation..."

    create_resource_service
    create_resource_manager_script
    create_resource_timer

    # Enable and start the service
    systemctl daemon-reload
    systemctl enable ai-resource-manager.service
    systemctl start ai-resource-manager.service

    log_success "AI resource management service setup complete!"
    log_info "Service will run on boot and daily"
    log_info "Monitor with: journalctl -u ai-resource-manager -f"
}

main "$@"</content>
<parameter name="filePath">/Users/fuaadabdullah/ForgeMonorepo/scripts/create_resource_management_service.sh
