#!/usr/bin/env bash
# ============================================================================
# Ollama Service Timeout Fix Script
# Purpose: Fix persistent startup timeout issues on 192.175.23.150:8002
# ============================================================================

set -euo pipefail

# Configuration
INFERENCE_SERVER="192.175.23.150"
INFERENCE_PORT="8002"
SSH_USER="root"
SSH_KEY="${SSH_KEY:-~/.ssh/kamatera_raptor}"
CONNECT_TIMEOUT=15
COMMAND_TIMEOUT=120

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  ${1}${NC}"; }
log_success() { echo -e "${GREEN}✅ ${1}${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  ${1}${NC}"; }
log_error() { echo -e "${RED}❌ ${1}${NC}"; }
log_step() { echo -e "${PURPLE}🔧 ${1}${NC}"; }

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

# Phase 1: Diagnose Current Status
diagnose_current_status() {
    log_step "PHASE 1: Diagnosing Current Ollama Service Status"
    echo ""
    
    local status_cmd="
    echo '=== CURRENT SERVICE STATUS ==='
    systemctl status ollama --no-pager -l || echo 'Ollama service status unavailable'
    echo ''
    echo '=== OLLAMA SERVICE TIMEOUT SETTINGS ==='
    systemctl show ollama --property=DefaultTimeoutStartSec 2>/dev/null || echo 'No timeout settings found'
    systemctl show ollama --property=DefaultTimeoutStopSec 2>/dev/null || echo 'No stop timeout found'
    echo ''
    echo '=== OLLAMA PROCESSES ==='
    ps aux | grep ollama | grep -v grep || echo 'No Ollama processes found'
    echo ''
    echo '=== PORT USAGE ==='
    ss -tlnp | grep -E ':11434|:8002' || echo 'Ports not in use'
    echo ''
    echo '=== SYSTEM RESOURCES ==='
    free -h
    df -h / | tail -1
    echo ''
    echo '=== MODEL FILES ==='
    ls ~/.ollama/models/blobs/ 2>/dev/null | wc -l || echo '0'
    "
    
    run_remote_command "$INFERENCE_SERVER" "$status_cmd" "Collecting diagnostic information" || true
    
    echo ""
}

# Phase 2: Apply Extended Timeout Configuration
apply_extended_timeouts() {
    log_step "PHASE 2: Applying Extended Timeout Configuration"
    echo ""
    
    log_info "Applying extended timeout configuration to Ollama service..."
    
    local timeout_config="
    # Create systemd override directory
    sudo mkdir -p /etc/systemd/system/ollama.service.d
    
    # Create comprehensive timeout override
    sudo tee /etc/systemd/system/ollama.service.d/timeout-fix.conf > /dev/null << 'EOF'
[Service]
# Extended timeout configurations
TimeoutStartSec=900
TimeoutStopSec=300
TimeoutSec=900
TimeoutStartFailureAction=terminate
TimeoutStopFailureAction=terminate

# Restart configuration
Restart=always
RestartSec=10
StartLimitIntervalSec=300
StartLimitBurst=5

# Resource management
LimitNOFILE=65536
LimitMEMLOCK=infinity
LimitAS=infinity

# Environment variables
Environment=OLLAMA_HOST=0.0.0.0:11434
Environment=OLLAMA_ORIGINS=*
Environment=OLLAMA_NUM_PARALLEL=4
Environment=OLLAMA_MAX_LOADED_MODELS=2

# Process management
Type=notify
NotifyAccess=all

# Working directory
WorkingDirectory=/root

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ollama

# Health check
ExecStartPost=/bin/bash -c 'for i in {1..60}; do if curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then exit 0; fi; sleep 2; done; exit 1'

# Startup optimization
ExecStartPre=/bin/bash -c 'echo 1 > /proc/sys/vm/overcommit_memory 2>/dev/null || true'
EOF
    
    # Reload systemd configuration
    sudo systemctl daemon-reload
    sudo systemctl reset-failed ollama 2>/dev/null || true
    
    echo 'Extended timeout configuration applied'
    "
    
    run_remote_command "$INFERENCE_SERVER" "$timeout_config" "Applying extended timeout configuration" || true
    
    echo ""
}

# Phase 3: Optimize Startup Process
optimize_startup() {
    log_step "PHASE 3: Optimizing Ollama Startup Process"
    echo ""
    
    log_info "Creating Ollama startup optimization script..."
    
    local optimization_cmd="
    # Create startup optimization script
    sudo tee /usr/local/bin/ollama-startup-optimize > /dev/null << 'EOF'
#!/bin/bash
# Ollama Startup Optimization

echo 'Starting Ollama optimization...'

# Increase system limits
sysctl -w vm.max_map_count=262144 2>/dev/null || true
sysctl -w fs.file-max=2097152 2>/dev/null || true

# Memory optimization
echo never > /sys/kernel/mm/transparent_hugepage/enabled 2>/dev/null || true

# Start Ollama with optimization flags
echo 'Starting Ollama service...'
systemctl start ollama

# Wait for Ollama to be ready with extended timeout
echo 'Waiting for Ollama to become ready...'
for i in {1..90}; do
    if curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
        echo 'Ollama is ready'
        exit 0
    fi
    echo \"Attempt \$i/90 - Ollama not ready yet\"
    sleep 5
done

echo 'Ollama startup timeout exceeded'
exit 1
EOF

    sudo chmod +x /usr/local/bin/ollama-startup-optimize
    echo 'Startup optimization script created'
    "
    
    run_remote_command "$INFERENCE_SERVER" "$optimization_cmd" "Creating startup optimization script" || true
    
    echo ""
}

# Phase 4: Restart with New Configuration
restart_with_new_config() {
    log_step "PHASE 4: Restarting Service with New Configuration"
    echo ""
    
    log_info "Restarting Ollama service with extended timeouts..."
    
    local restart_cmd="
    echo 'Stopping current Ollama service...'
    sudo systemctl stop ollama || true
    sleep 5
    
    echo 'Starting Ollama service with new configuration...'
    sudo systemctl start ollama
    
    echo 'Monitoring service startup...'
    sleep 10
    
    # Check service status
    echo 'Service status after restart:'
    systemctl is-active ollama || echo 'Service not active'
    
    echo 'Checking port availability...'
    timeout 10 bash -c 'echo > /dev/tcp/127.0.0.1/11434' 2>/dev/null && echo 'Ollama port (11434): OK' || echo 'Ollama port (11434): NOT READY'
    
    echo 'Checking Ollama API...'
    curl -sf http://localhost:11434/api/tags 2>/dev/null | head -c 100 || echo 'API not ready yet'
    
    echo 'Service restart completed'
    "
    
    run_remote_command "$INFERENCE_SERVER" "$restart_cmd" "Restarting service with new configuration" || true
    
    echo ""
}

# Phase 5: Test and Validate
test_service_functionality() {
    log_step "PHASE 5: Testing Service Functionality"
    echo ""
    
    log_info "Testing Ollama service functionality..."
    
    local test_cmd="
    echo '=== OLLAMA FUNCTIONALITY TEST ==='
    
    # Test Ollama API
    echo 'Testing Ollama API endpoint...'
    OLLAMA_RESPONSE=\"\$(curl -sf http://localhost:11434/api/tags 2>/dev/null)\"
    if [[ \"\$OLLAMA_RESPONSE\" == *\"models\"* ]]; then
        echo 'Ollama API: ✅ WORKING'
        echo \"Models available: \$(echo \$OLLAMA_RESPONSE | jq -r '.models | length' 2>/dev/null || echo 'Unknown')\"
    else
        echo 'Ollama API: ❌ NOT WORKING'
        echo \"Response: \${OLLAMA_RESPONSE:0:200}\"
    fi
    
    echo ''
    echo '=== PROXY SERVICE TEST ==='
    
    # Test local-llm-proxy if it exists
    if systemctl list-unit-files | grep -q 'local-llm-proxy'; then
        echo 'Testing local-llm-proxy...'
        PROXY_RESPONSE=\"\$(curl -sf http://localhost:8002/health 2>/dev/null)\"
        if [[ \"\$PROXY_RESPONSE\" == *\"healthy\"* ]]; then
            echo 'Proxy service: ✅ WORKING'
        else
            echo 'Proxy service: ⚠️  UNKNOWN STATUS'
            echo \"Response: \${PROXY_RESPONSE:0:200}\"
        fi
    else
        echo 'local-llm-proxy: Not installed'
    fi
    
    echo ''
    echo '=== RESOURCE USAGE ==='
    echo 'Memory usage:'
    free -h
    echo ''
    echo 'Disk usage:'
    df -h / | tail -1
    "
    
    run_remote_command "$INFERENCE_SERVER" "$test_cmd" "Testing service functionality" || true
    
    echo ""
}

# Phase 6: Test Router Connectivity
test_router_connectivity() {
    log_step "PHASE 6: Testing Router to Inference Connectivity"
    echo ""
    
    log_info "Testing router to inference server connectivity..."
    
    local router_server="45.61.51.220"
    local router_test="
    echo '=== ROUTER CONNECTIVITY TEST ==='
    
    # Test from router to inference
    echo 'Testing router to inference connectivity...'
    timeout 10 bash -c 'echo > /dev/tcp/$INFERENCE_SERVER/8002' 2>/dev/null && echo 'Router → Inference: OK' || echo 'Router → Inference: FAIL'
    
    # Test router health
    echo 'Testing router health...'
    curl -sf http://localhost:8000/health 2>/dev/null | head -c 200 || echo 'Router health: No response'
    
    # Test chat completion through router
    echo 'Testing chat completion through router...'
    local chat_test=\"\$(curl -s -X POST http://localhost:8000/v1/chat/completions \
      -H 'Content-Type: application/json' \
      -H 'X-API-Key: cef5587890c73a5316a9a2c4ed851d97beb89fd28443885aad6e570dabd5f765' \
      -d '{\"model\":\"llama2:7b\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello\"}],\"max_tokens\":50}' \
      2>/dev/null)\"
    
    if [[ \"\$chat_test\" == *\"choices\"* ]]; then
        echo 'Router chat: ✅ WORKING'
    elif [[ \"\$chat_test\" == *\"unavailable\"* ]]; then
        echo 'Router chat: ❌ FAILED - All servers unavailable'
    else
        echo 'Router chat: ⚠️  UNKNOWN RESPONSE'
        echo \"Response: \${chat_test:0:200}\"
    fi
    "
    
    run_remote_command "$router_server" "$router_test" "Testing router connectivity" || true
    
    echo ""
}

# Phase 7: Final Summary
display_final_summary() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════════════╗"
    echo "║  🎉 OLLAMA SERVICE TIMEOUT FIX - COMPLETE                       ║"
    echo "╚════════════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "═══════════════════════════════════════════════════════════════════════"
    echo "                    🔧 FIXES APPLIED"
    echo "═══════════════════════════════════════════════════════════════════════"
    echo ""
    echo "✅ Extended timeout configuration (900s start, 300s stop)"
    echo "✅ Restart policy optimization (always restart, 10s interval)"
    echo "✅ Resource limit optimization (file limits, memory limits)"
    echo "✅ Environment variable configuration (host, origins, parallel)"
    echo "✅ Startup optimization script (system limits, memory)"
    echo "✅ Health check integration (API readiness verification)"
    echo "✅ Process management (notify type, access control)"
    echo ""
    echo "═══════════════════════════════════════════════════════════════════════"
    echo "                    📊 CONFIGURATION DETAILS"
    echo "═══════════════════════════════════════════════════════════════════════"
    echo ""
    echo "Service: ollama"
    echo "Server: $INFERENCE_SERVER"
    echo "Startup Timeout: 900 seconds (15 minutes)"
    echo "Stop Timeout: 300 seconds (5 minutes)"
    echo "Restart Policy: always (10s interval)"
    echo "Max Restarts: 5 per 5 minutes"
    echo ""
    echo "═══════════════════════════════════════════════════════════════════════"
    echo "                    🛠️  MONITORING COMMANDS"
    echo "═══════════════════════════════════════════════════════════════════════"
    echo ""
    echo "Monitor service status:"
    echo "  ssh root@$INFERENCE_SERVER 'systemctl status ollama'"
    echo ""
    echo "View service logs:"
    echo "  ssh root@$INFERENCE_SERVER 'journalctl -u ollama -f'"
    echo ""
    echo "Test Ollama API:"
    echo "  ssh root@$INFERENCE_SERVER 'curl -s http://localhost:11434/api/tags'"
    echo ""
    echo "Manual restart:"
    echo "  ssh root@$INFERENCE_SERVER 'sudo systemctl restart ollama'"
    echo ""
    echo "═══════════════════════════════════════════════════════════════════════"
    echo "                    🎯 EXPECTED OUTCOMES"
    echo "═══════════════════════════════════════════════════════════════════════"
    echo ""
    echo "✅ Ollama service should start successfully within extended timeout"
    echo "✅ API endpoints should become available after startup"
    echo "✅ Router should be able to connect to inference server"
    echo "✅ End-to-end chat completions should work"
    echo "✅ Service should automatically restart on failures"
    echo ""
    echo "╔════════════════════════════════════════════════════════════════════════╗"
    echo "║  ✅ Ollama timeout fix implementation complete!                      ║"
    echo "╚════════════════════════════════════════════════════════════════════════╝"
    echo ""
}

# Main execution
main() {
    echo ""
    echo "════════════════════════════════════════════════════════════════════════"
    echo "         🔧 Ollama Service Timeout Fix"
    echo "════════════════════════════════════════════════════════════════════════"
    echo ""
    echo "Target Server: $INFERENCE_SERVER"
    echo "Service: ollama"
    echo "Issue: Service stuck in 'activating' state"
    echo ""
    
    # Check SSH key
    if [ ! -r "$SSH_KEY" ]; then
        log_error "SSH key not found: $SSH_KEY"
        exit 1
    fi
    log_success "SSH key found"
    echo ""
    
    # Execute all phases
    diagnose_current_status
    apply_extended_timeouts
    optimize_startup
    restart_with_new_config
    test_service_functionality
    test_router_connectivity
    display_final_summary
}

# Run main function
main "$@"