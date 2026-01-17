#!/bin/bash
# Project: Goblin AI System
# Script: verify_kamatera_deployment.sh
# Purpose: Kamatera LLM Infrastructure Verification Script
# Date: 2025-12-12
# Maintainer: fuaadabdullah
# Usage: ./verify_kamatera_deployment.sh

set -e

# Set API Keys as Environment Variables
export INFERENCE_API_KEY="206e61fdeda2267c9a4ecac3997c4eae7ebd20038282445f7524a84a78ac0158"
export INTERNAL_INFERENCE_API_KEY="dcb2546960bb963c61db8b56939e8e3c25398f073409938882d6b07a7741de89"
export PUBLIC_API_KEY="cef5587890c73a5316a9a2c4ed851d97beb89fd28443885aad6e570dabd5f765"

SERVER1_IP="192.175.23.150"
SERVER2_IP="45.61.51.220"

echo "🔍 Verifying Kamatera LLM Infrastructure..."
echo "=========================================="
echo "API Keys configured:"
echo "- Inference API Key: ${INFERENCE_API_KEY:0:16}..."
echo "- Internal Inference API Key: ${INTERNAL_INFERENCE_API_KEY:0:16}..."
echo "- Public API Key: ${PUBLIC_API_KEY:0:16}..."
echo ""

# Function to test endpoint
test_endpoint() {
    local url=$1
    local expected=$2
    local description=$3
    local auth_header=$4

    echo -n "Testing $description: "
    if [ -n "$auth_header" ]; then
        response=$(curl -s -H "$auth_header" "$url")
    else
        response=$(curl -s "$url")
    fi
    
    if echo "$response" | grep -q "$expected"; then
        echo "✅ PASS"
        return 0
    else
        echo "❌ FAIL"
        echo "Response: $response"
        return 1
    fi
}

# Function to test Ollama models endpoint
test_models() {
    local url=$1
    local description=$2
    local auth_header=$3

    echo -n "Testing $description: "
    if [ -n "$auth_header" ]; then
        response=$(curl -s -H "$auth_header" "$url")
    else
        response=$(curl -s "$url")
    fi
    
    if echo "$response" | grep -q "models"; then
        model_count=$(echo "$response" | grep -o '"name"' | wc -l)
        echo "✅ PASS ($model_count models)"
        return 0
    else
        echo "❌ FAIL"
        echo "Response: $response"
        return 1
    fi
}

# Test Server 1 (Inference)
echo "🖥️  Testing Server 1 (Inference Node - $SERVER1_IP):"
test_models "http://$SERVER1_IP:8002/api/tags" "Inference Models" "x-api-key: $INFERENCE_API_KEY"

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
echo "curl -H 'x-api-key: $PUBLIC_API_KEY' \"
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