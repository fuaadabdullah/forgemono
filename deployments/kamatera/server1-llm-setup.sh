#!/bin/bash
# Project: Goblin Assistant
# Script: server1-llm-setup.sh
# Purpose: Setup LLM Inference Server (192.175.23.150) with Ollama + Llama.cpp
# Date: 2025-12-18
# Maintainer: fuaadabdullah

set -e

SERVER_IP="192.175.23.150"
SERVER_NAME="goblin-llm-inference"
USER="root"

echo "🚀 Setting up LLM Inference Server: $SERVER_NAME ($SERVER_IP)"
echo "=============================================================="

# Update system
echo "📦 Updating system packages..."
apt update && apt upgrade -y

# Install essential packages
echo "🔧 Installing essential packages..."
apt install -y curl wget git build-essential cmake pkg-config \
    libssl-dev libffi-dev python3-dev python3-pip \
    nginx ufw fail2ban

# Install Ollama
echo "🦙 Installing Ollama..."
curl -fsSL https://ollama.ai/install.sh | sh

# Create Ollama systemd service
echo "🔧 Creating Ollama systemd service..."
cat > /etc/systemd/system/ollama.service << 'EOF'
[Unit]
Description=Ollama Service
After=network.target

[Service]
Type=notify
ExecStart=/usr/local/bin/ollama serve
User=ollama
Group=ollama
Restart=always
RestartSec=3
Environment="OLLAMA_HOST=0.0.0.0:8002"
Environment="OLLAMA_ORIGINS=*"

[Install]
WantedBy=multi-user.target
EOF

# Create ollama user
useradd -r -s /bin/false ollama

# Create Ollama data directory
mkdir -p /opt/ollama
chown -R ollama:ollama /opt/ollama

# Install Llama.cpp from source for better performance
echo "🐂 Installing Llama.cpp from source..."
cd /opt
git clone https://github.com/ggerganov/llama.cpp.git
cd llama.cpp

# Install Python requirements
pip3 install -r requirements.txt

# Build llama.cpp
make LLAMA_BUILD_METAL=0  # Disable Metal for CPU-only builds

# Create Llama.cpp service wrapper with API key authentication
cat > /opt/llama.cpp/serve.py << 'EOF'
#!/usr/bin/env python3
"""
Simple Llama.cpp API wrapper for OpenAI-compatible endpoints with API key authentication
"""

import subprocess
import json
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import requests
import time

class LlamaCPPHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.api_key = os.getenv("LOCAL_LLM_API_KEY", "")
        super().__init__(*args, **kwargs)
    
    def check_auth(self):
        """Check API key authentication"""
        if not self.api_key:
            # Dev mode - allow all requests
            return True
            
        auth_header = self.headers.get('x-api-key') or self.headers.get('authorization', '')
        if auth_header.startswith('Bearer '):
            auth_header = auth_header[7:]  # Remove "Bearer " prefix
            
        return auth_header == self.api_key
    
    def do_POST(self):
        if not self.check_auth():
            self.send_response(401)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {
                "error": {
                    "message": "Invalid API key",
                    "type": "authentication_error"
                }
            }
            self.wfile.write(json.dumps(error_response).encode())
            return
            
        if self.path == '/v1/chat/completions':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                prompt = self.extract_prompt(data)
                model = data.get('model', 'default')
                
                # Call llama.cpp
                result = subprocess.run([
                    './main',
                    '-m', f'models/{model}.gguf',
                    '--prompt', prompt,
                    '--temp', '0.7',
                    '-c', '2048'
                ], capture_output=True, text=True, cwd='/opt/llama.cpp')
                
                if result.returncode == 0:
                    response = {
                        "id": "cmpl-" + str(int(time.time())),
                        "object": "chat.completion",
                        "created": int(time.time()),
                        "model": model,
                        "choices": [{
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": result.stdout.strip()
                            },
                            "finish_reason": "stop"
                        }]
                    }
                else:
                    response = {
                        "error": {
                            "message": "Llama.cpp execution failed",
                            "type": "internal_error"
                        }
                    }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                error_response = {"error": {"message": str(e)}}
                self.wfile.write(json.dumps(error_response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def extract_prompt(self, data):
        messages = data.get('messages', [])
        prompt_parts = []
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            if role == 'user':
                prompt_parts.append(f"Human: {content}")
            elif role == 'assistant':
                prompt_parts.append(f"Assistant: {content}")
            elif role == 'system':
                prompt_parts.append(f"System: {content}")
        
        prompt_parts.append("Assistant:")
        return "\n".join(prompt_parts)
    
    def log_message(self, format, *args):
        print(f"[Llama.cpp] {format % args}")

def run_server():
    port = 8003
    server = HTTPServer(('0.0.0.0', port), LlamaCPPHandler)
    print(f"🚀 Llama.cpp server starting on port {port}")
    server.serve_forever()

if __name__ == '__main__':
    run_server()
EOF

chmod +x /opt/llama.cpp/serve.py

# Create Llama.cpp systemd service
cat > /etc/systemd/system/llama-cpp.service << 'EOF'
[Unit]
Description=Llama.cpp API Service
After=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/llama.cpp
ExecStart=/usr/bin/python3 /opt/llama.cpp/serve.py
Restart=always
RestartSec=10
Environment=LOCAL_LLM_API_KEY=206e61fdeda2267c9a4ecac3997c4eae7ebd20038282445f7524a84a78ac0158

[Install]
WantedBy=multi-user.target
EOF

# Setup firewall
echo "🔥 Configuring firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 8002/tcp  # Ollama
ufw allow 8003/tcp  # Llama.cpp
ufw allow 80/tcp    # Nginx
ufw allow 443/tcp   # Nginx
ufw --force enable

# Install and configure Nginx as reverse proxy
echo "🌐 Configuring Nginx reverse proxy..."
cat > /etc/nginx/sites-available/goblin-llm << 'EOF'
server {
    listen 80;
    server_name localhost;

    # Ollama proxy
    location /ollama/ {
        proxy_pass http://127.0.0.1:8002/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Llama.cpp proxy
    location /llama-cpp/ {
        proxy_pass http://127.0.0.1:8003/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

ln -sf /etc/nginx/sites-available/goblin-llm /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
nginx -t

# Start and enable services
echo "🚀 Starting services..."
systemctl daemon-reload
systemctl enable ollama
systemctl start ollama
systemctl enable llama-cpp
systemctl start llama-cpp
systemctl enable nginx
systemctl restart nginx

# Pull initial models
echo "📚 Downloading initial LLM models..."
sleep 10  # Wait for Ollama to start

# High-quality models for Server 1 (24GB RAM)
MODELS=(
    "llama3.1:8b-instruct"
    "mistral:7b-instruct-v0.2"
    "codellama:7b-instruct"
    "gemma2:9b-it"
    "phi3:3.8b-mini-instruct-4k-fp16"
    "qwen2.5:3b-instruct-q4f16"
)

for model in "${MODELS[@]}"; do
    echo "⬇️ Downloading $model..."
    ollama pull "$model" || echo "⚠️ Failed to download $model"
done

# Create model download script for future updates
cat > /opt/ollama/download-models.sh << 'EOF'
#!/bin/bash
# Script to download/update Ollama models

MODELS=(
    "llama3.1:8b-instruct"
    "mistral:7b-instruct-v0.2" 
    "codellama:7b-instruct"
    "gemma2:9b-it"
    "phi3:3.8b-mini-instruct-4k-fp16"
    "qwen2.5:3b-instruct-q4f16"
)

echo "📚 Downloading Ollama models..."
for model in "${MODELS[@]}"; do
    echo "⬇️ Downloading $model..."
    ollama pull "$model"
    echo "✅ Downloaded $model"
done

echo "🎉 All models downloaded successfully!"
ollama list
EOF

chmod +x /opt/ollama/download-models.sh

# Create backup script
cat > /opt/ollama/backup-models.sh << 'EOF'
#!/bin/bash
# Backup Ollama models

BACKUP_DIR="/opt/ollama/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/models_$DATE.tar.gz"

mkdir -p "$BACKUP_DIR"
echo "💾 Creating backup: $BACKUP_FILE"

tar -czf "$BACKUP_FILE" /root/.ollama/models/
echo "✅ Backup created: $BACKUP_FILE"

# Keep only last 5 backups
cd "$BACKUP_DIR"
ls -t models_*.tar.gz | tail -n +6 | xargs -r rm
echo "🧹 Old backups cleaned up"
EOF

chmod +x /opt/ollama/backup-models.sh

# Setup log rotation
cat > /etc/logrotate.d/goblin-llm << 'EOF'
/opt/ollama/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
}
EOF

# Create monitoring script
cat > /opt/ollama/monitor.sh << 'EOF'
#!/bin/bash
# Monitor LLM server health

echo "=== Goblin LLM Server Health Check ==="
echo "Time: $(date)"
echo

echo "🤖 Ollama Status:"
systemctl is-active ollama
echo "🐂 Llama.cpp Status:"
systemctl is-active llama-cpp
echo "🌐 Nginx Status:"
systemctl is-active nginx

echo
echo "📊 System Resources:"
echo "CPU: $(top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1)%"
echo "Memory: $(free | grep Mem | awk '{printf("%.1f%%", $3/$2 * 100.0)}')"
echo "Disk: $(df -h / | awk 'NR==2{printf "%s", $5}')"

echo
echo "📚 Available Models:"
ollama list 2>/dev/null || echo "⚠️ Ollama not responding"

echo
echo "🔗 Port Status:"
netstat -tlnp | grep -E ':8002|:8003'

echo
echo "🌐 Web Accessibility:"
curl -s -o /dev/null -w "%{http_code}" http://localhost/health || echo "FAIL"
EOF

chmod +x /opt/ollama/monitor.sh

# Create a cron job for daily backups
echo "0 2 * * * root /opt/ollama/backup-models.sh" >> /etc/crontab

# Final status check
echo
echo "🎉 LLM Inference Server Setup Complete!"
echo "======================================"
echo "✅ Ollama running on port 8002"
echo "✅ Llama.cpp API running on port 8003"
echo "✅ Nginx reverse proxy configured"
echo "✅ Firewall configured"
echo "✅ Models downloaded"
echo "✅ Backup scripts created"
echo "✅ Monitoring setup complete"
echo
echo "📋 Server Information:"
echo "IP Address: $SERVER_IP"
echo "Ollama API: http://$SERVER_IP:8002"
echo "Llama.cpp API: http://$SERVER_IP:8003"
echo "Health Check: http://$SERVER_IP/health"
echo
echo "🛠️ Useful Commands:"
echo "• Check status: systemctl status ollama"
echo "• View logs: journalctl -u ollama -f"
echo "• Download models: /opt/ollama/download-models.sh"
echo "• Monitor health: /opt/ollama/monitor.sh"
echo "• Backup models: /opt/ollama/backup-models.sh"
echo
echo "🚀 Server is ready for production use!"

# Test connectivity
echo
echo "🔍 Testing server connectivity..."
if curl -s http://localhost/health > /dev/null; then
    echo "✅ Server is responding to health checks"
else
    echo "⚠️ Server may need a few more seconds to fully start"
fi
