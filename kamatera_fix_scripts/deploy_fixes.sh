#!/bin/bash
# Kamatera Server Deployment Script
# Run this script to deploy the firewall fixes to both servers

echo "🚀 KAMATERA NETWORK FIX DEPLOYMENT"
echo "======================================"

# Check if we have SSH access to both servers
INFERENCE_SERVER="192.175.23.150"
ROUTER_SERVER="45.61.51.220"
USER="root"

echo "🔍 Checking server connectivity..."

# Test inference server
echo "Testing Inference Server ($INFERENCE_SERVER)..."
ping -c 1 $INFERENCE_SERVER >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Inference server reachable"
else
    echo "❌ Inference server unreachable"
    exit 1
fi

# Test router server  
echo "Testing Router Server ($ROUTER_SERVER)..."
ping -c 1 $ROUTER_SERVER >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Router server reachable"
else
    echo "❌ Router server unreachable"
    exit 1
fi

echo ""
echo "📋 DEPLOYMENT STEPS:"
echo "1. Copy fix scripts to both servers"
echo "2. Execute firewall configuration"
echo "3. Restart services"
echo "4. Verify connectivity"

echo ""
echo "⚠️  IMPORTANT: This script will attempt to deploy fixes to:"
echo "   - $INFERENCE_SERVER (Inference Server)"
echo "   - $ROUTER_SERVER (Router Server)"
echo ""
echo "Make sure you have SSH access configured for both servers."

# Generate deployment commands
echo ""
echo "📋 MANUAL DEPLOYMENT COMMANDS:"
echo "================================"
echo ""
echo "# On Inference Server ($INFERENCE_SERVER):"
echo "ssh $USER@$INFERENCE_SERVER"
echo "sudo cp /root/firewall_fix.sh /tmp/"
echo "sudo bash /tmp/firewall_fix.sh"
echo "sudo systemctl restart local-llm-proxy"
echo "sudo systemctl status local-llm-proxy"
echo ""
echo "# On Router Server ($ROUTER_SERVER):"
echo "ssh $USER@$ROUTER_SERVER"
echo "sudo cp /root/firewall_fix.sh /tmp/"
echo "sudo bash /tmp/firewall_fix.sh"
echo "sudo systemctl restart goblin-router"
echo "sudo systemctl status goblin-router"
echo ""
echo "# Test connectivity:"
echo "curl -s http://$INFERENCE_SERVER:8002/api/tags | jq ."
echo "curl -s http://$ROUTER_SERVER:8000/api/tags | jq ."
echo ""
echo "# Full end-to-end test:"
echo "curl -s -X POST http://$ROUTER_SERVER:8000/v1/chat/completions \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -H 'x-api-key: cef5587890c73a5316a9a2c4ed851d97beb89fd28443885aad6e570dabd5f765' \\"
echo "  -d '{\"model\":\"phi3:latest\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello\"}]}'"

echo ""
echo "✅ Deployment guide generated!"
echo "📄 Check kamatera_fix_scripts/ directory for all deployment files"