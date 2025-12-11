#!/bin/bash
# Complete Kamatera LLM Infrastructure Deployment Script
# Run this locally to deploy to both servers

set -e

# Server configuration
SERVER1_IP="192.175.23.150"  # Inference Node (4 CPU, 24GB RAM)
SERVER2_IP="45.61.51.220"    # Router Node (2 CPU, 12GB RAM)
SSH_KEY="~/.ssh/kamatera_raptor"

echo "🚀 Starting complete LLM infrastructure deployment..."

# Function to run command on server
run_on_server() {
    local server_ip=$1
    local command=$2
    echo "📡 Running on $server_ip: $command"
    ssh -i "$SSH_KEY" -o ConnectTimeout=30 -o StrictHostKeyChecking=no root@$server_ip "$command"
}

# Function to copy file to server
copy_to_server() {
    local server_ip=$1
    local file=$2
    echo "📤 Copying $file to $server_ip..."
    scp -i "$SSH_KEY" -o ConnectTimeout=30 -o StrictHostKeyChecking=no "$file" root@$server_ip:~/
}

echo "📋 Step 1: Copying bootstrap scripts to servers..."

# Copy scripts to servers
copy_to_server "$SERVER1_IP" "bootstrap_inference.sh"
copy_to_server "$SERVER2_IP" "bootstrap_router.sh"

echo "⚙️ Step 2: Running bootstrap on Server 1 (Inference Node)..."
run_on_server "$SERVER1_IP" "chmod +x bootstrap_inference.sh && ./bootstrap_inference.sh"

echo "🌐 Step 3: Running bootstrap on Server 2 (Router Node)..."
run_on_server "$SERVER2_IP" "chmod +x bootstrap_router.sh && ./bootstrap_router.sh"

echo "🔧 Step 4: Post-deployment configuration..."

# Configure rclone on Server 1
echo "📁 Setting up rclone on Server 1..."
run_on_server "$SERVER1_IP" "curl https://rclone.org/install.sh | bash"
echo "⚠️  MANUAL STEP REQUIRED: Configure rclone on Server 1"
echo "   Run: ssh -i $SSH_KEY root@$SERVER1_IP"
echo "   Then: rclone config (set up Google Drive access)"

# Install Ollama models on Server 1
echo "🤖 Installing Ollama models on Server 1..."
run_on_server "$SERVER1_IP" "curl -fsSL https://ollama.ai/install.sh | sh"
run_on_server "$SERVER1_IP" "ollama pull phi3:3.8b"
run_on_server "$SERVER1_IP" "ollama pull gemma:2b"

# Get API keys from Server 1
echo "🔑 Retrieving API keys from Server 1..."
INFERENCE_KEY=$(run_on_server "$SERVER1_IP" "grep 'LOCAL_LLM_API_KEY' /etc/systemd/system/local-llm-proxy.service | cut -d'=' -f2")
echo "Inference API Key: $INFERENCE_KEY"

# Update router configuration
echo "🔄 Updating router configuration on Server 2..."
run_on_server "$SERVER2_IP" "sed -i 's|REPLACE_WITH_INFERENCE_KEY|$INFERENCE_KEY|g' /etc/systemd/system/goblin-router.service"
run_on_server "$SERVER2_IP" "systemctl daemon-reload && systemctl restart goblin-router"

echo "✅ Step 5: Verification..."

# Test services
echo "🧪 Testing inference server health..."
run_on_server "$SERVER1_IP" "curl -s http://localhost:8002/health"

echo "🧪 Testing router server health..."
run_on_server "$SERVER2_IP" "curl -s http://localhost:8000/health"

echo "🎉 Deployment complete!"
echo ""
echo "📊 Server Information:"
echo "Server 1 (Inference): $SERVER1_IP - 4 CPU, 24GB RAM, 200GB disk"
echo "Server 2 (Router): $SERVER2_IP - 2 CPU, 12GB RAM, 80GB disk"
echo ""
echo "🔗 API Endpoints:"
echo "Router Public API: http://$SERVER2_IP:8000/v1/chat/completions"
echo "Inference Internal: http://$SERVER1_IP:8002/chat/completions"
echo ""
echo "🔑 API Keys:"
echo "Public API Key: $(run_on_server "$SERVER2_IP" "grep 'PUBLIC_API_KEY' /etc/systemd/system/goblin-router.service | cut -d'=' -f2")"
echo "Inference API Key: $INFERENCE_KEY"
echo ""
echo "📋 Next Steps:"
echo "1. Set up domain and TLS on Server 2: certbot --nginx -d yourdomain.com"
echo "2. Copy models to Server 1: rclone copy gdrive:models /srv/models/active"
echo "3. Test end-to-end API calls"
echo "4. Set up monitoring and logging"
