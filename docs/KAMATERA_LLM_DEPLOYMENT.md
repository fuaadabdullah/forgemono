# Deploying Ollama and Llama.cpp to Kamatera VPS

**Date**: December 1, 2025
**Purpose**: Production deployment guide for local LLM services on Kamatera
**Services**: Ollama, Llama.cpp, Local LLM Proxy

---

## Overview

This guide covers deploying self-hosted LLM services (Ollama and Llama.cpp) to a Kamatera VPS server, providing cost-effective local inference for Goblin Assistant.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Goblin Assistant Backend                  │
│                  (Render/Cloud Deployment)                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ HTTPS (API Key Auth)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│               Kamatera VPS (45.61.60.3)                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  NGINX Reverse Proxy (Port 443)                      │   │
│  │  - SSL/TLS termination                               │   │
│  │  - Rate limiting                                      │   │
│  │  - API key validation proxy                          │   │
│  └────────────────┬─────────────────────────────────────┘   │
│                   │                                          │
│                   ▼                                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Local LLM Proxy (Port 8002)                         │   │
│  │  - FastAPI service                                   │   │
│  │  - API key authentication                            │   │
│  │  - Request routing                                   │   │
│  │  - Model management                                  │   │
│  └─────────┬────────────────────┬───────────────────────┘   │
│            │                    │                            │
│            ▼                    ▼                            │
│  ┌─────────────────┐  ┌────────────────────┐               │
│  │  Ollama         │  │  Llama.cpp Server  │               │
│  │  Port 11434     │  │  Port 8080         │               │
│  │  - Multi-model  │  │  - Single model    │               │
│  │  - Pull models  │  │  - GGUF format     │               │
│  └─────────────────┘  └────────────────────┘               │
│                                                              │
│  Storage: /srv/models/active/                               │
│  - Model files (.gguf format)                               │
│  - Downloaded from Google Drive via rclone                  │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

### 1. Kamatera Server

- **Server IP**: 45.61.60.3 (update as needed)
- **SSH Access**: Root access with SSH key
- **Specs Recommended**:
  - CPU: 4+ cores
  - RAM: 16GB+ (for 7B models)
  - Storage: 50GB+ SSD
  - Network: Unmetered bandwidth

### 2. Local Setup

- **SSH Key**: `~/kamatera_key` with proper permissions (600)
- **Deployment Scripts**: Available in ForgeMonorepo
- **Google Drive**: Models stored in `gdrive:models/llama_models`

### 3. Model Files

Models must be in **GGUF format** for Llama.cpp compatibility:

- Recommended: Q4_K_M quantization (good balance)
- Sizes: 3B-7B models for VPS with 16GB RAM
- Storage: Upload to Google Drive for rclone sync

## Deployment Steps

### Step 1: Prepare SSH Access

```bash
# Verify SSH key exists and has correct permissions
ls -la ~/kamatera_key
chmod 600 ~/kamatera_key

# Test SSH connection
ssh -i ~/kamatera_key root@45.61.60.3 "echo 'Connection successful'"
```

### Step 2: Run Automated Deployment

```bash

# Navigate to ForgeMonorepo root
cd /Users/fuaadabdullah/ForgeMonorepo

# Run deployment script
bash deployments/local/deploy_llm.sh
```

The script will:

1. ✅ Verify SSH connectivity
2. ✅ Transfer deployment files to server
3. ✅ Install system dependencies (curl, wget, nginx, rclone, etc.)
4. ✅ Install Ollama
5. ✅ Create deployment directory structure
6. ✅ Set up systemd services
7. ✅ Configure firewall (UFW)
8. ⚠️ Require manual rclone configuration

### Step 3: Configure rclone for Google Drive

**On the Kamatera server:**

```bash
# SSH into server
ssh -i ~/kamatera_key root@45.61.60.3

# Switch to deploy user
sudo -u deploy -i

# Configure rclone
rclone config

# Follow these steps:
# n) New remote
# name> gdrive
# Storage> drive (Google Drive)
# client_id> (leave blank for default)
# client_secret> (leave blank for default)
# scope> drive (Full access)
# root_folder_id> (leave blank)
# service_account_file> (leave blank)
# Edit advanced config? n
# Use auto config? n (server doesn't have GUI)

# You'll get a URL to authorize in your browser:
# 1. Open the URL in your browser
# 2. Sign in with your Google account
# 3. Allow access
# 4. Copy the authorization code
# 5. Paste it back in the terminal

# Verify configuration
rclone ls gdrive:models/llama_models
```

### Step 4: Download Models and Start Services

```bash

# Still as deploy user on server
cd ~/llm-deployment

# Run bootstrap script with your model path
./bootstrap_llm.sh gdrive:models/llama_models

# This will:

# - Download models from Google Drive

# - Configure llama.cpp with model path

# - Start all services (Ollama, llama.cpp, proxy)

# - Run health checks
```

### Step 5: Verify Deployment

**Check service status:**

```bash
# On Kamatera server
sudo systemctl status ollama
sudo systemctl status llamacpp
sudo systemctl status local-llm-proxy

# Check logs
sudo journalctl -u local-llm-proxy -f
sudo journalctl -u ollama -f
sudo journalctl -u llamacpp -f
```

**Test endpoints:**

```bash

# Health check (no auth required)
curl <http://localhost:8002/health>

# List models (requires API key)
curl -H "x-api-key: your-secure-api-key-here" \
<http://localhost:8002/models>

# Test completion
curl -X POST <http://localhost:8002/chat/completions> \
  -H "x-api-key: your-secure-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "phi3:3.8b",
    "messages": [{"role": "user", "content": "Hello, how are you?"}],
    "max_tokens": 100
  }'
```

### Step 6: Configure Goblin Assistant Backend

Update your backend `.env` file:

```bash
# In /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/backend/.env
LOCAL_LLM_PROXY_URL=http://45.61.60.3:8002
LOCAL_LLM_API_KEY=your-secure-api-key-here
```

## Service Management

### Systemd Services

**Local LLM Proxy** (`/etc/systemd/system/local-llm-proxy.service`):
```ini

[Unit]
Description=Local LLM Proxy Service
After=network.target ollama.service llamacpp.service

[Service]
Type=simple
User=root
WorkingDirectory=/usr/local/bin
ExecStart=/opt/llm-proxy-venv/bin/python /usr/local/bin/local_llm_proxy.py
Restart=always
RestartSec=5
Environment="LOCAL_LLM_API_KEY=your-secure-api-key-here"

[Install]
WantedBy=multi-user.target
```

**Ollama** (`ollama.service` - installed by Ollama installer):

- Manages Ollama service
- Listens on port 11434
- Auto-restarts on failure

**Llama.cpp** (`/etc/systemd/system/llamacpp.service`):

```ini
[Unit]
Description=llama.cpp server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/llama.cpp
ExecStart=/opt/llama.cpp/build/bin/server -m /srv/models/active/model.gguf --port 8080 --threads 2
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Common Commands

```bash

# Start services
sudo systemctl start local-llm-proxy
sudo systemctl start ollama
sudo systemctl start llamacpp

# Stop services
sudo systemctl stop local-llm-proxy
sudo systemctl stop ollama
sudo systemctl stop llamacpp

# Restart services
sudo systemctl restart local-llm-proxy
sudo systemctl restart ollama
sudo systemctl restart llamacpp

# Enable on boot
sudo systemctl enable local-llm-proxy
sudo systemctl enable ollama
sudo systemctl enable llamacpp

# View logs
sudo journalctl -u local-llm-proxy -f
sudo journalctl -u ollama -f
sudo journalctl -u llamacpp -f
```

## Available Models

### Ollama Models

Download models with:

```bash
# SSH into server
ssh -i ~/kamatera_key root@45.61.60.3

# Pull models
ollama pull phi3:3.8b          # 2.3GB - Fast, efficient
ollama pull gemma:2b           # 1.4GB - Very fast
ollama pull qwen2.5:3b         # 1.9GB - Good multilingual
ollama pull deepseek-coder:1.3b # 800MB - Code focused
ollama pull mistral:7b         # 4.1GB - High quality
```

### Llama.cpp Models

Place `.gguf` files in `/srv/models/active/`:
- Download from HuggingFace
- Use Q4_K_M quantization for best balance
- Popular sources:
  - TheBloke's quantized models
  - Official model repos with GGUF releases

Example models:
- `phi-3-mini-4k-instruct-q4.gguf` (2.3GB)
- `llama-2-7b-chat-q4_k_m.gguf` (4GB)
- `mistral-7b-instruct-v0.2-q4_k_m.gguf` (4GB)

## API Endpoints

### Base URL
- **Local**: `http://localhost:8002`
- **External**: `http://45.61.60.3:8002` (configure firewall/nginx)

### Authentication
All endpoints (except `/health`) require:
```
Header: x-api-key: your-secure-api-key-here
```

### Endpoints

#### Health Check
```http

GET /health
```
Response: `{"status": "healthy", "service": "local-llm-proxy"}`

#### List Models

```http
GET /models
Headers: x-api-key: <key>
```
Response:
```json

{
  "models": {
    "ollama": ["phi3:3.8b", "gemma:2b"],
    "llamacpp": ["active-model"]
  }
}
```

#### Chat Completions

```http
POST /chat/completions
Headers:
  x-api-key: <key>
  Content-Type: application/json

Body:
{
  "model": "phi3:3.8b",
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "temperature": 0.7,
  "max_tokens": 100,
  "stream": false
}
```

## Security Considerations

### 1. API Key Security
- **Generate strong key**: Use `openssl rand -hex 32`
- **Store securely**: Environment variable, never commit
- **Rotate regularly**: Update monthly

### 2. Firewall Configuration
```bash

# On Kamatera server
sudo ufw status

# Should see:

# 22/tcp    ALLOW   (SSH)

# 80/tcp    ALLOW   (HTTP)

# 443/tcp   ALLOW   (HTTPS)

# 8002/tcp  DENY    (Proxy - only via nginx)
```

### 3. NGINX Reverse Proxy (Optional)
Set up NGINX with SSL for production:

```nginx
server {
    listen 443 ssl;
    server_name llm.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 300s;
    }
}
```

## Resource Monitoring

### System Resources
```bash

# Memory usage
free -h

# Disk usage
df -h /srv/models/active

# CPU usage
top

# Process details
ps aux | grep -E "(ollama|llama|python.*proxy)"
```

### Expected Resource Usage

**Idle State:**

- Ollama: ~500MB RAM
- Llama.cpp: ~100MB RAM
- Proxy: ~50MB RAM

**Under Load (7B model inference):**

- Model: 4-8GB RAM
- CPU: 50-100% (depends on threads)
- Response time: 1-5 seconds per query

## Troubleshooting

### Services Won't Start

**Check logs:**

```bash
sudo journalctl -u local-llm-proxy -n 50
sudo journalctl -u ollama -n 50
sudo journalctl -u llamacpp -n 50
```

**Common issues:**
1. **Port conflicts**: Check if ports 8002, 8080, 11434 are in use
2. **Model not found**: Verify model path in llamacpp.service
3. **Permission errors**: Ensure /srv/models/active is readable
4. **Out of memory**: Reduce model size or increase RAM

### Connection Issues

**Test from server:**
```bash

curl <http://localhost:8002/health>
curl <http://localhost:11434/api/tags>
curl <http://localhost:8080/health>
```

**Test from external:**

```bash
curl http://45.61.60.3:8002/health
```

If external fails:
1. Check firewall: `sudo ufw status`
2. Check nginx config
3. Verify server is listening: `netstat -tlnp | grep 8002`

### Model Download Fails

**rclone issues:**
```bash

# Test rclone config
rclone ls gdrive:models/llama_models

# Re-authorize if needed
rclone config reconnect gdrive:

# Check bandwidth
rclone bandwidth gdrive:
```

### Performance Issues

**Slow inference:**

1. Check CPU threads: Increase in llamacpp.service `--threads 4`
2. Use smaller model: Q4_K_M instead of Q8_0
3. Reduce context window: `--ctx-size 2048`

**Out of memory:**

1. Use smaller model (3B instead of 7B)
2. Use lighter quantization (Q4_0 instead of Q4_K_M)
3. Close other services
4. Upgrade VPS RAM

## Cost Analysis

### Kamatera VPS Costs (Estimated)

**Type A (4 CPU, 16GB RAM, 50GB SSD)**:

- ~$40-60/month
- Good for 7B models
- Multiple model hosting

**Type B (2 CPU, 8GB RAM, 30GB SSD)**:

- ~$20-30/month
- Good for 3B models
- Single model hosting

### vs Cloud API Costs

**GPT-4 Turbo** ($10/1M input tokens):

- 1000 queries/day = ~$30/month
- Break-even: ~1500 queries/month

**Claude 3 Sonnet** ($3/1M input tokens):

- 1000 queries/day = ~$9/month
- Break-even: ~5000 queries/month

**Local LLM Advantage:**

- Fixed monthly cost
- No per-token charges
- Privacy (data stays on your server)
- Unlimited queries
- No rate limits

## Maintenance

### Weekly Tasks

- [ ] Check service status
- [ ] Review logs for errors
- [ ] Monitor disk usage
- [ ] Check resource usage

### Monthly Tasks

- [ ] Update system packages: `sudo apt update && sudo apt upgrade`
- [ ] Rotate API keys
- [ ] Review security logs
- [ ] Test disaster recovery

### Quarterly Tasks

- [ ] Evaluate model performance
- [ ] Consider model upgrades
- [ ] Review cost efficiency
- [ ] Backup configurations

## Related Files

### Deployment Scripts

- `deployments/local/deploy_llm.sh` - Main deployment script
- `deployments/local/local_deploy.sh` - Alternative local deployment
- `/apps/goblin-assistant/backend/bootstrap_llm.sh` - Server bootstrap

### Service Files

- `/apps/goblin-assistant/backend/local_llm_proxy.py` - FastAPI proxy
- `/apps/goblin-assistant/backend/local-llm-proxy.service` - Systemd unit

### Adapters

- `/apps/goblin-assistant/backend/providers/ollama_adapter.py`
- `/apps/goblin-assistant/backend/providers/llamacpp_adapter.py`

## Next Steps

After successful deployment:

1. **Test from Goblin Assistant**:

   ```python
   # In routing service
   adapter = OllamaAdapter(
       api_key=os.getenv("LOCAL_LLM_API_KEY"),
       base_url="http://45.61.60.3:8002"
   )
   health = await adapter.health_check()
   ```

2. **Set up monitoring**:
   - Datadog/Prometheus for metrics
   - Uptime monitoring
   - Alert on service failures

3. **Optimize performance**:
   - Benchmark response times
   - Tune thread counts
   - Cache frequent queries

4. **Scale if needed**:
   - Add more models
   - Upgrade VPS specs
   - Load balance multiple VPS instances

---

**Status**: Ready for Production Deployment
**Last Updated**: December 1, 2025
**Maintained By**: GoblinOS Team
