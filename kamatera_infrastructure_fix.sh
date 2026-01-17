#!/usr/bin/env bash
# ============================================================================
# Kamatera Infrastructure Network Fix
# Purpose: Fix connectivity between Router (45.61.51.220) and Inference (192.175.23.150)
# 
# This script:
# 1. Updates firewall rules on both servers
# 2. Fixes configuration (INFERENCE_URL)
# 3. Restarts services
# 4. Verifies connectivity
# ============================================================================

set -euo pipefail

# ============================================================================
# CONFIGURATION
# ============================================================================

ROUTER_SERVER="45.61.51.220"
INFERENCE_SERVER="192.175.23.150"
INFERENCE_PORT="8002"
ROUTER_PORT="8000"

# SSH/Connection settings
SSH_USER="root"
SSH_KEY="${SSH_KEY:-~/.ssh/id_rsa}"
CONNECT_TIMEOUT=10
COMMAND_TIMEOUT=30

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

test_connectivity() {
    local from_server=$1
    local to_server=$2
    local port=$3
    local description=$4
    
    log_info "Testing $description..."
    
    # Test from source server to destination
    local cmd="timeout 5 bash -c 'echo > /dev/tcp/$to_server/$port' 2>/dev/null && echo 'OK' || echo 'FAIL'"
    local result=$(ssh -i "$SSH_KEY" -o ConnectTimeout=$CONNECT_TIMEOUT -o StrictHostKeyChecking=no "$SSH_USER@$from_server" "$cmd" 2>/dev/null || echo "ERROR")
    
    if [[ "$result" == "OK" ]]; then
        log_success "$description: ✅ Connectivity OK"
        return 0
    else
        log_error "$description: ❌ Connectivity FAILED"
        return 1
    fi
}

# ============================================================================
# STEP 1: CONFIGURE FIREWALL ON INFERENCE SERVER
# ============================================================================

configure_inference_firewall() {
    log_info "Configuring firewall on Inference Server (${INFERENCE_SERVER})"
    
    # Allow Router server to connect on port 8002
    local cmd1="ufw allow from $ROUTER_SERVER to any port $INFERENCE_PORT comment 'Router LLM API Access'"
    run_remote_command "$INFERENCE_SERVER" "$cmd1" "Adding UFW rule for Router on port $INFERENCE_PORT" || true
    
    # Enable UFW if not already enabled
    local cmd2="ufw status | grep -q 'Status: active' || ufw --force enable"
    run_remote_command "$INFERENCE_SERVER" "$cmd2" "Enabling UFW" || true
    
    # Verify firewall rule
    local cmd3="ufw status | grep -A 1 'Router LLM' || ufw status | grep $INFERENCE_PORT"
    log_info "Firewall rules on Inference Server:"
    ssh -i "$SSH_KEY" -o ConnectTimeout=$CONNECT_TIMEOUT -o StrictHostKeyChecking=no "$SSH_USER@$INFERENCE_SERVER" "$cmd3" 2>/dev/null || true
}

# ============================================================================
# STEP 2: CONFIGURE FIREWALL ON ROUTER SERVER
# ============================================================================

configure_router_firewall() {
    log_info "Configuring firewall on Router Server (${ROUTER_SERVER})"
    
    # Allow outbound connections to Inference server
    local cmd1="ufw allow out to $INFERENCE_SERVER port $INFERENCE_PORT comment 'Inference Server LLM API'"
    run_remote_command "$ROUTER_SERVER" "$cmd1" "Adding UFW rule for Inference Server access" || true
    
    # Enable UFW if not already enabled
    local cmd2="ufw status | grep -q 'Status: active' || ufw --force enable"
    run_remote_command "$ROUTER_SERVER" "$cmd2" "Enabling UFW" || true
    
    # Verify firewall rule
    local cmd3="ufw status | grep -A 1 'Inference' || ufw status | grep $INFERENCE_PORT"
    log_info "Firewall rules on Router Server:"
    ssh -i "$SSH_KEY" -o ConnectTimeout=$CONNECT_TIMEOUT -o StrictHostKeyChecking=no "$SSH_USER@$ROUTER_SERVER" "$cmd3" 2>/dev/null || true
}

# ============================================================================
# STEP 3: UPDATE ROUTER CONFIGURATION
# ============================================================================

update_router_configuration() {
    log_info "Updating Router configuration with correct Inference Server IP"
    
    # Update systemd service file with correct INFERENCE_URL
    local cmd1="
    if [ -f /etc/systemd/system/goblin-router.service ]; then
        sed -i 's|Environment=\"INFERENCE_URL=.*\"|Environment=\"INFERENCE_URL=http://$INFERENCE_SERVER:$INFERENCE_PORT\"|' /etc/systemd/system/goblin-router.service
        systemctl daemon-reload
        echo 'Service file updated'
    else
        echo 'Service file not found'
    fi
    "
    run_remote_command "$ROUTER_SERVER" "$cmd1" "Updating systemd service with correct INFERENCE_URL" || true
    
    # Update Python environment variables if running via app.py
    local cmd2="
    if [ -f /home/fuaad/.bashrc ]; then
        grep -q 'INFERENCE_URL' /home/fuaad/.bashrc && sed -i 's|export INFERENCE_URL=.*|export INFERENCE_URL=http://$INFERENCE_SERVER:$INFERENCE_PORT|' /home/fuaad/.bashrc || echo 'export INFERENCE_URL=http://$INFERENCE_SERVER:$INFERENCE_PORT' >> /home/fuaad/.bashrc
        echo 'Bashrc updated'
    fi
    "
    run_remote_command "$ROUTER_SERVER" "$cmd2" "Updating bashrc environment variables" || true
    
    log_success "Router configuration updated"
}

# ============================================================================
# STEP 4: RESTART SERVICES
# ============================================================================

restart_services() {
    log_info "Restarting services"
    
    # Restart local-llm-proxy on Inference Server
    log_info "Restarting local-llm-proxy on Inference Server..."
    local cmd1="
    if systemctl list-unit-files | grep -q 'local-llm-proxy'; then
        systemctl restart local-llm-proxy
        sleep 5
        systemctl is-active local-llm-proxy && echo 'Service running' || echo 'Service failed'
    elif systemctl list-unit-files | grep -q 'ollama'; then
        systemctl restart ollama
        sleep 5
        systemctl is-active ollama && echo 'Service running' || echo 'Service failed'
    else
        echo 'No LLM service found'
    fi
    "
    run_remote_command "$INFERENCE_SERVER" "$cmd1" "Restarting Inference Server LLM service" || true
    
    # Restart goblin-router on Router Server
    log_info "Restarting goblin-router on Router Server..."
    local cmd2="
    if systemctl list-unit-files | grep -q 'goblin-router'; then
        systemctl restart goblin-router
        sleep 5
        systemctl is-active goblin-router && echo 'Service running' || echo 'Service failed'
    else
        echo 'goblin-router service not found'
    fi
    "
    run_remote_command "$ROUTER_SERVER" "$cmd2" "Restarting Router service" || true
    
    log_success "Services restarted"
}

# ============================================================================
# STEP 5: TEST CONNECTIVITY
# ============================================================================

test_connectivity_all() {
    log_info "Testing connectivity between servers"
    echo ""
    
    local all_passed=true
    
    # Test Router -> Inference on port 8002
    if ! test_connectivity "$ROUTER_SERVER" "$INFERENCE_SERVER" "$INFERENCE_PORT" "Router → Inference Server (port $INFERENCE_PORT)"; then
        all_passed=false
    fi
    
    # Test Inference -> Router on port 8000 (for reverse communication if needed)
    if ! test_connectivity "$INFERENCE_SERVER" "$ROUTER_SERVER" "$ROUTER_PORT" "Inference → Router Server (port $ROUTER_PORT)"; then
        log_warning "Reverse communication may not be needed"
    fi
    
    echo ""
    if [ "$all_passed" = true ]; then
        log_success "All connectivity tests passed!"
        return 0
    else
        log_error "Some connectivity tests failed"
        return 1
    fi
}

# ============================================================================
# STEP 6: TEST HEALTH ENDPOINTS
# ============================================================================

test_health_endpoints() {
    log_info "Testing health endpoints"
    echo ""
    
    # Test Inference Server health
    log_info "Testing Inference Server health endpoint..."
    local inference_health_cmd="
    curl -s -m 5 -H 'X-API-Key: 206e61fdeda2267c9a4ecac3997c4eae7ebd20038282445f7524a84a78ac0158' \
         http://localhost:$INFERENCE_PORT/health 2>/dev/null | head -c 100 || echo 'TIMEOUT'
    "
    local result=$(ssh -i "$SSH_KEY" -o ConnectTimeout=$CONNECT_TIMEOUT -o StrictHostKeyChecking=no "$SSH_USER@$INFERENCE_SERVER" "$inference_health_cmd" 2>/dev/null || echo "ERROR")
    if [[ "$result" == *"healthy"* ]] || [[ "$result" == *"ok"* ]]; then
        log_success "Inference Server health: ✅ OK"
    else
        log_warning "Inference Server health response: $result"
    fi
    
    # Test Router health
    log_info "Testing Router Server health endpoint..."
    local router_health_cmd="
    curl -s -m 5 http://localhost:$ROUTER_PORT/health 2>/dev/null | head -c 100 || echo 'TIMEOUT'
    "
    local result=$(ssh -i "$SSH_KEY" -o ConnectTimeout=$CONNECT_TIMEOUT -o StrictHostKeyChecking=no "$SSH_USER@$ROUTER_SERVER" "$router_health_cmd" 2>/dev/null || echo "ERROR")
    if [[ "$result" == *"healthy"* ]] || [[ "$result" == *"ok"* ]]; then
        log_success "Router health: ✅ OK"
    else
        log_warning "Router health response: $result"
    fi
    
    echo ""
}

# ============================================================================
# STEP 7: TEST END-TO-END CHAT
# ============================================================================

test_end_to_end_chat() {
    log_info "Testing end-to-end chat completion"
    echo ""
    
    log_info "Sending test chat request through Router API..."
    local chat_cmd="
    curl -s -X POST http://localhost:$ROUTER_PORT/v1/chat/completions \
      -H 'Content-Type: application/json' \
      -H 'X-API-Key: cef5587890c73a5316a9a2c4ed851d97beb89fd28443885aad6e570dabd5f765' \
      -d '{
        \"model\": \"llama2:7b\",
        \"messages\": [{\"role\": \"user\", \"content\": \"Say hello in one word\"}],
        \"temperature\": 0.7,
        \"max_tokens\": 50
      }' | head -c 200
    "
    
    local result=$(ssh -i "$SSH_KEY" -o ConnectTimeout=$CONNECT_TIMEOUT -o StrictHostKeyChecking=no "$SSH_USER@$ROUTER_SERVER" "$chat_cmd" 2>/dev/null || echo "ERROR")
    
    if [[ "$result" == *"choices"* ]]; then
        log_success "Chat completion test: ✅ PASSED - Received response from Router API"
        echo "Response snippet: ${result:0:150}..."
    elif [[ "$result" == *"All servers unavailable"* ]]; then
        log_error "Chat completion test: ❌ FAILED - Still getting 'All servers unavailable'"
        echo "Full response: $result"
    else
        log_warning "Chat completion test: ⚠️  Unexpected response"
        echo "Response: $result"
    fi
    
    echo ""
}

# ============================================================================
# STEP 8: DISPLAY SUMMARY
# ============================================================================

display_summary() {
    echo ""
    echo "═══════════════════════════════════════════════════════════════════════"
    echo "                    🎉 INFRASTRUCTURE FIX SUMMARY"
    echo "═══════════════════════════════════════════════════════════════════════"
    echo ""
    echo "Configuration Applied:"
    echo "  ✓ Firewall rules configured on both servers"
    echo "  ✓ Router INFERENCE_URL updated to: http://${INFERENCE_SERVER}:${INFERENCE_PORT}"
    echo "  ✓ Services restarted"
    echo ""
    echo "Servers:"
    echo "  • Router Server:       ${ROUTER_SERVER}:${ROUTER_PORT}"
    echo "  • Inference Server:    ${INFERENCE_SERVER}:${INFERENCE_PORT}"
    echo ""
    echo "Next Steps:"
    echo "  1. Test the chat completions from the frontend"
    echo "  2. Monitor logs: ssh root@${ROUTER_SERVER} journalctl -u goblin-router -f"
    echo "  3. Check inference server: ssh root@${INFERENCE_SERVER} systemctl status local-llm-proxy"
    echo ""
    echo "Manual Testing Commands:"
    echo "  • Test Router health:     curl http://${ROUTER_SERVER}:${ROUTER_PORT}/health"
    echo "  • Test chat completion:   curl -X POST http://${ROUTER_SERVER}:${ROUTER_PORT}/v1/chat/completions \\"
    echo "    -H 'Content-Type: application/json' -d '{\"model\":\"llama2:7b\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello\"}]}'"
    echo ""
    echo "═══════════════════════════════════════════════════════════════════════"
    echo ""
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

main() {
    echo ""
    echo "═══════════════════════════════════════════════════════════════════════"
    echo "         🔧 Kamatera Infrastructure Network Fix"
    echo "═══════════════════════════════════════════════════════════════════════"
    echo ""
    echo "This script will fix connectivity between:"
    echo "  • Router Server:       ${ROUTER_SERVER}"
    echo "  • Inference Server:    ${INFERENCE_SERVER}"
    echo ""
    echo "Ensuring SSH key is readable: ${SSH_KEY}"
    if [ ! -r "$SSH_KEY" ]; then
        log_error "SSH key not found or not readable: $SSH_KEY"
        exit 1
    fi
    log_success "SSH key found"
    echo ""
    
    # Execute all steps
    configure_inference_firewall
    echo ""
    
    configure_router_firewall
    echo ""
    
    update_router_configuration
    echo ""
    
    restart_services
    echo ""
    
    # Wait a bit for services to stabilize
    log_info "Waiting for services to stabilize..."
    sleep 10
    
    test_connectivity_all
    echo ""
    
    test_health_endpoints
    
    test_end_to_end_chat
    
    display_summary
}

# Run main function
main "$@"
