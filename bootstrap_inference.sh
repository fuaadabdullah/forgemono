#!/usr/bin/env bash
set -euo pipefail
# bootstrap_inference.sh - run as root or with sudo

## CONFIG - edit if needed
MODEL_DISK_DEVICE="/dev/disk/by-id/scsi-0QEMU_QEMU_HARDDISK_drive-scsi1" # second disk
MODEL_MOUNT="/srv/models/active"
LLM_USER="fuaad"
LOCAL_API_PORT=8002
ALLOWED_ROUTER_IP="${ALLOWED_ROUTER_IP:-45.61.51.220}"   # server2 public IP (override with env var)
SWAP_SIZE_GB=12

echo "Starting inference bootstrap..."

# 1) basic packages
apt update 2>/dev/null || apt update --allow-releaseinfo-change 2>/dev/null || true
apt upgrade -y
apt install -y build-essential git curl wget python3 python3-venv python3-pip \
  nginx ufw rclone ca-certificates cmake pkg-config jq

# 2) create user
id -u $LLM_USER &>/dev/null || adduser --disabled-password --gecos "" $LLM_USER
usermod -aG sudo $LLM_USER

# 3) swap (safety net)
if ! swapon --show | grep -q '/swapfile'; then
  fallocate -l ${SWAP_SIZE_GB}G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  echo '/swapfile none swap sw 0 0' | tee -a /etc/fstab
fi

# 1.5) Install Ollama and multiple models for different complexity levels
echo "Installing Ollama for multi-model inference..."
curl -fsSL https://ollama.ai/install.sh | sh
systemctl enable ollama
systemctl start ollama
sleep 5

# Pull models for different complexity levels
echo "Pulling Ollama models..."
ollama pull llama3.2:1b    # Simple tasks (fast, lightweight)
ollama pull llama3.2:3b    # Medium complexity (balanced speed/quality)
ollama pull llama3.1:8b    # Complex tasks (higher quality, slower)
ollama pull phi3:3.8b      # Alternative medium model (good for coding)

# Pull Mistral models for benchmarking and cost optimization
echo "Pulling Mistral models..."
ollama pull mistral:7b     # Mistral-7B-Instruct for medium tasks (cost-effective)
ollama pull mistral        # Mistral-7B base model (alternative medium option)

# Create model aliases for easier management
ollama create goblin-simple -f /dev/stdin <<EOF
FROM llama3.2:1b
PARAMETER temperature 0.7
PARAMETER top_p 0.9
SYSTEM "You are a helpful AI assistant. Keep responses concise and direct."
EOF

ollama create goblin-medium -f /dev/stdin <<EOF
FROM llama3.2:3b
PARAMETER temperature 0.6
PARAMETER top_p 0.85
SYSTEM "You are a knowledgeable AI assistant. Provide detailed but efficient responses."
EOF

ollama create goblin-complex -f /dev/stdin <<EOF
FROM llama3.1:8b
PARAMETER temperature 0.5
PARAMETER top_p 0.8
SYSTEM "You are an expert AI assistant. Provide comprehensive, well-reasoned responses with examples when helpful."
EOF

# Create Mistral model aliases for benchmarking and cost optimization
ollama create goblin-medium-mistral-7b -f /dev/stdin <<EOF
FROM mistral:7b
PARAMETER temperature 0.6
PARAMETER top_p 0.85
SYSTEM "You are a knowledgeable AI assistant. Provide detailed but efficient responses."
EOF

ollama create goblin-medium-mistral-3b -f /dev/stdin <<EOF
FROM mistral
PARAMETER temperature 0.6
PARAMETER top_p 0.85
SYSTEM "You are a knowledgeable AI assistant. Provide detailed but efficient responses."
EOF

# 5) system tuning for LLM workloads
cat > /etc/sysctl.d/99-llm.conf <<'EOF'
vm.swappiness=10
vm.overcommit_memory=1
vm.max_map_count=262144
fs.file-max=200000
EOF
sysctl --system

# 6) install rclone (for model copy)
if ! command -v rclone >/dev/null 2>&1; then
    curl https://rclone.org/install.sh | bash
else
    echo "rclone already installed, skipping installation"
fi
# configure rclone interactively later with: rclone config

# 7) python virtualenv for local-llm-proxy
sudo -u $LLM_USER bash <<'BASH'
cd ~
python3 -m venv llm-proxy-venv
source llm-proxy-venv/bin/activate
pip install --upgrade pip
pip install fastapi uvicorn httpx python-dotenv
deactivate
BASH

# 8) create local-llm-proxy app (FastAPI) - semaphore + api-key check
PROXY_DIR="/home/$LLM_USER/local_llm_proxy"
mkdir -p "$PROXY_DIR"
cat > "$PROXY_DIR/app.py" <<'PY'
from fastapi import FastAPI, Request, HTTPException
import asyncio, os, httpx, json

API_KEY = os.getenv("LOCAL_LLM_API_KEY","changeme")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL","http://127.0.0.1:11434")
SEMAPHORE_CONCURRENCY = int(os.getenv("SEMAPHORE_CONCURRENCY","2"))  # Allow more concurrency for multiple models
SEM = asyncio.Semaphore(SEMAPHORE_CONCURRENCY)

# Model mapping for different complexity levels
MODEL_MAPPING = {
    "simple": "goblin-simple",
    "medium": "goblin-medium-mistral-7b",  # Use Mistral-7B for medium tasks (cost-effective)
    "medium-llama": "goblin-medium",       # Keep llama3.2:3b as alternative for comparison
    "medium-mistral-3b": "goblin-medium-mistral-3b",  # Mistral-3B option
    "complex": "goblin-complex",           # Keep llama3.1:8b for complex (until Mistral Large 3 available)
    "default": "goblin-medium-mistral-7b"  # Default to Mistral-7B
}

app = FastAPI()

def select_model(payload):
    """Select appropriate model based on request parameters or headers"""
    # Check for model override in headers (from router)
    model_hint = payload.get("model_hint", "").lower()
    if model_hint in MODEL_MAPPING:
        return MODEL_MAPPING[model_hint]

    # Check for model in payload (OpenAI format)
    model = payload.get("model", "").lower()
    if "simple" in model:
        return MODEL_MAPPING["simple"]
    elif "complex" in model or "advanced" in model:
        return MODEL_MAPPING["complex"]
    elif "medium" in model or "balanced" in model:
        return MODEL_MAPPING["medium"]

    # Default to medium
    return MODEL_MAPPING["default"]

@app.get("/health")
async def health():
    return {
        "ok": True,
        "backend": OLLAMA_BASE_URL,
        "available_models": list(MODEL_MAPPING.keys()),
        "concurrency": SEMAPHORE_CONCURRENCY
    }

@app.post("/v1/chat/completions")
async def chat_completions(req: Request):
    key = req.headers.get("x-api-key")
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="invalid api key")

    async with SEM:
        try:
            payload = await req.json()

            # Select appropriate model
            selected_model = select_model(payload)
            payload["model"] = selected_model

            print(f"Routing to model: {selected_model}")

            # Convert OpenAI format to Ollama format
            ollama_payload = {
                "model": selected_model,
                "prompt": "",
                "stream": payload.get("stream", False),
                "options": {
                    "temperature": payload.get("temperature", 0.6),
                    "top_p": payload.get("top_p", 0.9),
                    "max_tokens": payload.get("max_tokens", 1024)
                }
            }

            # Extract messages and build prompt
            messages = payload.get("messages", [])
            if messages:
                # Simple prompt construction - can be enhanced
                system_msg = ""
                user_msgs = []
                for msg in messages:
                    if msg.get("role") == "system":
                        system_msg = msg.get("content", "")
                    elif msg.get("role") == "user":
                        user_msgs.append(msg.get("content", ""))

                if system_msg:
                    ollama_payload["system"] = system_msg

                ollama_payload["prompt"] = "\n".join(user_msgs)

            async with httpx.AsyncClient(timeout=300.0) as client:
                resp = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json=ollama_payload)
                resp.raise_for_status()
                ollama_result = resp.json()

                # Convert back to OpenAI format
                return {
                    "id": f"ollama-{selected_model}-{hash(str(payload))}",
                    "object": "chat.completion",
                    "created": 1234567890,
                    "model": selected_model,
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": ollama_result.get("response", "")
                        },
                        "finish_reason": "stop"
                    }],
                    "usage": {
                        "prompt_tokens": len(ollama_payload["prompt"]),
                        "completion_tokens": len(ollama_result.get("response", "")),
                        "total_tokens": len(ollama_payload["prompt"]) + len(ollama_result.get("response", ""))
                    }
                }

        except Exception as e:
            print(f"Error in chat_completions: {e}")
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/completions")  # Legacy endpoint
async def chat_legacy(req: Request):
    # Forward to new endpoint for backward compatibility
    return await chat_completions(req)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
PY
chown -R $LLM_USER:$LLM_USER "$PROXY_DIR"

# 9) systemd service for local-llm-proxy
cat > /etc/systemd/system/local-llm-proxy.service <<EOF
[Unit]
Description=Local LLM Proxy Service
After=network.target

[Service]
Type=simple
User=$LLM_USER
WorkingDirectory=/home/$LLM_USER
Environment=LOCAL_LLM_API_KEY=$(openssl rand -hex 32)
Environment=OLLAMA_BASE_URL=http://127.0.0.1:11434
Environment=SEMAPHORE_CONCURRENCY=2
ExecStart=/home/$LLM_USER/llm-proxy-venv/bin/uvicorn local_llm_proxy.app:app --host 0.0.0.0 --port $LOCAL_API_PORT
Restart=always
RestartSec=5
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable local-llm-proxy

# 10) nginx reverse proxy with IP allow/deny
cat > /etc/nginx/sites-available/local-llm-proxy <<EOF
server {
    listen 8002;
    server_name _;

    # Allow only from router server
    allow $ALLOWED_ROUTER_IP;
    deny all;

    location / {
        proxy_pass http://127.0.0.1:8002;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # Timeout settings for LLM requests
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
EOF
ln -sf /etc/nginx/sites-available/local-llm-proxy /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

# 11) ufw firewall
ufw --force enable
ufw allow ssh
ufw allow 8002
ufw --force reload

# 12) start service
systemctl start local-llm-proxy

# 13) Deploy Promtail for log collection (push to router's Loki)
echo "Setting up Promtail for log collection..."

# Install Promtail
echo "Downloading Promtail..."
apt install -y unzip
PROMTAIL_VERSION="2.9.0"
wget -q https://github.com/grafana/loki/releases/download/v${PROMTAIL_VERSION}/promtail-linux-amd64.zip
unzip promtail-linux-amd64.zip
mv promtail-linux-amd64 /usr/local/bin/promtail
chmod +x /usr/local/bin/promtail
rm promtail-linux-amd64.zip

# Create Promtail systemd service
cat > /etc/systemd/system/promtail.service <<'PROMTAIL_SERVICE_EOF'
[Unit]
Description=Promtail
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/promtail -config.file=/etc/promtail/config.yml
Restart=always

[Install]
WantedBy=multi-user.target
PROMTAIL_SERVICE_EOF

# Create Promtail config directory
mkdir -p /etc/promtail

# Promtail configuration for inference server
cat > /etc/promtail/config.yml <<PROMTAIL_EOF
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://$ALLOWED_ROUTER_IP:3100/loki/api/v1/push

scrape_configs:
  # System logs
  - job_name: systemd-inference
    journal:
      max_age: 12h
      labels:
        job: goblin-inference
        host: inference
    relabel_configs:
      - source_labels: ['__journal__systemd_unit']
        target_label: 'unit'
      - source_labels: ['__journal__hostname']
        target_label: 'hostname'

  # Application logs
  - job_name: app-logs-inference
    static_configs:
      - targets:
          - localhost
        labels:
          job: goblin-inference-app
          host: inference
          __path__: /var/log/local-llm-proxy/*.log
    pipeline_stages:
      - match:
          selector: '{job="goblin-inference-app"}'
          stages:
            - regex:
                expression: '^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (?P<level>\w+) (?P<message>.+)$'
            - labels:
                level: level

  # Ollama logs
  - job_name: ollama-logs
    static_configs:
      - targets:
          - localhost
        labels:
          job: goblin-ollama
          host: inference
          __path__: /var/log/ollama/*.log
    pipeline_stages:
      - match:
          selector: '{job="goblin-ollama"}'
          stages:
            - regex:
                expression: 'time=\"(?P<timestamp>[^\"]+)\" level=(?P<level>\w+) msg=\"(?P<message>[^\"]+)\"'
            - labels:
                level: level

  # Docker container logs (if any)
  - job_name: docker-logs-inference
    static_configs:
      - targets:
          - localhost
        labels:
          job: goblin-docker-inference
          host: inference
          __path__: /var/lib/docker/containers/*/*.log
    pipeline_stages:
      - docker: {}
PROMTAIL_EOF

# Create log directories
mkdir -p /var/log/local-llm-proxy
mkdir -p /var/log/ollama

# Enable and start Promtail
systemctl enable promtail
systemctl start promtail

echo "INFERENCE BOOTSTRAP FINISHED."
echo ""
echo "Multi-model setup complete with the following models:"
echo "  - goblin-simple: llama3.2:1b (fast, lightweight)"
echo "  - goblin-medium: llama3.2:3b (balanced speed/quality)"
echo "  - goblin-complex: llama3.1:8b (higher quality, slower)"
echo ""
echo "Logging Infrastructure:"
echo "  Promtail: Configured to send logs to router's Loki at $ALLOWED_ROUTER_IP:3100"
echo ""
echo "Next steps:"
echo "1. Verify models: ollama list"
echo "2. Test models: curl -X POST http://localhost:11434/api/generate -d '{\"model\":\"goblin-medium\",\"prompt\":\"Hello\"}'"
echo "3. Configure rclone: rclone config (setup Google Drive)"
echo "4. Copy additional models: rclone copy gdrive:models/llama_models $MODEL_MOUNT --progress"
echo "5. The proxy automatically selects models based on 'model_hint' in requests"
