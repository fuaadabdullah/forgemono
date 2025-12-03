#!/bin/bash
set -e

echo "🚀 Local LLM Deployment Script"
echo "Run this on your local machine with access to Kamatera server"

# Configuration
SERVER_IP="45.61.60.3"
SSH_KEY="$HOME/kamatera_key"
DEPLOY_DIR="$HOME/ForgeMonorepo/apps/goblin-assistant/backend"

# Check SSH key
if [ ! -f "$SSH_KEY" ]; then
    echo "❌ SSH key not found at $SSH_KEY"
    exit 1
fi
chmod 600 "$SSH_KEY"
echo "✅ SSH key ready"

# Test connection
echo "Testing SSH connection..."
if ! ssh -i "$SSH_KEY" -o ConnectTimeout=10 root@$SERVER_IP "echo 'Connected'"; then
    echo "❌ Cannot connect to server"
    exit 1
fi
echo "✅ SSH connection successful"

# Transfer files
echo "Transferring deployment files..."
cd "$DEPLOY_DIR"
scp -i "$SSH_KEY" local_llm_proxy.py local-llm-proxy.service nginx-local-llm.conf bootstrap_llm.sh root@$SERVER_IP:/tmp/
echo "✅ Files transferred"

# Setup server
echo "Setting up server..."
ssh -i "$SSH_KEY" root@$SERVER_IP << 'ENDSSH'
apt update && apt upgrade -y
apt install -y curl wget git python3 python3-pip python3-venv nginx rclone ufw build-essential cmake
curl -fsSL https://ollama.ai/install.sh | sh
mkdir -p ~/llm-deployment
cd ~/llm-deployment
mv /tmp/local_llm_proxy.py /tmp/local-llm-proxy.service /tmp/nginx-local-llm.conf /tmp/bootstrap_llm.sh ./
chmod +x bootstrap_llm.sh
ufw --force enable
ufw allow 22/tcp 80/tcp 443/tcp
echo "✅ Server setup complete"
ENDSSH

# Run bootstrap
echo "Running bootstrap script..."
ssh -i "$SSH_KEY" root@$SERVER_IP << 'ENDSSH'
cd ~/llm-deployment
./bootstrap_llm.sh
ENDSSH

echo "🎉 Deployment completed!"
echo ""
echo "Next steps:"
echo "1. Configure rclone: ssh -i ~/kamatera_key root@$SERVER_IP 'rclone config'"
echo "2. Test proxy: curl http://$SERVER_IP:8002/health"
echo "3. Update backend config with LOCAL_LLM_PROXY_URL=http://$SERVER_IP:8002"
