#!/bin/bash
set -e

echo "🚀 Starting Local LLM Deployment to Kamatera VPS"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SERVER_IP="45.61.60.3"
SSH_KEY="$HOME/kamatera_key"
DEPLOY_DIR="$HOME/ForgeMonorepo/apps/goblin-assistant/backend"

echo -e "${YELLOW}📋 Step 1: Checking SSH key...${NC}"
if [ ! -f "$SSH_KEY" ]; then
    echo -e "${RED}❌ SSH key not found at $SSH_KEY${NC}"
    exit 1
fi
chmod 600 "$SSH_KEY"
echo -e "${GREEN}✅ SSH key found and secured${NC}"

echo -e "${YELLOW}📋 Step 2: Testing SSH connection...${NC}"
if ! ssh -i "$SSH_KEY" -o ConnectTimeout=10 -o StrictHostKeyChecking=no root@$SERVER_IP "echo 'SSH connection successful'"; then
    echo -e "${RED}❌ Cannot connect to server. Please check:${NC}"
    echo "  - Server IP: $SERVER_IP"
    echo "  - SSH key: $SSH_KEY"
    echo "  - Server status in Kamatera console"
    exit 1
fi
echo -e "${GREEN}✅ SSH connection successful${NC}"

echo -e "${YELLOW}📋 Step 3: Transferring deployment files...${NC}"
cd "$DEPLOY_DIR"
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no \
    local_llm_proxy.py \
    local-llm-proxy.service \
    nginx-local-llm.conf \
    bootstrap_llm.sh \
    ../scripts/setup_resource_isolation.sh \
    ../scripts/configure_systemd_cgroups.sh \
    ../scripts/create_resource_management_service.sh \
    ../scripts/ai-resource-monitor.sh \
    root@$SERVER_IP:/tmp/
echo -e "${GREEN}✅ Files transferred${NC}"

echo -e "${YELLOW}📋 Step 4: Setting up resource isolation...${NC}"
ssh -i "$SSH_KEY" root@$SERVER_IP << 'RESOURCE_SETUP_EOF'
cd ~/llm-deployment

echo "� Setting up resource isolation for AI services..."

# Copy resource isolation scripts
cp ~/llm-deployment/setup_resource_isolation.sh /usr/local/bin/ 2>/dev/null || echo "Resource isolation script not found, skipping..."
cp ~/llm-deployment/configure_systemd_cgroups.sh /usr/local/bin/ 2>/dev/null || echo "Systemd cgroups script not found, skipping..."
cp ~/llm-deployment/create_resource_management_service.sh /usr/local/bin/ 2>/dev/null || echo "Resource management service script not found, skipping..."
cp ~/llm-deployment/ai-resource-monitor.sh /usr/local/bin/ 2>/dev/null || echo "Resource monitor script not found, skipping..."

# Make scripts executable
chmod +x /usr/local/bin/setup_resource_isolation.sh 2>/dev/null || true
chmod +x /usr/local/bin/configure_systemd_cgroups.sh 2>/dev/null || true
chmod +x /usr/local/bin/create_resource_management_service.sh 2>/dev/null || true
chmod +x /usr/local/bin/ai-resource-monitor.sh 2>/dev/null || true

# Run resource isolation setup
if [[ -x /usr/local/bin/setup_resource_isolation.sh ]]; then
    echo "Setting up swap and zram..."
    /usr/local/bin/setup_resource_isolation.sh
else
    echo "Resource isolation script not available, setting up basic swap..."
    # Fallback: basic swap setup
    if [[ ! -f /swapfile ]]; then
        echo "Creating 8GB swapfile..."
        dd if=/dev/zero of=/swapfile bs=1M count=8192 status=progress
        chmod 600 /swapfile
        mkswap /swapfile
        swapon /swapfile
        echo '/swapfile none swap sw 0 0' >> /etc/fstab
    fi
fi

# Configure systemd cgroups
if [[ -x /usr/local/bin/configure_systemd_cgroups.sh ]]; then
    echo "Configuring systemd cgroups..."
    /usr/local/bin/configure_systemd_cgroups.sh
else
    echo "Systemd cgroups script not available, skipping..."
fi

# Create resource management service
if [[ -x /usr/local/bin/create_resource_management_service.sh ]]; then
    echo "Creating resource management service..."
    /usr/local/bin/create_resource_management_service.sh
else
    echo "Resource management service script not available, skipping..."
fi

echo "✅ Resource isolation setup complete!"
RESOURCE_SETUP_EOF

echo -e "${GREEN}✅ Resource isolation setup complete${NC}"

echo -e "${YELLOW}📋 Step 5: Running bootstrap script...${NC}"
ssh -i "$SSH_KEY" root@$SERVER_IP << 'BOOTSTRAP_EOF'
cd ~/llm-deployment

# Create a non-root user for running the bootstrap script
echo "Creating deployment user..."
useradd -m -s /bin/bash deploy || true
usermod -aG sudo deploy
echo 'deploy ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers.d/deploy
mkdir -p /home/deploy/.ssh
cp ~/.ssh/authorized_keys /home/deploy/.ssh/ 2>/dev/null || true
chown -R deploy:deploy /home/deploy/.ssh
chmod 700 /home/deploy/.ssh
chmod 600 /home/deploy/.ssh/authorized_keys 2>/dev/null || true

# Copy deployment files to deploy user's home
echo "Copying deployment files to deploy user..."
mkdir -p /home/deploy/llm-deployment
cp -r ~/llm-deployment/* /home/deploy/llm-deployment/
chown -R deploy:deploy /home/deploy/llm-deployment

# Create model directory
sudo mkdir -p /srv/models/active
sudo chown deploy:deploy /srv/models/active

# Install systemd services as root
echo "Installing systemd services..."
# Install llama.cpp service (if not exists)
if [ ! -f /etc/systemd/system/llamacpp.service ]; then
    sudo tee /etc/systemd/system/llamacpp.service > /dev/null << 'EOF'
[Unit]
Description=llama.cpp server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/llama.cpp
ExecStart=/opt/llama.cpp/build/bin/server --port 8080 --threads 2
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
fi

# Install local LLM proxy service
sudo cp ~/llm-deployment/local-llm-proxy.service /etc/systemd/system/
sudo cp ~/llm-deployment/local_llm_proxy.py /usr/local/bin/
sudo chmod +x /usr/local/bin/local_llm_proxy.py

# Create virtual environment for proxy if needed
if [ ! -d /opt/llm-proxy-venv ]; then
    sudo python3 -m venv /opt/llm-proxy-venv
fi

# Ensure the proxy virtualenv has the dependencies it needs (FastAPI stack)
sudo /opt/llm-proxy-venv/bin/pip install --upgrade pip
sudo /opt/llm-proxy-venv/bin/pip install fastapi "uvicorn[standard]" httpx pydantic

# Update proxy service to use virtual environment
sudo sed -i 's|ExecStart=.*|ExecStart=/opt/llm-proxy-venv/bin/python /usr/local/bin/local_llm_proxy.py|' /etc/systemd/system/local-llm-proxy.service

sudo systemctl daemon-reload

# Configure rclone for Google Drive (interactive setup needed)
echo "Setting up rclone for Google Drive..."
echo "You'll need to configure rclone interactively. Run these commands on the server:"
echo "  sudo -u deploy rclone config"
echo "  - Choose 'gdrive' as storage type"
echo "  - Name it 'gdrive'"
echo "  - Follow the OAuth setup for Google Drive"
echo ""
echo "For now, let's try with existing config or skip model download..."

# Switch to deploy user and run bootstrap
echo "🚀 Running bootstrap script as deploy user..."
sudo -u deploy bash -c "
cd ~/llm-deployment
echo 'Using model remote: gdrive:models/llama_models'
# Try to run bootstrap, but it may fail due to rclone config
./bootstrap_llm.sh gdrive:models/llama_models || echo 'Bootstrap failed - rclone may need configuration'
"
BOOTSTRAP_EOF

echo -e "${GREEN}✅ Bootstrap script executed${NC}"

echo -e "${YELLOW}📋 Step 6: Configure rclone for Google Drive access${NC}"
echo "You need to configure rclone to access your Google Drive where the LLMs are stored."
echo ""
echo "Run this command on the Kamatera server:"
echo "  ssh -i ~/kamatera_key root@$SERVER_IP 'rclone config'"
echo ""
echo "Follow these steps in rclone config:"
echo "  - Choose 'gdrive' as the storage type"
echo "  - Name it 'gdrive'"
echo "  - Leave client_id and client_secret blank for auto-config"
echo "  - Choose the Google account with your LLMs"
echo "  - Accept the permissions"
echo ""
echo "Once configured, the bootstrap script will download your models from:"
echo "  gdrive:models/llama_models"
echo ""
echo "If your models are in a different path, modify the MODEL_REMOTE in the bootstrap call."
echo ""

echo -e "${YELLOW}📋 Step 7: Testing deployment...${NC}"
sleep 10

if ssh -i "$SSH_KEY" root@$SERVER_IP "curl -s http://localhost:8002/health | grep -q 'healthy'"; then
    echo -e "${GREEN}✅ Local LLM proxy is healthy${NC}"
else
    echo -e "${YELLOW}⚠️  Local LLM proxy health check failed - may still be starting${NC}"
fi

if ssh -i "$SSH_KEY" root@$SERVER_IP "curl -s http://localhost:8002/v1/models | grep -q 'models'"; then
    echo -e "${GREEN}✅ Model listing endpoint working${NC}"
else
    echo -e "${YELLOW}⚠️  Model listing failed - services may still be starting${NC}"
fi

echo -e "${GREEN}✅ Deployment completed!${NC}"
echo ""
echo "📋 Next steps:"
echo "1. Configure rclone for Google Drive model storage (see Step 6 above)"
echo "2. Run the bootstrap script again after rclone config:"
echo "   ssh -i ~/kamatera_key root@$SERVER_IP 'cd ~/llm-deployment && ./bootstrap_llm.sh gdrive:models/llama_models'"
echo "3. Test the local LLM proxy:"
echo "   curl http://$SERVER_IP:8002/health"
echo "   curl http://$SERVER_IP:8002/v1/models"
echo ""
echo "4. Update your Goblin Assistant backend config to use:"
echo "   LOCAL_LLM_PROXY_URL=http://$SERVER_IP:8002"
echo "   LOCAL_LLM_API_KEY=your-api-key-here"
echo ""
echo "5. Monitor services:"
echo "   ssh -i ~/kamatera_key root@$SERVER_IP 'systemctl status local-llm-proxy'"
echo "   ssh -i ~/kamatera_key root@$SERVER_IP 'systemctl status ollama'"
echo "   ssh -i ~/kamatera_key root@$SERVER_IP 'systemctl status llamacpp'"
echo ""
echo "6. Monitor resources:"
echo "   ssh -i ~/kamatera_key root@$SERVER_IP 'ai-resource-monitor.sh --display'"
echo "   ssh -i ~/kamatera_key root@$SERVER_IP 'journalctl -u ai-resource-monitor -f'"
echo "   ssh -i ~/kamatera_key root@$SERVER_IP 'journalctl -u ai-resource-manager -f'"

