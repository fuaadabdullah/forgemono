#!/usr/bin/env bash
# ============================================================================
# Ollama Inference Server Timeout Fix
# Purpose: Fix persistent startup timeout issues on 192.175.23.150:8002
# 
# This script:
# 1. Diagnoses current Ollama service status and configuration
# 2. Optimizes systemd service configuration for reliable startup
# 3. Implements startup timeout fixes and dependency management
# 4. Adds health checks and recovery mechanisms
# 5. Tests service reliability and end-to-end functionality
# ============================================================================

set -euo pipefail

# ============================================================================
# CONFIGURATION
# ============================================================================

INFERENCE_SERVER="192.175.23.150"
INFERENCE_PORT="8002"
SSH_USER="root"
SSH_KEY="${SSH_KEY:-~/.ssh/kamatera_raptor}"
CONNECT_TIMEOUT=15
COMMAND_TIMEOUT=60

# Service configuration
OLLAMA_SERVICE_NAME="ollama"
PROXY_SERVICE_NAME="local-llm-proxy"
SYSTEMD_OVERRIDE_DIR="/etc/systemd/system/${PROXY_SERVICE_NAME}.service.d"

# Timeout configurations (in seconds)
STARTUP_TIMEOUT=900  # 15 minutes for full startup
STOP_TIMEOUT=300    # 5 minutes for graceful shutdown
HEALTH_CHECK_TIMEOUT=30
MAX_STARTUP_ATTEMPTS=3

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

log_info() {
    echo -e "${BLUE}ℹ️  ${1}${NC}"
}

log_success() {
    echo -e "${GREEN}✅ ${1}${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  ${1}${NC}"
}

log_error() {
    echo -e "${RED}❌ ${1}${NC}"
}

log_step() {
    echo -e "${PURPLE}🔧 ${1}${NC}"
}

run_remote_command() {
    local server=$1
    local command=$2
    local description=$3
    
    log_info "$description on $server..."
    
    if ssh -i "$SSH_KEY" -o ConnectTimeout=$CONNECT_TIMEOUT -o StrictHostKeyChecking=no "$SSH_USER@$server" "timeout $COMMAND_TIMEOUT bash -c '$command'" 2>/dev/null; then
        log_success "$description completed on $server"
        return 0
    else
        log_error "Failed to execute: $description on $server"
        return 1
    fi
}

test_service_port() {
    local server=$1
    local port=$2
    local service_name=$3
    
    log_info "Testing $service_name on $server:$port..."
    
    local cmd="timeout 10 bash -c 'echo > /dev/tcp/$server/$port' 2>/dev/null && echo 'OK' || echo 'FAIL'"
    local result=$(ssh -i "$SSH_KEY" -o ConnectTimeout=$CONNECT_TIMEOUT -o StrictHostKeyChecking=no "$SSH_USER@localhost" "$cmd" 2>/dev/null || echo "ERROR")
    
    if [[ "$result" == "OK" ]]; then
        log_success "$service_name port test: ✅ OK"
        return 0
    else
        log_error "$service_name port test: ❌ FAILED"
        return 1
    fi
}

# ============================================================================
# PHASE 1: SERVICE DIAGNOSTICS
# ============================================================================

diagnose_current_status() {
    log_step "PHASE 1: Service Diagnostics & Configuration Analysis"
    echo ""
    
    log_info "Analyzing current Ollama service status and configuration..."
    
    # Check service status
    local status_cmd="
    echo '=== SERVICE STATUS ==='
    systemctl is-active $PROXY_SERVICE_NAME 2>/dev/null || echo 'Service not found'
    systemctl is-active $OLLAMA_SERVICE_NAME 2>/dev/null || echo 'Ollama service not found'
    echo ''
    echo '=== SYSTEMD SERVICE FILES ==='
    systemctl cat $PROXY_SERVICE_NAME 2>/dev/null | head -20 || echo 'No service file found'
    echo ''
    echo '=== SERVICE LOGS (Last 10 lines) ==='
    journalctl -u $PROXY_SERVICE_NAME -n 10 --no-pager 2>/dev/null | tail -10 || echo 'No logs available'
    echo ''
    echo '=== SYSTEM RESOURCES ==='
    free -h
    df -h / | tail -1
    "
    
    run_remote_command "$INFERENCE_SERVER" "$status_cmd" "Collecting service diagnostic information" || true
    
    echo ""
}

check_service_configuration() {
    log_info "Checking systemd service configuration..."
    
    local config_cmd="
    echo '=== CURRENT SERVICE CONFIGURATION ==='
    systemctl cat $PROXY_SERVICE_NAME 2>/dev/null || echo 'Service file not found'
    echo ''
    echo '=== TIMEOUT SETTINGS ==='
    systemctl show $PROXY_SERVICE_NAME --property=DefaultTimeoutStartSec 2>/dev/null || echo 'No timeout settings found'
    systemctl show $PROXY_SERVICE_NAME --property=DefaultTimeoutStopSec 2>/dev/null || echo 'No stop timeout found'
    echo ''
    echo '=== ENVIRONMENT VARIABLES ==='
    systemctl show $PROXY_SERVICE_NAME --property=Environment 2>/dev/null || echo 'No environment variables'
    echo ''
    echo '=== DEPENDENCIES ==='
    systemctl show $PROXY_SERVICE_NAME --property=After 2>/dev/null || echo 'No dependencies'
    systemctl show $PROXY_SERVICE_NAME --property=Requires 2>/dev/null || echo 'No requirements'
    "
    
    run_remote_command "$INFERENCE_SERVER" "$config_cmd" "Checking service configuration" || true
    
    echo ""
}

analyze_startup_bottlenecks() {
    log_info "Analyzing potential startup bottlenecks..."
    
    local bottleneck_cmd="
    echo '=== OLLAMA PROCESSES ==='
    ps aux | grep -E '(ollama|local-llm-proxy)' | grep -v grep || echo 'No Ollama processes found'
    echo ''
    echo '=== PORT USAGE ==='
    netstat -tlnp 2>/dev/null | grep ':8002\|:11434' || ss -tlnp | grep ':8002\|:11434' || echo 'Ports not in use'
    echo ''
    echo '=== DISK SPACE ==='
    df -h / | tail -1
    echo '=== MEMORY USAGE ==='
    free -h
    echo ''
    echo '=== MODEL FILES ==='
    ls -la ~/.ollama/models/blobs/ 2>/dev/null | head -10 || echo 'No model files found'
    echo '=== MODEL COUNT ==='
    ls ~/.ollama/models/blobs/ 2>/dev/null | wc -l || echo '0'
    "
    
    run_remote_command "$INFERENCE_SERVER" "$bottleneck_cmd" "Analyzing startup bottlenecks" || true
    
    echo ""
}

# ============================================================================
# PHASE 2: SERVICE OPTIMIZATION
# ============================================================================

optimize_systemd_service() {
    log_step "PHASE 2: Service Optimization & Configuration"
    echo ""
    
    log_info "Creating optimized systemd service configuration..."
    
    # Create systemd override directory
    local setup_cmd="
    sudo mkdir -p $SYSTEMD_OVERRIDE_DIR
    sudo tee $SYSTEMD_OVERRIDE_DIR/override.conf > /dev/null << 'EOF'
[Service]
# Timeout configurations
TimeoutStartSec=${STARTUP_TIMEOUT}
TimeoutStopSec=${STOP_TIMEOUT}
TimeoutSec=${STARTUP_TIMEOUT}

# Restart configuration
Restart=always
RestartSec=5
StartLimitIntervalSec=300
StartLimitBurst=5

# Resource management
LimitNOFILE=65536
LimitMEMLOCK=infinity

# Working directory
WorkingDirectory=/root

# Environment
Environment=OLLAMA_HOST=0.0.0.0:11434
Environment=OLLAMA_ORIGINS=*

# Process management
Type=notify
NotifyAccess=all

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=local-llm-proxy

# Health check
ExecStartPost=/bin/bash -c 'for i in {1..30}; do if curl -sf http://localhost:${INFERENCE_PORT}/api/tags >/dev/null 2>&1; then exit 0; fi; sleep 2; done; exit 1'
EOF
    "
    
    run_remote_command "$INFERENCE_SERVER" "$setup_cmd" "Creating systemd service override" || true
    
    # Create main service file if it doesn't exist
    local create_service_cmd="
    if [ ! -f /etc/systemd/system/$PROXY_SERVICE_NAME.service ]; then
        sudo tee /etc/systemd/system/$PROXY_SERVICE_NAME.service > /dev/null << 'EOF'
[Unit]
Description=Local LLM Proxy with Ollama
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=notify
User=root
Group=root
WorkingDirectory=/root
ExecStart=/usr/local/bin/local-llm-proxy
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
    fi
    "
    
    run_remote_command "$INFERENCE_SERVER" "$create_service_cmd" "Creating main service file" || true
    
    echo ""
}

create_ollama_optimization_script() {
    log_info "Creating Ollama startup optimization script..."
    
    local optimization_script="
    sudo tee /usr/local/bin/ollama-startup-optimize > /dev/null << 'EOF'
#!/bin/bash
# Ollama Startup Optimization Script

set -e

# Increase system limits for Ollama
echo 'Increasing system limits for Ollama...'
sysctl -w vm.max_map_count=262144 2>/dev/null || echo 'vm.max_map_count not modifiable'
sysctl -w fs.file-max=2097152 2>/dev/null || echo 'fs.file-max not modifiable'

# Set optimal memory parameters
echo 'Optimizing memory parameters...'
echo 'never' > /sys/kernel/mm/transparent_hugepage/enabled 2>/dev/null || echo 'THP not modifiable'

# Pre-warm Ollama models (if configured)
echo 'Pre-warming Ollama models...'
if command -v ollama >/dev/null 2>&1; then
    # Start Ollama in background for model warming
    nohup ollama serve > /tmp/ollama-serve.log 2>&1 &
    OLLAMA_PID=\$!
    
    # Wait for Ollama to be ready
    for i in {1..60}; do
        if curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
            echo 'Ollama server ready'
            break
        fi
        sleep 2
    done
    
    # Keep Ollama running for model caching
    if [ \$i -lt 60 ]; then
        echo 'Warming models...'
        # Optionally warm specific models
        # ollama pull llama2:7b 2>/dev/null || echo 'Model warm failed'
        sleep 30
    fi
    
    # Kill the warmup process (main service will handle it)
    kill \$OLLAMA_PID 2>/dev/null || true
    wait \$OLLAMA_PID 2>/dev/null || true
fi

echo 'Ollama optimization complete'
EOF

    sudo chmod +x /usr/local/bin/ollama-startup-optimize
    "
    
    run_remote_command "$INFERENCE_SERVER" "$optimization_script" "Creating optimization script" || true
    
    echo ""
}

update_service_with_optimizations() {
    log_info "Updating service with optimization hooks..."
    
    local update_cmd="
    # Add optimization to service
    sudo sed -i '/^\[Service\]/a ExecStartPre=/usr/local/bin/ollama-startup-optimize' /etc/systemd/system/$PROXY_SERVICE_NAME.service
    
    # Reload systemd
    sudo systemctl daemon-reload
    sudo systemctl reset-failed $PROXY_SERVICE_NAME 2>/dev/null || true
    
    echo 'Service updated with optimizations'
    "
    
    run_remote_command "$INFERENCE_SERVER" "$update_cmd" "Updating service with optimizations" || true
    
    echo ""
}

# ============================================================================
# PHASE 3: MONITORING & STABILITY
# ============================================================================

setup_monitoring_and_health_checks() {
    log_step "PHASE 3: Monitoring & Stability"
    echo ""
    
    log_info "Setting up comprehensive monitoring and health checks..."
    
    # Create health check script
    local health_check_script="
    sudo tee /usr/local/bin/ollama-health-check > /dev/null << 'EOF'
#!/bin/bash
# Comprehensive Ollama Health Check

INFERENCE_PORT=8002
OLLAMA_PORT=11434
LOG_FILE='/var/log/ollama-health.log'

log_health() {
    echo \"[\$(date)] \$1\" >> \$LOG_FILE
}

# Check Ollama service
if ! systemctl is-active --quiet ollama; then
    log_health 'ERROR: Ollama service is not active'
    exit 1
fi

# Check Ollama port
if ! timeout 5 bash -c \"echo > /dev/tcp/127.0.0.1/\$OLLAMA_PORT\" 2>/dev/null; then
    log_health 'ERROR: Ollama port \$OLLAMA_PORT not accessible'
    exit 1
fi

# Check Ollama API
if ! curl -sf http://localhost:\$OLLAMA_PORT/api/tags >/dev/null 2>&1; then
    log_health 'ERROR: Ollama API not responding'
    exit 1
fi

# Check local-llm-proxy service
if ! systemctl is-active --quiet $PROXY_SERVICE_NAME; then
    log_health 'ERROR: Proxy service is not active'
    exit 1
fi

# Check proxy port
if ! timeout 5 bash -c \"echo > /dev/tcp/127.0.0.1/\$INFERENCE_PORT\" 2>/dev/null; then
    log_health 'ERROR: Proxy port \$INFERENCE_PORT not accessible'
    exit 1
fi

# Check proxy API
if ! curl -sf http://localhost:\$INFERENCE_PORT/health >/dev/null 2>&1; then
    log_health 'WARNING: Proxy health endpoint not responding'
fi

log_health 'INFO: All health checks passed'
exit 0
EOF

    sudo chmod +x /usr/local/bin/ollama-health-check
    "
    
    run_remote_command "$INFERENCE_SERVER" "$health_check_script" "Creating health check script" || true
    
    # Create monitoring service
    local monitoring_service="
    sudo tee /etc/systemd/system/ollama-monitor.service > /dev/null << 'EOF'
[Unit]
Description=Ollama Health Monitor
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/ollama-health-check
User=root

[Install]
WantedBy=multi-user.target
EOF

    sudo tee /etc/systemd/system/ollama-monitor.timer > /dev/null << 'EOF'
[Unit]
Description=Run Ollama health check every 2 minutes
Requires=ollama-monitor.service

[Timer]
OnBootSec=30sec
OnUnitActiveSec=2min
Persistent=true

[Install]
WantedBy=timers.target
EOF
    "
    
    run_remote_command "$INFERENCE_SERVER" "$monitoring_service" "Creating monitoring service" || true
    
    # Enable monitoring
    local enable_monitoring="
    sudo systemctl daemon-reload
    sudo systemctl enable ollama-monitor.timer
    sudo systemctl start ollama-monitor.timer
    echo 'Monitoring enabled'
    "
    
    run_remote_command "$INFERENCE_SERVER" "$enable_monitoring" "Enabling monitoring service" || true
    
    echo ""
}

implement_recovery_mechanisms() {
    log_info "Implementing automatic recovery mechanisms..."
    
    local recovery_script="
    sudo tee /usr/local/bin/ollama-recovery > /dev/null << 'EOF'
#!/bin/bash
# Ollama Automatic Recovery Script

MAX_RESTARTS=5
RESTART_WINDOW=300  # 5 minutes
LOG_FILE='/var/log/ollama-recovery.log'

log_recovery() {
    echo \"[\$(date)] \$1\" >> \$LOG_FILE
}

# Check restart rate
RESTART_COUNT=\$(systemctl show $PROXY_SERVICE_NAME --property=Restarts | cut -d= -f2)
if [ \$RESTART_COUNT -gt \$MAX_RESTARTS ]; then
    log_recovery \"ERROR: Too many restarts (\$RESTART_COUNT), manual intervention required\"
    exit 1
fi

# Force restart with backoff
log_recovery \"INFO: Attempting recovery restart\"
systemctl restart $PROXY_SERVICE_NAME

# Wait for startup
sleep 30

# Verify recovery
if systemctl is-active --quiet $PROXY_SERVICE_NAME; then
    log_recovery \"SUCCESS: Service recovered successfully\"
    
    # Run health check
    if /usr/local/bin/ollama-health-check; then
        log_recovery \"SUCCESS: Health check passed\"
        exit 0
    else
        log_recovery \"WARNING: Service active but health check failed\"
        exit 1
    fi
else
    log_recovery \"ERROR: Recovery failed, service not active\"
    exit 1
fi
EOF

    sudo chmod +x /usr/local/bin/ollama-recovery
    "
    
    run_remote_command "$INFERENCE_SERVER" "$recovery_script" "Creating recovery script" || true
    
    # Update service with recovery
    local update_recovery="
    sudo sed -i '/^\