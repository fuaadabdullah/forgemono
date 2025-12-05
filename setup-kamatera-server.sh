#!/bin/bash
# Complete Kamatera LLM Server Setup Script
# Run this as root on your new Kamatera server (66.55.77.147)

set -e

echo "🚀 Starting complete LLM server setup..."

# 1. Disk & OS Prep
echo "📁 Setting up disks and swap..."
sudo mkdir -p /srv/ai/models
sudo chown ubuntu:ubuntu /srv/ai/models 2>/dev/null || sudo chown $USER:$USER /srv/ai/models

# Create 6GB swap
echo "🔄 Creating 6GB swap..."
sudo fallocate -l 6G /swapfile 2>/dev/null || sudo dd if=/dev/zero of=/swapfile bs=1M count=6144
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Tune swappiness
sudo sysctl vm.swappiness=10
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf

# Install essentials
echo "📦 Installing system packages..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl git htop build-essential jq ufw fail2ban

# 2. Install Docker & Ollama
echo "🐳 Installing Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh
sudo usermod -aG docker $USER 2>/dev/null || true
sudo usermod -aG docker ubuntu 2>/dev/null || true
sudo systemctl start docker
sudo systemctl enable docker

echo "📦 Installing Docker Compose plugin..."
sudo apt install -y docker-compose-plugin

echo "🤖 Installing Ollama..."
curl -sSf https://ollama.com/install.sh | sh

# Reload groups
newgrp docker 2>/dev/null || true

# 3. Create Docker Compose setup
echo "📝 Creating Docker Compose setup..."
sudo mkdir -p /srv/ai/fastapi

# Docker Compose file
cat > /srv/ai/docker-compose.yml << 'EOF'
version: "3.8"
services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    restart: unless-stopped
    volumes:
      - /srv/ai/models:/var/lib/ollama/models:rw
    ports:
      - "127.0.0.1:11434:11434"
    environment:
      OLLAMA_MODELS_DIR: /var/lib/ollama/models

  llama-cpp:
    image: ghcr.io/ggerganov/llama.cpp:latest
    container_name: llama-cpp
    restart: unless-stopped
    volumes:
      - /srv/ai/models:/models:ro
    command: ["--model","/models/mistral-7b-instruct-v0.1.Q4_0.gguf","--host","0.0.0.0","--port","9000","--threads","2","--mmap","--ctx-size","2048"]
    ports:
      - "127.0.0.1:9000:9000"

  fastapi:
    build: ./fastapi
    container_name: ai-proxy
    restart: unless-stopped
    volumes:
      - ./fastapi:/app
    environment:
      OLLAMA_URL: "http://ollama:11434"
      LLAMA_CPP_URL: "http://llama-cpp:9000"
    ports:
      - "127.0.0.1:8000:8000"
EOF

# FastAPI main.py
cat > /srv/ai/fastapi/main.py << 'EOF'
from fastapi import FastAPI, Request
import httpx
import os

app = FastAPI()
OLLAMA = os.environ.get("OLLAMA_URL","http://ollama:11434")
LLAMA = os.environ.get("LLAMA_CPP_URL","http://llama-cpp:9000")

@app.post("/v1/chat/completions")
async def chat_completions(req: Request):
    body = await req.json()
    model = body.get("model", "mistral:7b")

    if "mistral" in model.lower():
        # Route to Ollama
        ollama_payload = {
            "model": "mistral:7b",
            "prompt": body.get("messages", [{}])[-1].get("content", ""),
            "stream": False
        }
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(f"{OLLAMA}/api/generate", json=ollama_payload)
        return r.json()
    else:
        # Route to llama.cpp
        llama_payload = {
            "prompt": body.get("messages", [{}])[-1].get("content", ""),
            "n_predict": body.get("max_tokens", 100)
        }
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(f"{LLAMA}/completion", json=llama_payload)
        return r.json()

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "ai-proxy"}
EOF

# FastAPI Dockerfile
cat > /srv/ai/fastapi/Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install "fastapi[all]" httpx uvicorn
CMD ["uvicorn","main:app","--host","0.0.0.0","--port","8000","--workers","1"]
EOF

# 4. Pull models
echo "🤖 Pulling Ollama models..."
export PATH=$PATH:/usr/local/bin
ollama pull mistral:7b

# Download GGUF model for llama.cpp
echo "📥 Downloading GGUF model..."
cd /srv/ai/models
wget -O mistral-7b-instruct-v0.1.Q4_0.gguf \
    https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.Q4_0.gguf

# 5. Start services
echo "▶️  Starting Docker services..."
cd /srv/ai
docker compose up -d

# 6. Security setup
echo "🔒 Configuring security..."
sudo ufw --force reset
sudo ufw allow OpenSSH
sudo ufw allow 8000/tcp
sudo ufw --force enable

# 7. Maintenance scripts
echo "🛠️  Setting up maintenance scripts..."

# Disk monitor script
cat > /usr/local/bin/disk_watch.sh << 'EOF'
#!/bin/bash
THRESH=85
USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$USAGE" -ge "$THRESH" ]; then
  docker system prune -af
  find /srv/ai/models -type f -mtime +30 -exec rm -f {} \; 2>/dev/null || true
  echo "$(date): Disk usage at ${USAGE}%, pruned Docker and old models" >> /var/log/disk_monitor.log
fi
EOF

chmod +x /usr/local/bin/disk_watch.sh

# Add to crontab
(crontab -l 2>/dev/null; echo "*/15 * * * * /usr/local/bin/disk_watch.sh") | crontab -
(crontab -l 2>/dev/null; echo "0 3 * * * docker system prune -af") | crontab -

# 8. Test setup
echo "🧪 Testing setup..."
sleep 10

# Check containers
echo "Container status:"
docker ps

# Test health endpoint
echo "Testing health endpoint:"
curl -s http://localhost:8000/health

# Test Ollama
echo "Testing Ollama:"
curl -s http://localhost:11434/api/tags | jq '.models[0].name' 2>/dev/null || echo "Ollama not ready yet"

echo ""
echo "✅ Setup complete!"
echo ""
echo "🌐 Services running:"
echo "  - FastAPI Proxy: http://localhost:8000"
echo "  - Ollama: http://localhost:11434"
echo "  - llama.cpp: http://localhost:9000"
echo ""
echo "🔑 For external access, update your backend OLLAMA_BASE_URL to:"
echo "   http://66.55.77.147:8000"
echo ""
echo "🧪 Test commands:"
echo "  curl http://localhost:8000/health"
echo "  curl -X POST http://localhost:8000/v1/chat/completions \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"model\":\"mistral:7b\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello!\"}]}'"
echo ""
echo "📊 Monitor with: htop, docker stats, df -h"
