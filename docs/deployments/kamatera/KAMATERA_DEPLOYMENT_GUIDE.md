## 🚀 KAMATERA DEPLOYMENT EXECUTION GUIDE

### Step 1: Access Kamatera Console

1. Go to: <https://console.kamatera.com>
2. Login with your credentials
3. Navigate to "My Cloud" → "Servers"
4. You should see two servers:
   - Server 1: 192.175.23.150 (4 CPU, 24GB RAM) - Inference Node
   - Server 2: 45.61.51.220 (2 CPU, 12GB RAM) - Router Node

### Step 2: Deploy Server 1 (Inference Node - 192.175.23.150)

**In Kamatera Console:**

1. Find server with IP: 192.175.23.150
2. Click "Actions" → "Access via Console" (opens new window)
3. In the console, run these commands:

```bash
# Update system first
apt update && apt upgrade -y

# Download bootstrap script
curl -O https://raw.githubusercontent.com/fuaadabdullah/ForgeMonorepo/develop/bootstrap_inference.sh

# Make executable
chmod +x bootstrap_inference.sh

# Run bootstrap (this will take 5-10 minutes)
./bootstrap_inference.sh
```

**Expected output ends with:** "INFERENCE BOOTSTRAP FINISHED."

### Step 3: Deploy Server 2 (Router Node - 45.61.51.220)

**In Kamatera Console:**
1. Find server with IP: 45.61.51.220
2. Click "Actions" → "Access via Console" (opens new window)
3. In the console, run these commands:

```bash

# Update system first
apt update && apt upgrade -y

# Download bootstrap script
curl -O <https://raw.githubusercontent.com/fuaadabdullah/ForgeMonorepo/develop/bootstrap_router.sh>

# Make executable
chmod +x bootstrap_router.sh

# Run bootstrap (this will take 5-10 minutes)
./bootstrap_router.sh
```

**Expected output ends with:** "ROUTER BOOTSTRAP FINISHED."

### Step 4: Configure Inference Server Services (Server 1)

**Back in Server 1 console (192.175.23.150):**

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Install rclone
curl https://rclone.org/install.sh | bash

# Configure rclone for Google Drive (follow interactive prompts)
rclone config
# Name: gdrive
# Type: drive
# Client ID: (leave blank)
# Client Secret: (leave blank)
# Scope: drive
# Root folder ID: (leave blank)
# Service Account: (leave blank)
# Edit advanced config: n
# Use auto config: n
# Get the auth link, paste it in browser, authorize, paste code back

# Pull initial models
ollama pull phi3:3.8b
ollama pull gemma:2b

# Get the inference API key (copy this for Server 2)
grep "LOCAL_LLM_API_KEY" /etc/systemd/system/local-llm-proxy.service
```

### Step 5: Configure Cross-Server Communication (Server 2)

**In Server 2 console (45.61.51.220):**

```bash

# Get the inference API key from Server 1 and update router config

# Edit the systemd service file
nano /etc/systemd/system/goblin-router.service

# In the file, replace:

# REPLACE_WITH_INFERENCE_KEY → [paste the key from Server 1]

# INFERENCE_IP_REPLACE → 192.175.23.150

# Example (replace with actual key):

# Environment="INFERENCE_API_KEY=abc123def456..."

# Environment="INFERENCE_URL=http://192.175.23.150:8002"

# Save and exit (Ctrl+X, Y, Enter)

# Reload systemd and restart router
systemctl daemon-reload
systemctl restart goblin-router

# Get the public API key (for testing)
grep "PUBLIC_API_KEY" /etc/systemd/system/goblin-router.service
```

### Step 6: Verify Infrastructure Setup

**Test Server 1 (192.175.23.150):**

```bash
# Health check
curl http://localhost:8002/health

# Service status
systemctl status local-llm-proxy

# Check logs
journalctl -u local-llm-proxy -n 10 --no-pager
```

**Test Server 2 (45.61.51.220):**
```bash

# Health check
curl <http://localhost:8000/health>

# Service status
systemctl status goblin-router

# Check logs
journalctl -u goblin-router -n 10 --no-pager
```

### Step 7: Deploy Models (Server 1)

**In Server 1 console (192.175.23.150):**

```bash
# Copy models from Google Drive
rclone copy gdrive:models/llama_models /srv/models/active --progress

# List copied models
ls -la /srv/models/active/

# Restart inference service
systemctl restart local-llm-proxy

# Verify models are loaded
curl http://localhost:8002/health
```

### Step 8: Test End-to-End API Functionality

**In Server 2 console (45.61.51.220):**

```bash

# Get the public API key
PUBLIC_KEY=$(grep "PUBLIC_API_KEY" /etc/systemd/system/goblin-router.service | cut -d'=' -f2)

# Test end-to-end API call
curl -H "x-api-key: $PUBLIC_KEY" \
  -H "Content-Type: application/json" \
  -d 
    "model": "phi3:3.8b",
    "messages": [{"role": "user", "content": "Hello, how are you?"}],
    "max_tokens": 100
  
<http://localhost:8000/v1/chat/completions>
```

**Expected response:** JSON with AI-generated response

### Step 9: Run Local Verification

**Back on your local machine:**

```bash
# Run the verification script
./verify_kamatera_deployment.sh
```

## 📋 DEPLOYMENT CHECKLIST

- [ ] Access Kamatera console
- [ ] Deploy bootstrap on Server 1 (192.175.23.150)
- [ ] Deploy bootstrap on Server 2 (45.61.51.220)
- [ ] Configure inference services (Ollama, rclone, models)
- [ ] Setup cross-server communication (API keys)
- [ ] Verify health endpoints
- [ ] Deploy models from Google Drive
- [ ] Test end-to-end API functionality

## 🔧 TROUBLESHOOTING

If bootstrap fails:
```bash

# Check logs
journalctl -n 50 --no-pager

# Re-run bootstrap
./bootstrap_inference.sh 2>&1 | tee bootstrap.log
```

If services don't start:

```bash
# Check service status
systemctl status local-llm-proxy
systemctl status goblin-router

# Check logs
journalctl -u local-llm-proxy -f
journalctl -u goblin-router -f
```

## 📊 INFRASTRUCTURE SUMMARY

- **Inference Node (192.175.23.150)**: 4 CPU, 24GB RAM, Ollama/llama.cpp, model storage
- **Router Node (45.61.51.220)**: 2 CPU, 12GB RAM, FastAPI router, PostgreSQL, Redis
- **Security**: UFW firewall, API key authentication, IP-based access control
- **Cost**: ~$50/month total (Kamatera pricing)
- **Performance**: Semaphore concurrency control, nginx rate limiting
- **Storage**: Google Drive integration via rclone for model deployment
