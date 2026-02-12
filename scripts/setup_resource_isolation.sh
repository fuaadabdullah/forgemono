#!/bin/bash
# Resource Isolation Setup for Goblin AI System
# Sets up swapfile, zram, and resource limits for Ollama/llama.cpp

set -e

echo "🔧 Setting up resource isolation for Goblin AI System"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SWAP_SIZE_GB=16  # 16GB swapfile
ZRAM_SIZE_GB=8   # 8GB zram
ZRAM_COMPRESSION=lz4  # Fast compression algorithm

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

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    log_error "This script must be run as root"
    exit 1
fi

# Function to check available memory
check_memory() {
    local total_mem_kb=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    local total_mem_gb=$((total_mem_kb / 1024 / 1024))

    log_info "System has ${total_mem_gb}GB RAM"

    if [[ $total_mem_gb -lt 16 ]]; then
        log_warning "System has less than 16GB RAM. Consider upgrading for better AI performance."
    fi
}

# Setup swapfile
setup_swapfile() {
    log_info "Setting up ${SWAP_SIZE_GB}GB swapfile..."

    # Check if swapfile already exists
    if [[ -f /swapfile ]]; then
        local current_size=$(stat -c%s /swapfile)
        local expected_size=$((SWAP_SIZE_GB * 1024 * 1024 * 1024))

        if [[ $current_size -eq $expected_size ]]; then
            log_info "Swapfile already exists with correct size"
            return 0
        else
            log_warning "Swapfile exists but wrong size. Removing and recreating..."
            swapoff /swapfile 2>/dev/null || true
            rm -f /swapfile
        fi
    fi

    # Create swapfile
    log_info "Creating ${SWAP_SIZE_GB}GB swapfile..."
    dd if=/dev/zero of=/swapfile bs=1M count=$((SWAP_SIZE_GB * 1024)) status=progress
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile

    # Make it persistent
    if ! grep -q "/swapfile" /etc/fstab; then
        echo '/swapfile none swap sw 0 0' >> /etc/fstab
    fi

    log_success "Swapfile setup complete"
}

# Setup zram
setup_zram() {
    log_info "Setting up ${ZRAM_SIZE_GB}GB zram with ${ZRAM_COMPRESSION} compression..."

    # Install zram tools if not present
    if ! command -v zramctl &> /dev/null; then
        log_info "Installing zram tools..."
        apt update && apt install -y zram-tools
    fi

    # Configure zram
    cat > /etc/default/zramswap << EOF
# Zramswap configuration
ZRAM_COMPRESSION=${ZRAM_COMPRESSION}
ZRAM_SIZE_GB=${ZRAM_SIZE_GB}
EOF

    # Enable zram service
    systemctl enable zramswap.service 2>/dev/null || true
    systemctl start zramswap.service 2>/dev/null || true

    # Alternative: manual zram setup if service fails
    if ! systemctl is-active --quiet zramswap.service 2>/dev/null; then
        log_warning "zramswap service not available, setting up manually..."

        # Load zram module
        modprobe zram

        # Configure zram device
        echo ${ZRAM_COMPRESSION} > /sys/block/zram0/comp_algorithm
        echo $((ZRAM_SIZE_GB * 1024 * 1024 * 1024)) > /sys/block/zram0/disksize
        mkswap /dev/zram0
        swapon /dev/zram0 -p 10  # Higher priority than swapfile

        # Make persistent
        if ! grep -q "zram" /etc/modules; then
            echo "zram" >> /etc/modules
        fi

        cat > /etc/systemd/system/zram-setup.service << EOF
[Unit]
Description=Setup zram swap device
After=local-fs.target
Before=swap.target

[Service]
Type=oneshot
ExecStart=/bin/bash -c 'modprobe zram && echo ${ZRAM_COMPRESSION} > /sys/block/zram0/comp_algorithm && echo $((ZRAM_SIZE_GB * 1024 * 1024 * 1024)) > /sys/block/zram0/disksize && mkswap /dev/zram0 && swapon /dev/zram0 -p 10'
RemainAfterExit=yes

[Install]
WantedBy=swap.target
EOF

        systemctl daemon-reload
        systemctl enable zram-setup.service
    fi

    log_success "zram setup complete"
}

# Configure swappiness
configure_swappiness() {
    log_info "Configuring swappiness for optimal performance..."

    # Set swappiness to 10 (lower = prefer RAM, higher = prefer swap)
    # For AI workloads, we want to use RAM as much as possible but have swap as safety net
    sysctl -w vm.swappiness=10

    # Make persistent
    if ! grep -q "vm.swappiness" /etc/sysctl.conf; then
        echo "vm.swappiness=10" >> /etc/sysctl.conf
    else
        sed -i 's/vm.swappiness=.*/vm.swappiness=10/' /etc/sysctl.conf
    fi

    # Configure vfs_cache_pressure (how aggressively to reclaim cache)
    sysctl -w vm.vfs_cache_pressure=50

    if ! grep -q "vm.vfs_cache_pressure" /etc/sysctl.conf; then
        echo "vm.vfs_cache_pressure=50" >> /etc/sysctl.conf
    else
        sed -i 's/vm.vfs_cache_pressure=.*/vm.vfs_cache_pressure=50/' /etc/sysctl.conf
    fi

    log_success "Swappiness configured"
}

# Setup OOM protection
setup_oom_protection() {
    log_info "Setting up OOM protection..."

    # Install earlyoom for better OOM handling
    if ! command -v earlyoom &> /dev/null; then
        log_info "Installing earlyoom..."
        apt install -y earlyoom
    fi

    # Configure earlyoom (kill processes at 10% memory remaining)
    cat > /etc/default/earlyoom << EOF
EARLYOOM_ARGS="-m 10 -s 99 -r 60 -n"
EOF

    systemctl enable earlyoom.service
    systemctl start earlyoom.service

    log_success "OOM protection setup complete"
}

# Main execution
main() {
    log_info "Starting resource isolation setup..."

    check_memory
    setup_swapfile
    setup_zram
    configure_swappiness
    setup_oom_protection

    log_success "Resource isolation setup complete!"
    echo ""
    log_info "Current memory and swap status:"
    free -h
    echo ""
    swapon -s
    echo ""
    log_info "Next: Configure systemd cgroups for AI services"
}

main "$@"</content>
<parameter name="filePath">/Users/fuaadabdullah/ForgeMonorepo/scripts/setup_resource_isolation.sh
