#!/bin/bash
#
# Deploy GoblinOS Assistant to GCP VM with DuckDNS
# This script runs ON the GCP VM
#

set -euo pipefail

# Configuration
DUCKDNS_DOMAIN="goblinosassistant"
DUCKDNS_TOKEN="59be274c-ca62-4e86-b671-035cee6f5bad"
SSL_EMAIL="fuaadabdullah@gmail.com"
BACKEND_PORT=8000
OLLAMA_URL="http://34.60.255.199:11434"
LLAMACPP_URL="http://34.132.226.143:8000"

echo "🚀 GoblinOS Assistant - Backend Deployment"
echo ""
echo "Domain: ${DUCKDNS_DOMAIN}.duckdns.org"
echo "Port:   ${BACKEND_PORT}"
echo ""

# Get external IP
EXTERNAL_IP=$(curl -sf -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip || curl -s https://api.ipify.org)
echo "External IP: ${EXTERNAL_IP}"
echo ""

# Update DuckDNS
echo "📡 Updating DuckDNS..."
RESPONSE=$(curl -sf "https://www.duckdns.org/update?domains=${DUCKDNS_DOMAIN}&token=${DUCKDNS_TOKEN}&ip=${EXTERNAL_IP}")
if [[ "$RESPONSE" == "OK" ]]; then
    echo "✅ DuckDNS updated: ${DUCKDNS_DOMAIN}.duckdns.org → ${EXTERNAL_IP}"
else
    echo "❌ DuckDNS update failed: ${RESPONSE}"
    exit 1
fi

# Setup cron for auto-update
echo "⏰ Setting up DuckDNS auto-update..."
CRON_JOB="*/5 * * * * curl -s \"https://www.duckdns.org/update?domains=${DUCKDNS_DOMAIN}&token=${DUCKDNS_TOKEN}&ip=\" > /dev/null 2>&1"
(sudo crontab -l 2>/dev/null | grep -v "duckdns.org" ; echo "$CRON_JOB") | sudo crontab -
echo "✅ Cron job installed (updates every 5 minutes)"
echo ""

# Wait for DNS propagation
echo "⏳ Waiting for DNS propagation (30 seconds)..."
sleep 30
echo ""

# Configure Nginx
echo "🔧 Configuring Nginx..."
sudo tee /etc/nginx/sites-available/goblin-assistant > /dev/null << 'NGINX_CONFIG'
upstream goblin_backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

# Rate limiting
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_conn_zone $binary_remote_addr zone=conn_limit:10m;

server {
    listen 80;
    server_name goblinosassistant.duckdns.org;
    
    # Temporary response for SSL setup
    location / {
        return 200 'GoblinOS Assistant - Setting up SSL...\n';
        add_header Content-Type text/plain;
    }
}
NGINX_CONFIG

sudo ln -sf /etc/nginx/sites-available/goblin-assistant /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
echo "✅ Nginx configured"
echo ""

# Install SSL certificate
echo "🔒 Installing SSL certificate..."
sudo certbot --nginx \
    --non-interactive \
    --agree-tos \
    --email "${SSL_EMAIL}" \
    --domains "${DUCKDNS_DOMAIN}.duckdns.org" \
    --redirect

if [[ $? -eq 0 ]]; then
    echo "✅ SSL certificate installed"
else
    echo "❌ SSL installation failed"
    exit 1
fi
echo ""

# Update Nginx with full backend proxy
echo "🔧 Updating Nginx with backend proxy..."
sudo tee /etc/nginx/sites-available/goblin-assistant > /dev/null << NGINX_FULL
upstream goblin_backend {
    server 127.0.0.1:${BACKEND_PORT};
    keepalive 32;
}

# Rate limiting
limit_req_zone \$binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_conn_zone \$binary_remote_addr zone=conn_limit:10m;

server {
    listen 80;
    server_name ${DUCKDNS_DOMAIN}.duckdns.org;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name ${DUCKDNS_DOMAIN}.duckdns.org;
    
    ssl_certificate /etc/letsencrypt/live/${DUCKDNS_DOMAIN}.duckdns.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DUCKDNS_DOMAIN}.duckdns.org/privkey.pem;
    
    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # CORS headers
    add_header Access-Control-Allow-Origin "*" always;
    add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
    add_header Access-Control-Allow-Headers "Content-Type, Authorization" always;
    
    # Rate limiting
    limit_req zone=api_limit burst=20 nodelay;
    limit_conn conn_limit 10;
    
    # Proxy to backend
    location / {
        proxy_pass http://goblin_backend;
        proxy_http_version 1.1;
        
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Connection "";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffering
        proxy_buffering off;
        proxy_request_buffering off;
    }
    
    # WebSocket support
    location /ws {
        proxy_pass http://goblin_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_read_timeout 86400;
    }
    
    # Health check
    location /health {
        proxy_pass http://goblin_backend/health;
        access_log off;
    }
}
NGINX_FULL

sudo nginx -t
sudo systemctl reload nginx
echo "✅ Nginx updated with backend proxy"
echo ""

# Clone repository
echo "📦 Cloning repository..."
cd /opt/goblin-assistant
if [[ ! -d "ForgeMonorepo" ]]; then
    sudo -u ubuntu git clone https://github.com/fuaadabdullah/ForgeMonorepo.git
    cd ForgeMonorepo
    sudo -u ubuntu git checkout feat/chat-kamatera-integration
else
    cd ForgeMonorepo
    sudo -u ubuntu git pull origin feat/chat-kamatera-integration
fi
echo "✅ Repository ready"
echo ""

# Setup backend
echo "🐍 Setting up backend..."
cd apps/goblin-assistant/backend

# Create .env file
sudo -u ubuntu tee .env > /dev/null << ENV_FILE
# API Configuration
API_PORT=${BACKEND_PORT}
API_HOST=0.0.0.0

# LLM Endpoints
OLLAMA_URL=${OLLAMA_URL}
LLAMACPP_URL=${LLAMACPP_URL}

# Domain
PUBLIC_DOMAIN=${DUCKDNS_DOMAIN}.duckdns.org
PUBLIC_URL=https://${DUCKDNS_DOMAIN}.duckdns.org

# CORS
ALLOWED_ORIGINS=https://${DUCKDNS_DOMAIN}.duckdns.org,https://goblin-assistant.vercel.app,https://*.vercel.app

# Environment
ENV=production
LOG_LEVEL=info
ENV_FILE

# Install Python dependencies
echo "📦 Installing Python dependencies..."
sudo -u ubuntu python3 -m venv venv
sudo -u ubuntu ./venv/bin/pip install -r requirements.txt || echo "⚠️  Some dependencies may need manual installation"
echo ""

# Create systemd service
echo "⚙️  Creating systemd service..."
sudo tee /etc/systemd/system/goblin-assistant.service > /dev/null << SERVICE_FILE
[Unit]
Description=GoblinOS Assistant Backend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/goblin-assistant/ForgeMonorepo/apps/goblin-assistant/backend
Environment="PATH=/opt/goblin-assistant/ForgeMonorepo/apps/goblin-assistant/backend/venv/bin"
ExecStart=/opt/goblin-assistant/ForgeMonorepo/apps/goblin-assistant/backend/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port ${BACKEND_PORT}
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE_FILE

sudo systemctl daemon-reload
sudo systemctl enable goblin-assistant
sudo systemctl start goblin-assistant
echo "✅ Backend service started"
echo ""

# Setup SSL auto-renewal
echo "🔄 Setting up SSL auto-renewal..."
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
echo "✅ SSL auto-renewal enabled"
echo ""

# Summary
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║   🎉 DEPLOYMENT COMPLETE!                                     ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "✅ DuckDNS:       Configured and auto-updating"
echo "✅ SSL/HTTPS:     Certificate installed and auto-renewing"
echo "✅ Backend:       Running on port ${BACKEND_PORT}"
echo "✅ Nginx:         Reverse proxy configured"
echo ""
echo "🌐 Your Backend API:"
echo "   https://${DUCKDNS_DOMAIN}.duckdns.org"
echo ""
echo "📊 Check Status:"
echo "   sudo systemctl status goblin-assistant"
echo "   sudo systemctl status nginx"
echo "   curl https://${DUCKDNS_DOMAIN}.duckdns.org/health"
echo ""
echo "📋 Logs:"
echo "   sudo journalctl -u goblin-assistant -f"
echo "   sudo tail -f /var/log/nginx/access.log"
echo ""
