#!/usr/bin/env bash
# ============================================================================
# Manual Router Network Fix - Step by Step Instructions
# ============================================================================
# 
# This script provides step-by-step commands to run on each server to fix
# the "All servers unavailable" issue.
#
# Issue: Router (45.61.51.220) cannot reach Inference (192.175.23.150:8002)
# Root Cause: 
#   1. Firewall blocks traffic between servers
#   2. INFERENCE_URL configured as 172.16.0.1 (wrong IP)
#
# ============================================================================

set -e

# Configuration
INFERENCE_IP="192.175.23.150"
ROUTER_IP="45.61.51.220"
INFERENCE_PORT="8002"
ROUTER_PORT="8000"

echo ""
echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║          🔧 Kamatera Router Network Fix - Manual Steps                 ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""

# ============================================================================
# STEP 1: FIX FIREWALL ON INFERENCE SERVER
# ============================================================================

echo "═══════════════════════════════════════════════════════════════════════════"
echo "STEP 1: Configure Firewall on Inference Server (${INFERENCE_IP})"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "Run these commands ON THE INFERENCE SERVER (${INFERENCE_IP}):"
echo ""
echo "  # Allow Router to connect on port 8002"
echo "  sudo ufw allow from ${ROUTER_IP} to any port ${INFERENCE_PORT}"
echo ""
echo "  # Verify the rule"
echo "  sudo ufw status"
echo ""
echo "Example SSH command:"
echo "  ssh root@${INFERENCE_IP} 'sudo ufw allow from ${ROUTER_IP} to any port ${INFERENCE_PORT}'"
echo ""

# ============================================================================
# STEP 2: FIX FIREWALL ON ROUTER SERVER
# ============================================================================

echo "═══════════════════════════════════════════════════════════════════════════"
echo "STEP 2: Configure Firewall on Router Server (${ROUTER_IP})"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "Run these commands ON THE ROUTER SERVER (${ROUTER_IP}):"
echo ""
echo "  # Allow outbound connections to Inference server"
echo "  sudo ufw allow out to ${INFERENCE_IP} port ${INFERENCE_PORT}"
echo ""
echo "  # Or allow all outbound (if above doesn't work)"
echo "  sudo ufw allow out on eth0 to ${INFERENCE_IP} port ${INFERENCE_PORT}"
echo ""
echo "  # Verify the rules"
echo "  sudo ufw status"
echo ""
echo "Example SSH command:"
echo "  ssh root@${ROUTER_IP} 'sudo ufw allow out to ${INFERENCE_IP} port ${INFERENCE_PORT}'"
echo ""

# ============================================================================
# STEP 3: UPDATE ROUTER CONFIGURATION
# ============================================================================

echo "═══════════════════════════════════════════════════════════════════════════"
echo "STEP 3: Update Router Configuration with Correct Inference IP"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "The router is currently configured to use 172.16.0.1 but should use ${INFERENCE_IP}"
echo ""
echo "Run these commands ON THE ROUTER SERVER (${ROUTER_IP}):"
echo ""
echo "  # Update systemd service file"
echo "  sudo sed -i 's|Environment=\"INFERENCE_URL=.*\"|Environment=\"INFERENCE_URL=http://${INFERENCE_IP}:${INFERENCE_PORT}\"|' /etc/systemd/system/goblin-router.service"
echo ""
echo "  # Reload systemd configuration"
echo "  sudo systemctl daemon-reload"
echo ""
echo "  # Verify the change"
echo "  sudo grep INFERENCE_URL /etc/systemd/system/goblin-router.service"
echo ""
echo "Expected output:"
echo "  Environment=\"INFERENCE_URL=http://${INFERENCE_IP}:${INFERENCE_PORT}\""
echo ""

# ============================================================================
# STEP 4: RESTART SERVICES
# ============================================================================

echo "═══════════════════════════════════════════════════════════════════════════"
echo "STEP 4: Restart Services"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "A) ON INFERENCE SERVER (${INFERENCE_IP}):"
echo ""
echo "  # Restart the LLM inference service"
echo "  sudo systemctl restart local-llm-proxy"
echo ""
echo "  # Or if using ollama:"
echo "  sudo systemctl restart ollama"
echo ""
echo "  # Wait for service to start"
echo "  sleep 5"
echo ""
echo "  # Check status"
echo "  sudo systemctl status local-llm-proxy --no-pager"
echo ""
echo "B) ON ROUTER SERVER (${ROUTER_IP}):"
echo ""
echo "  # Restart the router service"
echo "  sudo systemctl restart goblin-router"
echo ""
echo "  # Wait for service to start"
echo "  sleep 5"
echo ""
echo "  # Check status"
echo "  sudo systemctl status goblin-router --no-pager"
echo ""

# ============================================================================
# STEP 5: TEST CONNECTIVITY
# ============================================================================

echo "═══════════════════════════════════════════════════════════════════════════"
echo "STEP 5: Test Connectivity"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "Test 1: Can Router reach Inference Server?"
echo ""
echo "  Run on ROUTER SERVER (${ROUTER_IP}):"
echo "  curl -v http://${INFERENCE_IP}:${INFERENCE_PORT}/health -H 'X-API-Key: 206e61fdeda2267c9a4ecac3997c4eae7ebd20038282445f7524a84a78ac0158'"
echo ""
echo "  Expected: HTTP 200 with health check response"
echo ""
echo "Test 2: TCP port test from Router to Inference"
echo ""
echo "  Run on ROUTER SERVER (${ROUTER_IP}):"
echo "  timeout 5 bash -c 'echo > /dev/tcp/${INFERENCE_IP}/${INFERENCE_PORT}' && echo 'Port open' || echo 'Port closed'"
echo ""
echo "  Expected: 'Port open'"
echo ""

# ============================================================================
# STEP 6: TEST END-TO-END CHAT
# ============================================================================

echo "═══════════════════════════════════════════════════════════════════════════"
echo "STEP 6: Test End-to-End Chat Completion"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "Test the full chat flow from Router API:"
echo ""
echo "  curl -X POST http://${ROUTER_IP}:${ROUTER_PORT}/v1/chat/completions \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -H 'X-API-Key: cef5587890c73a5316a9a2c4ed851d97beb89fd28443885aad6e570dabd5f765' \\"
echo "    -d '{'"
echo "      \"model\": \"llama2:7b\","
echo "      \"messages\": [{\"role\": \"user\", \"content\": \"Say hello in one word\"}],"
echo "      \"temperature\": 0.7"
echo "    }'"
echo ""
echo "  Expected: Chat completion response with content"
echo "  NOT: {\"detail\":\"All servers unavailable\"}"
echo ""

# ============================================================================
# STEP 7: TROUBLESHOOTING
# ============================================================================

echo "═══════════════════════════════════════════════════════════════════════════"
echo "STEP 7: Troubleshooting Commands"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "If chat still fails, run these diagnostics:"
echo ""
echo "On ROUTER SERVER (${ROUTER_IP}):"
echo ""
echo "  # Check Router logs"
echo "  sudo journalctl -u goblin-router -f"
echo ""
echo "  # Check if Router service is running"
echo "  sudo systemctl status goblin-router"
echo ""
echo "  # Check if port 8000 is listening"
echo "  sudo ss -tlnp | grep 8000"
echo ""
echo "  # Check network routes"
echo "  ip route"
echo ""
echo "  # Test DNS resolution"
echo "  nslookup ${INFERENCE_IP}"
echo ""
echo "On INFERENCE SERVER (${INFERENCE_IP}):"
echo ""
echo "  # Check if port 8002 is listening"
echo "  sudo ss -tlnp | grep 8002"
echo ""
echo "  # Check firewall rules"
echo "  sudo ufw status verbose"
echo ""
echo "  # Check service logs"
echo "  sudo journalctl -u local-llm-proxy -f"
echo ""
echo "  # Test local connectivity"
echo "  curl http://localhost:8002/health"
echo ""

# ============================================================================
# SUMMARY
# ============================================================================

echo "═══════════════════════════════════════════════════════════════════════════"
echo "SUMMARY OF ACTIONS"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "1. ✓ Firewall on Inference (${INFERENCE_IP}): Allow from ${ROUTER_IP} port ${INFERENCE_PORT}"
echo "2. ✓ Firewall on Router (${ROUTER_IP}): Allow out to ${INFERENCE_IP} port ${INFERENCE_PORT}"
echo "3. ✓ Router config: Update INFERENCE_URL from 172.16.0.1 to ${INFERENCE_IP}"
echo "4. ✓ Restart: local-llm-proxy on Inference, goblin-router on Router"
echo "5. ✓ Test: Verify connectivity with curl commands"
echo "6. ✓ Chat: Test end-to-end chat completion"
echo ""
echo "After applying these fixes, chat completions should work!"
echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
