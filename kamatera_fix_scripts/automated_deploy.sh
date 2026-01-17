#!/bin/bash
# Kamatera Automated Fix Deployment Script
# This script attempts to deploy the firewall fixes to both servers

set -e

INFERENCE_SERVER="192.175.23.150"
ROUTER_SERVER="45.61.51.220"
USER="root"

echo "🚀 KAMATERA NETWORK FIX - AUTOMATED DEPLOYMENT"
echo "=============================================="

# Function to deploy to a server
deploy_to_server() {
    local server_ip=$1
    local server_name=$2
    
    echo "🔧 Deploying to $server_name ($server_ip)..."
    
    # Check if we can SSH
    if ssh -o ConnectTimeout=5 -o BatchMode=yes $USER@$server_ip "echo 'SSH access confirmed'" 2>/dev/null; then
        echo "✅ SSH access available for $server_name"
        
        # Copy firewall fix script
        echo "📤 Copying firewall_fix.sh to $server_name..."
        scp -q kamatera_fix_scripts/firewall_fix.sh $USER@$server_ip:/tmp/
        
        # Execute firewall fix
        echo "🔧 Running firewall configuration on $server_name..."
        ssh $USER@$server_ip "sudo bash /tmp/firewall_fix.sh"
        
        # Restart services based on server type
        if [[ "$server_name" == *"Inference"* ]]; then
            echo "🔄 Restarting local-llm-proxy service..."
            ssh $USER@$server_ip "sudo systemctl restart local-llm-proxy"
        else
            echo "🔄 Restarting goblin-router service..."
            ssh $USER@$server_ip "sudo systemctl restart goblin-router"
        fi
        
        echo "✅ $server_name deployment completed"
    else
        echo "❌ Cannot access $server_name via SSH"
        echo "📋 Manual deployment required for $server_name:"
        echo "   ssh $USER@$server_ip"
        echo "   sudo bash /tmp/firewall_fix.sh"
        if [[ "$server_name" == *"Inference"* ]]; then
            echo "   sudo systemctl restart local-llm-proxy"
        else
            echo "   sudo systemctl restart goblin-router"
        fi
    fi
    echo ""
}

# Deploy to both servers
deploy_to_server $INFERENCE_SERVER "Inference Server"
deploy_to_server $ROUTER_SERVER "Router Server"

# Test connectivity after deployment
echo "🧪 Testing connectivity after deployment..."
echo ""

echo "Testing Inference Server..."
curl -s http://$INFERENCE_SERVER:8002/api/tags >/dev/null && echo "✅ Inference API working" || echo "❌ Inference API failed"

echo "Testing Router Server..."
curl -s http://$ROUTER_SERVER:8000/api/tags >/dev/null && echo "✅ Router API working" || echo "❌ Router API failed"

echo "Testing Router Health..."
curl -s http://$ROUTER_SERVER:8000/api/tags | grep -q '"healthy":true' && echo "✅ Router-to-Inference connectivity restored!" || echo "❌ Router-to-Inference still blocked"

echo ""
echo "🎯 Final End-to-End Test..."
RESPONSE=$(curl -s -X POST http://$ROUTER_SERVER:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -H 'x-api-key: cef5587890c73a5316a9a2c4ed851d97beb89fd28443885aad6e570dabd5f765' \
  -d '{"model":"phi3:latest","messages":[{"role":"user","content":"Hello"}]}' 2>/dev/null || echo '{"error": "failed"}')

if echo "$RESPONSE" | grep -q '"content"'; then
    echo "🎉 SUCCESS! Full chat flow is working!"
    echo "📊 Response preview: $(echo "$RESPONSE" | head -c 100)..."
else
    echo "⚠️ Chat flow still failing: $RESPONSE"
    echo "🔍 Check server logs and firewall configuration"
fi

echo ""
echo "📋 DEPLOYMENT SUMMARY:"
echo "================================"
echo "✅ Firewall configuration scripts created"
echo "✅ Deployment scripts generated"
echo "✅ Testing tools provided"
echo "✅ Manual deployment instructions available"
echo ""
echo "If automated deployment failed, use the manual commands in INSTRUCTIONS.md"