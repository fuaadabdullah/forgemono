#!/bin/bash
# Configure systemd cgroups for AI services resource isolation

set -e

echo "🔧 Configuring systemd cgroups for AI services"

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

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    log_error "This script must be run as root"
    exit 1
fi

# Function to backup existing service
backup_service() {
    local service_name=$1
    local service_file="/etc/systemd/system/${service_name}.service"

    if [[ -f "$service_file" ]]; then
        cp "$service_file" "${service_file}.backup.$(date +%Y%m%d_%H%M%S)"
        log_info "Backed up $service_file"
    fi
}

# Configure Ollama service with resource limits
configure_ollama_service() {
    log_info "Configuring Ollama service with resource limits..."

    backup_service "ollama"

    # Ollama service with resource limits
    cat > /etc/systemd/system/ollama.service << 'EOF'
[Unit]
Description=Ollama AI Service
After=network-online.target
Wants=network-online.target
RequiresMountsFor=/srv/models

[Service]
Type=simple
User=root
Group=root
Environment="HOME=/root"
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_MAX_LOADED_MODELS=3"
Environment="OLLAMA_MAX_QUEUE=512"
Environment="OLLAMA_RUNNERS_DIR=/usr/share/ollama/runners"
Environment="OLLAMA_TMPDIR=/tmp"
WorkingDirectory=/usr/share/ollama
ExecStart=/usr/local/bin/ollama serve
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=3
LimitNOFILE=1048576
LimitNPROC=512

# Resource limits for Ollama
MemoryLimit=8G
MemoryHigh=6G
CPUQuota=200%
CPUWeight=100
IOWeight=100
TasksMax=256

# CPU affinity - prefer CPU cores 0-7 for AI workloads
CPUAffinity=0-7

# Block IO limits
BlockIOWeight=100
BlockIOReadBandwidthMax=/dev/sda 100M
BlockIOWriteBandwidthMax=/dev/sda 50M

# Disable swap for Ollama to prevent thrashing
MemorySwapMax=0

[Install]
WantedBy=multi-user.target
EOF

    log_success "Ollama service configured"
}

# Configure llama.cpp service with resource limits
configure_llamacpp_service() {
    log_info "Configuring llama.cpp service with resource limits..."

    backup_service "llamacpp"

    # Find model file
    MODEL_FILE=$(find /srv/models/active -name "*.gguf" 2>/dev/null | head -1)
    if [[ -z "$MODEL_FILE" ]]; then
        MODEL_FILE="/srv/models/active/placeholder.gguf"
        log_warning "No model file found, using placeholder"
    fi

    cat > /etc/systemd/system/llamacpp.service << EOF
[Unit]
Description=llama.cpp server
After=network.target
RequiresMountsFor=/srv/models

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/llama.cpp
Environment="LLAMA_CPP_LOG_LEVEL=info"
ExecStart=/opt/llama.cpp/build/bin/server -m $MODEL_FILE --port 8080 --host 0.0.0.0 --threads 4 --ctx-size 4096 --n-gpu-layers 0 --batch-size 512 --ubatch-size 512
Restart=always
RestartSec=5
LimitNOFILE=65536
LimitNPROC=128

# Resource limits for llama.cpp
MemoryLimit=6G
MemoryHigh=4G
CPUQuota=150%
CPUWeight=80
IOWeight=80
TasksMax=64

# CPU affinity - prefer CPU cores 8-11 for inference workloads
CPUAffinity=8-11

# Block IO limits
BlockIOWeight=80
BlockIOReadBandwidthMax=/dev/sda 50M
BlockIOWriteBandwidthMax=/dev/sda 25M

# Allow some swap usage for llama.cpp (less critical than Ollama)
MemorySwapMax=2G

[Install]
WantedBy=multi-user.target
EOF

    log_success "llama.cpp service configured"
}

# Configure local LLM proxy service with resource limits
configure_proxy_service() {
    log_info "Configuring Local LLM Proxy service with resource limits..."

    backup_service "local-llm-proxy"

    cat > /etc/systemd/system/local-llm-proxy.service << 'EOF'
[Unit]
Description=Local LLM Proxy Service
After=network.target ollama.service llamacpp.service
Wants=ollama.service llamacpp.service

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/usr/local/bin
Environment=LOCAL_LLM_API_KEY=your-secure-api-key-here
Environment=OLLAMA_URL=http://localhost:11434
Environment=LLAMA_CPP_URL=http://localhost:8080
Environment=PYTHONUNBUFFERED=1
ExecStart=/opt/llm-proxy-venv/bin/python /usr/local/bin/local_llm_proxy.py
Restart=on-failure
RestartSec=5
LimitNOFILE=65536
LimitNPROC=64

# Resource limits for proxy (lightweight service)
MemoryLimit=1G
MemoryHigh=512M
CPUQuota=50%
CPUWeight=50
IOWeight=50
TasksMax=32

# CPU affinity - use any available cores
CPUAffinity=0-15

# Block IO limits
BlockIOWeight=50
BlockIOReadBandwidthMax=/dev/sda 10M
BlockIOWriteBandwidthMax=/dev/sda 5M

# Allow minimal swap
MemorySwapMax=512M

[Install]
WantedBy=multi-user.target
EOF

    log_success "Local LLM Proxy service configured"
}

# Configure systemd resource management
configure_systemd_resources() {
    log_info "Configuring systemd resource management..."

    # Enable systemd resource accounting
    mkdir -p /etc/systemd/system.conf.d

    cat > /etc/systemd/system.conf.d/resource-accounting.conf << 'EOF'
[Manager]
# Enable resource accounting
DefaultMemoryAccounting=yes
DefaultCPUAccounting=yes
DefaultIOAccounting=yes
DefaultBlockIOAccounting=yes
DefaultTasksAccounting=yes

# Set default resource limits for all services
DefaultLimitNOFILE=1024:524288
DefaultLimitNPROC=512
EOF

    # Configure cgroup delegation for better resource control
    cat > /etc/systemd/system.conf.d/cgroup-delegation.conf << 'EOF'
[Manager]
# Delegate cgroup control to services
Delegate=yes
EOF

    log_success "Systemd resource management configured"
}

# Create resource monitoring service
create_resource_monitor() {
    log_info "Creating resource monitoring service..."

    cat > /usr/local/bin/ai-resource-monitor.sh << 'EOF'
#!/bin/bash
# Monitor AI service resource usage and alert if limits exceeded

LOG_FILE="/var/log/ai-resource-monitor.log"
ALERT_THRESHOLD_MEMORY=85  # Alert at 85% memory usage
ALERT_THRESHOLD_CPU=90     # Alert at 90% CPU usage

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" >> "$LOG_FILE"
}

check_service_resources() {
    local service=$1

    if systemctl is-active --quiet "$service"; then
        # Get memory usage percentage
        local mem_usage=$(systemctl show "$service" -p MemoryCurrent --value 2>/dev/null)
        if [[ -n "$mem_usage" && "$mem_usage" != "0" ]]; then
            local mem_limit=$(systemctl show "$service" -p MemoryLimit --value 2>/dev/null)
            if [[ -n "$mem_limit" && "$mem_limit" != "0" ]]; then
                local mem_percent=$((mem_usage * 100 / mem_limit))
                if [[ $mem_percent -gt $ALERT_THRESHOLD_MEMORY ]]; then
                    log "ALERT: $service memory usage at ${mem_percent}% (${mem_usage} bytes)"
                fi
            fi
        fi

        # Get CPU usage
        local cpu_usage=$(systemctl show "$service" -p CPUUsageNSec --value 2>/dev/null)
        if [[ -n "$cpu_usage" ]]; then
            # Convert nanoseconds to percentage (rough estimate)
            local cpu_percent=$((cpu_usage / 10000000))  # This is approximate
            if [[ $cpu_percent -gt $ALERT_THRESHOLD_CPU ]]; then
                log "ALERT: $service high CPU usage detected"
            fi
        fi
    fi
}

# Monitor AI services
check_service_resources ollama
check_service_resources llamacpp
check_service_resources local-llm-proxy

# Check overall system resources
total_mem=$(free | grep Mem | awk '{print $2}')
used_mem=$(free | grep Mem | awk '{print $3}')
mem_percent=$((used_mem * 100 / total_mem))

if [[ $mem_percent -gt 90 ]]; then
    log "SYSTEM ALERT: Memory usage at ${mem_percent}%"
fi

# Check swap usage
swap_total=$(free | grep Swap | awk '{print $2}')
if [[ $swap_total -gt 0 ]]; then
    swap_used=$(free | grep Swap | awk '{print $3}')
    swap_percent=$((swap_used * 100 / swap_total))

    if [[ $swap_percent -gt 50 ]]; then
        log "SYSTEM ALERT: Swap usage at ${swap_percent}%"
    fi
fi
EOF

    chmod +x /usr/local/bin/ai-resource-monitor.sh

    # Create systemd timer for monitoring
    cat > /etc/systemd/system/ai-resource-monitor.service << 'EOF'
[Unit]
Description=AI Resource Monitor

[Service]
Type=oneshot
ExecStart=/usr/local/bin/ai-resource-monitor.sh
EOF

    cat > /etc/systemd/system/ai-resource-monitor.timer << 'EOF'
[Unit]
Description=Run AI resource monitor every 30 seconds
Requires=ai-resource-monitor.service

[Timer]
OnBootSec=30
OnUnitActiveSec=30
AccuracySec=1s

[Install]
WantedBy=timers.target
EOF

    systemctl daemon-reload
    systemctl enable ai-resource-monitor.timer
    systemctl start ai-resource-monitor.timer

    log_success "Resource monitoring service created"
}

# Main execution
main() {
    log_info "Starting systemd cgroup configuration..."

    configure_systemd_resources
    configure_ollama_service
    configure_llamacpp_service
    configure_proxy_service
    create_resource_monitor

    # Reload systemd and restart services
    log_info "Reloading systemd and restarting services..."
    systemctl daemon-reload

    # Stop services before restarting with new config
    systemctl stop ollama llamacpp local-llm-proxy 2>/dev/null || true

    # Start services with new configuration
    systemctl start ollama
    sleep 2
    systemctl start llamacpp
    sleep 2
    systemctl start local-llm-proxy

    log_success "Systemd cgroup configuration complete!"
    log_info "Services restarted with resource limits applied"
    log_info "Monitor logs with: journalctl -u ai-resource-monitor -f"
}

main "$@"</content>
<parameter name="filePath">/Users/fuaadabdullah/ForgeMonorepo/scripts/configure_systemd_cgroups.sh
