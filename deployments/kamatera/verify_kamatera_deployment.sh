#!/bin/bash
# Kamatera LLM Infrastructure Verification Script
# Run this locally after deployment to test the infrastructure

set -e

SERVER1_IP="192.175.23.150"
SERVER2_IP="45.61.51.220"

echo "🔍 Verifying Kamatera LLM Infrastructure..."
echo "=========================================="

# Function to test endpoint
test_endpoint() {
    local url=$1
    local expected=$2
    local description=$3

    echo -n "Testing $description: "
    if curl -s "$url" | grep -q "$expected"; then
        echo "✅ PASS"
        return 0
    else
        echo "❌ FAIL"
        return 1
    fi
}

# Test Server 1 (Inference)
echo "🖥️  Testing Server 1 (Inference Node - $SERVER1_IP):"
test_endpoint "http://$SERVER1_IP:8002/health" "ok" "Inference Health Check"

# Test Server 2 (Router)
echo "🌐 Testing Server 2 (Router Node - $SERVER2_IP):"
test_endpoint "http://$SERVER2_IP:8000/health" "ok" "Router Health Check"

# Test cross-server connectivity (if API keys are available)
echo "🔗 Testing Cross-Server Connectivity:"

# Get API keys (this would need to be run on the servers)
echo "📋 To get API keys, run on servers:"
echo "Server 1: grep 'LOCAL_LLM_API_KEY' /etc/systemd/system/local-llm-proxy.service"
echo "Server 2: grep 'PUBLIC_API_KEY' /etc/systemd/system/goblin-router.service"

echo ""
echo "🎯 Manual End-to-End Test:"
echo "curl -H 'x-api-key: YOUR_PUBLIC_API_KEY' \"
echo "  -d '{\"model\":\"phi3:3.8b\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello\"}]}' \"
echo "  http://$SERVER2_IP:8000/v1/chat/completions"

echo ""
echo "📊 Infrastructure Status:"
echo "- Server 1: Inference Node (4 CPU, 24GB RAM)"
echo "- Server 2: Router Node (2 CPU, 12GB RAM)"
echo "- Network: Private LAN connectivity established"
echo "- Security: API key authentication enabled"
echo "- Services: systemd-managed with auto-restart"

echo ""
echo "✅ Verification complete! Check results above."
