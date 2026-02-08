# Goblin Mini DocQA - Single Instance Deployment

This document outlines how to deploy Goblin Mini DocQA to prevent multiple listener instances from binding to the same port, using systemd and Docker with proper resource limits.

## Single Instance Architecture

Goblin Mini DocQA follows a **single listener rule**:

- Only **one instance** of the web server should run at a time
- Large models are loaded once, not duplicated across workers
- For scaling, use separate inference services instead of multiple web server replicas

## Socket-Based Deployment (Recommended)

## Recommendation: Where “prod” should live

I recommend deploying `prod` as a Single VM / Bare Metal instance using systemd + UDS + resource caps when you run local LLM models or need predictable, high-performance inference.

Why:

- Deterministic: single listener avoids duplication of expensive local model loads and prevents memory/cpu contention from multiple server processes.
- Low latency: UDS eliminates extra network hops, which matters for local model inference.
- Resource caps: systemd provides robust platform-level enforcement (MemoryLimit/CPUQuota) for predictable service behavior.
- Simpler telemetry and alerts: single-host monitoring simplifies early production troubleshooting.

Alternative: Docker host using docker-compose is a fine production choice for containerized environments, portability, and easy redeployments — but it adds a layer of complexity for GPU/driver access and may impact model loading strategies. Use docker-compose if your priorities are portability and ease of CI/CD.


For maximum security and to completely eliminate port conflicts, use Unix Domain Sockets (UDS):

### systemd with UDS

The systemd service uses `/run/goblinmini-docqa.sock` instead of TCP ports:

```ini
[Service]
ExecStart=/opt/goblinmini-docqa/venv/bin/uvicorn app.server:app --uds /run/goblinmini-docqa.sock --workers 1
PIDFile=/run/goblinmini-docqa.pid
RuntimeDirectory=goblinmini-docqa
EnvironmentFile=/etc/default/goblin-docqa
ExecStartPre=/bin/bash -c 'exec 200>/run/goblinmini-docqa.lock || exit 1'
ExecStartPre=/bin/bash -c 'flock -n 200 || { echo "Another instance is running"; exit 1; }'
```
#### systemd socket activation & enabling

To start the service with systemd socket activation and ensure it starts on boot:

```bash

sudo systemctl enable --now goblin-docqa.socket
sudo systemctl enable --now goblin-docqa.service
```

This ensures the socket is owned by systemd and the service is started safely on demand or on boot.

#### systemd drop-ins (recommended)
Place custom service options (timeouts/start-limit) into the repo `systemd/dropins/` directory and the `deploy_units.sh` script will copy them into `/etc/systemd/system/<unit>.service.d/` during deployment. We include safe defaults for:

- `TimeoutStartSec` / `TimeoutStopSec`
- `StartLimitIntervalSec` / `StartLimitBurst`


#### Resource caps and runtime directory

The systemd services include safe bounds for memory and CPU usage. You can tune these in `/etc/systemd/system/goblin-docqa.service` and `/etc/systemd/system/goblin-docqa-worker.service`:

- MemoryLimit: limit the usable RAM (e.g., `MemoryLimit=4G`)
- CPUQuota: cap CPU consumption (e.g., `CPUQuota=50%`)
- RuntimeDirectory: directory under `/run` created by systemd

Adjust these values to match server capability (total memory, CPU count, and expected load).


### Nginx Reverse Proxy

Use nginx to proxy HTTP requests to the UDS socket:

```nginx
upstream goblinmini-docqa {
    server unix:/run/goblinmini-docqa.sock;
}

server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://goblinmini-docqa;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeout settings for document processing
        proxy_read_timeout 300s;
    }
}
```

**Benefits of UDS approach:**
- ✅ No port conflicts possible
- ✅ Better security (socket permissions vs network access)
- ✅ Lower latency
- ✅ Automatic cleanup on service stop

## Optional: Enable local inference (recommended for offline or fast LLM inference)

If you want to run local LLMs (recommended for CPU-only inference with llama-cpp), follow these steps.
Keep `DOCQA_ENABLE_LOCAL_MODEL=false` in development to avoid accidental heavy loads.

1) Add env variables to `/etc/default/goblin-docqa`:
```ini

DOCQA_ENABLE_LOCAL_MODEL=true
MODEL_PATH=/opt/goblinmini-docqa/models
MODEL_NAME=Phi-3-mini-4k.gguf
MODEL_QUANTIZATION=auto
```

2) Install `llama-cpp-python` (preferred for CPU):

```bash
sudo apt-get update && sudo apt-get install -y build-essential cmake libssl-dev libsqlite3-dev
sudo -H -u docqa /opt/goblinmini-docqa/venv/bin/python -m pip install --upgrade pip
sudo -H -u docqa /opt/goblinmini-docqa/venv/bin/python -m pip install llama-cpp-python
```

If you prefer PyTorch-based local models (GPU/torch), install it inside the venv with the correct CUDA variant. Some third-party packages may have specific NumPy compatibility constraints; install the correct NumPy/CUDA combination per package documentation if needed:
```bash

# Example (CPU-only torch, check the official install instructions for CUDA if using GPU)
sudo -H -u docqa /opt/goblinmini-docqa/venv/bin/python -m pip install torch torchvision
```

3) Add model files to `MODEL_PATH` (GGUF for llama-cpp or TF/PyTorch weights for torch-based backends):

```bash
sudo mkdir -p /opt/goblinmini-docqa/models
sudo chown -R docqa:docqa /opt/goblinmini-docqa/models
# place your model files (e.g., *.gguf, *.pt) under this directory
```

4) Restart systemd unit(s) or re-run preflight/deploy:
```bash

sudo systemctl restart goblin-docqa.service
sudo systemctl restart goblin-docqa-worker.service

# Check service and inference logs in journal
sudo journalctl -u goblin-docqa.service -f
```

Note: Using CPU-models will affect memory and CPU limits. Tune systemd `MemoryLimit` and `CPUQuota` accordingly. If running GPU-backed PyTorch, configure CUDA and NVIDIA runtimes appropriately.


## App-Level Single Instance Guard

For additional protection against accidental duplicate instances during development or manual runs, use the provided startup script with PID and flock-based locking:

### Usage

```bash
# Make executable (already done)
chmod +x bin/start-docqa.sh

# Run the app with single instance protection
./bin/start-docqa.sh
```

### How It Works

The script (`bin/start-docqa.sh`) implements robust locking:

- **flock-based locking**: Uses `/var/lock/goblinmini-docqa.lock` to prevent multiple instances
- **PID file tracking**: Writes process ID to `/var/run/goblinmini-docqa.pid`
- **Automatic cleanup**: Removes lock and PID files on exit (trap handlers)
- **Non-blocking**: Exits immediately if another instance is running

**Benefits:**
- ✅ Prevents accidental manual duplicates
- ✅ Works in development environments
- ✅ Provides fallback protection beyond systemd
- ✅ Clean shutdown with proper resource cleanup

**Combine with systemd** for maximum protection: systemd prevents service duplicates, the startup script prevents manual run duplicates.

## Monitoring & Observability Setup

### Quick Start

1. **Add prometheus_client to your code** (already done ✅)
2. **Expose /metrics endpoint** (already configured ✅)
3. **Run the monitoring setup script:**

```bash

# Automated setup (includes Prometheus, Grafana, Loki)
sudo ./setup-monitoring.sh

# Or manual Docker setup
cd monitoring && docker-compose up -d
```

4. **Configure alerting rules** (already provided in `prometheus/alerting_rules.yml`)
5. **Set up centralized logging** (systemd journald + Loki)

### Prometheus Metrics

The application exposes comprehensive metrics at `/metrics`:

**Process Metrics:**

- `goblin_docqa_process_memory_bytes{type="rss|vms"}` - Process memory usage
- `goblin_docqa_process_cpu_seconds_total` - Total CPU time used

**Inference Metrics:**

- `goblin_docqa_inference_queue_length` - Current inference queue length
- `goblin_docqa_inference_latency_seconds` - Inference request latency

**Request Metrics:**

- `goblin_docqa_requests_total{method,endpoint,status_code}` - Total HTTP requests
- `goblin_docqa_requests_429_total{method,endpoint}` - HTTP 429 responses

### Prometheus Configuration

Add to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'goblin-docqa'
    static_configs:
      - targets: ['localhost:8000']  # Or your service endpoint
    scrape_interval: 15s
    metrics_path: '/metrics'
```

### Alerting Rules

Key alerts are configured in `prometheus/alerting_rules.yml`:

```yaml

groups:

- name: docqa.rules
  rules:

  - alert: DocQAHighQueue
    expr: docqa_job_queue_length > 0.8 * docqa_job_queue_capacity
    for: 2m
    labels: { severity: warning }
    annotations:
      summary: "Goblin Mini queue >80% capacity"
      description: "Queue length is {{ $value }}. Scale workers or throttle agents."

  - alert: DocQAMemoryHigh
    expr: process_resident_memory_bytes{job="docqa"} > 0.8 * machine_memory_bytes
    for: 1m
    labels: { severity: critical }
    annotations:
      summary: "High memory usage"
      description: "Memory >80% for >1m. Consider evicting nodes or restarting worker."

  - alert: DocQARestarting
    expr: increase(process_start_time_seconds{job="docqa"}[5m]) > 0
    for: 0m
    labels: { severity: warning }
    annotations:
      summary: "Frequent restarts detected"
```

### Service Level Objectives (SLOs)

**Target SLO**: 99% job completion under 5 seconds for "small" tasks

Track these key metrics:

- Job completion rate: `rate(docqa_jobs_completed_total[5m]) / rate(docqa_jobs_started_total[5m])`
- Job completion latency: `histogram_quantile(0.99, rate(docqa_job_duration_seconds_bucket[5m]))`
- Error rate: `rate(docqa_jobs_failed_total[5m]) / rate(docqa_jobs_started_total[5m])`

### Copilot Usage Optimization

**Monitor and optimize GitHub Copilot API token usage:**

```bash
# Analyze current usage patterns
python3 analyze-copilot-usage.py

# Environment variables for optimization
export COPILOT_CACHE_ENABLED=true          # Enable response caching
export COPILOT_TOKEN_BUDGET_DAILY=50000    # Set daily token limit
```

**Optimization Features:**
- ✅ **Response Caching**: 1-hour cache for identical requests (no token cost)
- ✅ **Token Budget**: Daily spending limits with automatic enforcement
- ✅ **Accurate Tracking**: Extracts real token usage from API responses
- ✅ **Usage Analytics**: Historical analysis and optimization recommendations

**Key Metrics to Monitor:**
- `goblin_docqa_copilot_tokens_used_total` - Total tokens consumed
- `goblin_docqa_copilot_requests_total` - API request count
- Cache hit ratio and budget utilization

### Centralized Logging

**systemd/journald** (recommended for Linux):
```bash

# View logs
sudo journalctl -u goblin-docqa.service -f

# Export logs to ELK stack
sudo journalctl -u goblin-docqa.service --since "1 hour ago" --output json | jq -r .MESSAGE
```

**Grafana Loki** setup:

```yaml
# Add to loki config
scrape_configs:
  - job_name: 'systemd-goblin-docqa'
    journal:
      json: false
      max_age: 12h
      labels:
        job: 'systemd-goblin-docqa'
    relabel_configs:
      - source_labels: ['__journal__systemd_unit']
        target_label: 'unit'
        regex: 'goblin-docqa\.service'
```

### Monitoring Dashboard

Minimum Grafana panels for production monitoring:

1. **Queue Length**: `docqa_job_queue_length`
2. **Job Throughput**: `rate(docqa_jobs_completed_total[5m])` (jobs/sec)
3. **Proxy Token Usage**: `rate(docqa_proxy_tokens_used_total[5m])`
4. **Inference Latency**: `histogram_quantile(0.50, docqa_inference_latency_seconds)` and `histogram_quantile(0.95, docqa_inference_latency_seconds)` (p50/p95)
5. **Memory & CPU per Service**: `process_resident_memory_bytes{job="docqa"}` and `rate(process_cpu_user_seconds_total{job="docqa"}[5m])`
6. **429 Rate**: `rate(docqa_requests_429_total[5m])`

**Copilot Savings Tracking**: Compare `proxy_calls_total` vs `local_calls_total` to measure cost savings from local inference:

- Proxy call ratio: `rate(proxy_calls_total[1h]) / (rate(proxy_calls_total[1h]) + rate(local_calls_total[1h]))`
- Local inference savings: `rate(local_calls_total[1h]) / rate(proxy_calls_total[1h])`

### Health Checks

The `/health` endpoint provides operational status including:
- Queue sizes and capacity
- Model loading status
- Rate limit configuration
- Worker status

## Backpressure Tuning

**Keep queue_size conservative** to prevent memory exhaustion and ensure predictable performance:

- Start with small queue sizes (e.g., `MAX_QUEUE_SIZE=10`) and scale up based on monitoring
- Monitor queue depth vs completion times to find optimal balance
- Use the alerting rules to detect when queues are approaching capacity

**Stress Testing for Production Validation:**

If job completion times stay <0.2s and you need real stress testing:

1. **Simulate slow jobs** by adding artificial delays in the worker:
   ```python

   # In worker.py, add temporary delay for testing
   import time
   time.sleep(2)  # Add 2-5s artificial delay
   ```

2. **Validate 429 behavior** under load:
   - Monitor when requests start getting rejected
   - Ensure autoscaling rules trigger appropriately
   - Test queue depth alerts fire correctly

3. **Load testing commands**:

   ```bash
   # Use tools like hey or siege for load testing
   hey -n 1000 -c 10 http://your-domain.com/api/query

   # Monitor metrics during test
   curl http://localhost:9090/api/v1/query?query=docqa_job_queue_length
   ```

## Security & Secrets Management

### Production Secrets Handling

**Never use .env files in production** - move all secrets to secure stores:

**Option 1: HashiCorp Vault**
```bash

# Store secrets in Vault
vault kv put secret/goblinmini-docqa \
  github_token="ghp_..." \
  openai_key="sk-..." \
  anthropic_key="sk-ant-..."

# Configure systemd to read from Vault
EnvironmentFile=/etc/vault.d/goblinmini-docqa.env
```

**Option 2: GitHub Secrets (for CI/CD)**

```yaml
# In GitHub Actions workflow
- name: Deploy
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

**Option 3: OS Secret Store**
```bash

# Linux (systemd credential storage)
sudo systemd-creds encrypt --name=goblinmini-docqa /path/to/secrets.json /etc/credstore/goblinmini-docqa.cred

# macOS Keychain
security add-generic-password -a goblinmini-docqa -s github-token -w "ghp_..."
```

### File System Security

**Make DOCQA_ROOT mount read-only** to prevent file system attacks:

```bash
# In systemd service file
[Service]
# Mount DOCQA_ROOT as read-only
MountFlags=slave
ReadWritePaths=/opt/goblinmini-docqa/data
ReadOnlyPaths=/opt/goblinmini-docqa/models

# Or use bind mounts for read-only access
ExecStartPre=/bin/mount --bind -o ro /opt/goblinmini-docqa/models /opt/goblinmini-docqa/models
```

### Content Sanitization

**Always sanitize file content before sending to proxy services**:

```python

# Example sanitization in your code
def sanitize_content(content: str) -> str:
    """Remove sensitive data before sending to external APIs"""
    # Remove API keys, tokens, secrets
    content = re.sub(r'(?i)(api[_-]?key|token|secret)[\'"]?\s*[:=]\s*[\'"][^\'"]*[\'"]', '[REDACTED]', content)

    # Remove personal information
    content = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN REDACTED]', content)  # SSN
    content = re.sub(r'\b\d{16}\b', '[CARD REDACTED]', content)  # Credit cards

    return content

# Use before sending to proxy
sanitized = sanitize_content(file_content)
proxy_response = await call_proxy_api(sanitized)
```

**Security Checklist:**

- ✅ Secrets stored in secure vaults, not .env files
- ✅ File system mounts are read-only where possible
- ✅ Content sanitization applied before external API calls
- ✅ Rate limiting configured to prevent abuse
- ✅ Input validation on all user-provided data
- ✅ Audit logging enabled for security events

## Deployment Options

### Option 1: systemd (Bare Metal)

#### Installation

1. Create the goblin user:

```bash
sudo useradd -m -s /bin/bash goblin
sudo usermod -aG goblin goblin
```

2. Set up the application directory:
```bash

sudo mkdir -p /opt/goblinmini-docqa
sudo chown goblin:goblin /opt/goblinmini-docqa
sudo chmod 755 /opt/goblinmini-docqa
```

3. Copy application files:

```bash
sudo cp -r /path/to/goblinmini-docqa/* /opt/goblinmini-docqa/
cd /opt/goblinmini-docqa
```

4. Create virtual environment:
```bash

sudo -u goblin python3 -m venv venv
sudo -u goblin venv/bin/pip install -r requirements.txt
```

5. Configure environment:

```bash
sudo -u goblin cp .env.example .env
# Edit .env with your configuration
sudo -u goblin nano .env
```

6. Install systemd services (automatic helper script):
```bash

# Optionally ensure a 'docqa' system user and set ownership of /opt/goblinmini-docqa first
sudo ENSURE_USER=true ENSURE_MODELS_DIR=true ENSURE_PIP_INSTALL=true ./systemd/deploy_units.sh

# Optional: run post-deploy smoke tests automatically after deployment

# Set RUN_POST_DEPLOY_TEST=true to run a lightweight health & analysis smoke test.

# If you also want to test model load (may be slow), set POST_DEPLOY_MODEL_NAME=your_model_name

# Example:

```bash
sudo RUN_POST_DEPLOY_TEST=true POST_DEPLOY_MODEL_NAME=Phi-3-mini-4k.gguf ./systemd/deploy_units.sh
```
### Installing llama-cpp and system dependencies (Ubuntu/Debian)

If you plan to use `llama-cpp-python` (recommended for CPU-only local inference), install these packages:

```bash

sudo apt-get update && sudo apt-get install -y build-essential cmake libssl-dev libsqlite3-dev pkg-config libopenblas-dev
sudo -H -u docqa /opt/goblinmini-docqa/venv/bin/python -m pip install --upgrade pip
sudo -H -u docqa /opt/goblinmini-docqa/venv/bin/python -m pip install llama-cpp-python
```

If you plan to use PyTorch (GPU or CPU), follow the official PyTorch install instructions for your platform and environment. Be careful to pick a `torch` wheel that matches CUDA on the host. For CPU-only PyTorch on recent systems consider explicitly pinning numpy<2 if compatibility requires it:

```bash
sudo -H -u docqa /opt/goblinmini-docqa/venv/bin/python -m pip install "numpy<2" torch torchvision
```

```

7. Create required directories:
```bash

sudo mkdir -p /run/goblinmini-docqa
sudo chown goblin:goblin /run/goblinmini-docqa
```

8. Start services:

```bash
sudo systemctl enable goblinmini-docqa
sudo systemctl enable goblinmini-docqa-worker
sudo systemctl start goblinmini-docqa
sudo systemctl start goblinmini-docqa-worker
```

#### systemd Service Features

- **PIDFile locking**: Prevents multiple instances
- **File locking**: Uses flock to ensure single instance
- **Resource limits**: MemoryLimit=4G, CPUQuota=200%
- **Security hardening**: NoNewPrivileges, PrivateTmp, ProtectSystem
- **Automatic restart**: on-failure with 5s delay

#### Management Commands

```bash

# Check status
sudo systemctl status goblinmini-docqa
sudo systemctl status goblinmini-docqa-worker

# View logs
sudo journalctl -u goblinmini-docqa -f
sudo journalctl -u goblinmini-docqa-worker -f

# Restart services
sudo systemctl restart goblinmini-docqa
sudo systemctl restart goblinmini-docqa-worker

# Stop services
sudo systemctl stop goblinmini-docqa
sudo systemctl stop goblinmini-docqa-worker
```

#### Cleanup & Accident Recovery

If something goes sideways:

**For systemd socket activation:**

```bash
sudo systemctl stop goblin-docqa.service
sudo systemctl stop goblin-docqa.socket
sudo rm -f /run/goblinmini-docqa.sock
sudo systemctl start goblin-docqa.socket
sudo systemctl start goblin-docqa.service
```

**For regular systemd services:**
```bash

sudo systemctl stop goblinmini-docqa
sudo systemctl stop goblinmini-docqa-worker
sudo rm -f /run/goblinmini-docqa.lock
sudo systemctl start goblinmini-docqa
sudo systemctl start goblinmini-docqa-worker
```

### Option 1.5: systemd Socket Activation (Recommended)

**systemd socket activation** is the cleanest deployment method. systemd holds the socket and hands it to your service atomically, preventing race conditions and ensuring only one instance can bind.

#### Socket Unit (`/etc/systemd/system/goblin-docqa.socket`)

```ini
[Unit]
Description=Goblin DocQA socket

[Socket]
ListenStream=/run/goblinmini-docqa.sock
SocketMode=0660
RemoveOnStop=true

[Install]
WantedBy=sockets.target
```

#### Service Unit (`/etc/systemd/system/goblin-docqa.service`)

```ini

[Unit]
Description=Goblin DocQA service
After=network.target

[Service]
User=docqa
Group=docqa
WorkingDirectory=/opt/goblinmini-docqa
EnvironmentFile=/etc/default/goblin-docqa
Environment=DOCQA_ROOT=/mnt/allowed
ExecStart=/opt/goblinmini-docqa/venv/bin/uvicorn app.server:app --uds /run/goblinmini-docqa.sock --workers 1 --log-level info
Restart=on-failure
RestartSec=5
LimitNOFILE=32768
ProtectSystem=full

[Install]
WantedBy=multi-user.target
```

#### Worker Service (`/etc/systemd/system/goblin-docqa-worker.service`)

```ini
[Unit]
Description=Goblin DocQA RQ Worker
After=network.target redis.service
Requires=redis.service
PartOf=goblin-docqa.service

[Service]
User=docqa
Group=docqa
WorkingDirectory=/opt/goblin-docqa
Environment=DOCQA_TOKEN=supersecret
Environment=DOCQA_ROOT=/mnt/allowed
ExecStart=/usr/bin/python3 worker.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

#### Automated Deployment

Use the provided deployment script:

```bash

# Run as root from project directory
sudo ./deploy-systemd-socket.sh
```

The script will:

- Create `docqa` user and group
- Set up `/opt/goblin-docqa` directory
- Copy application files
- Install systemd units
- Enable socket activation

#### Manual Installation

```bash
# 1. Create user and directories
sudo useradd --system --shell /bin/bash --home-dir /opt/goblin-docqa --create-home docqa
sudo mkdir -p /opt/goblin-docqa /mnt/allowed
sudo chown -R docqa:docqa /opt/goblin-docqa /mnt/allowed

# 2. Copy files
sudo cp -r /path/to/project/* /opt/goblin-docqa/
sudo cp systemd/goblin-docqa.* /etc/systemd/system/

# 3. Install dependencies
cd /opt/goblin-docqa
sudo -u docqa pip3 install -r requirements.txt

# 4. Configure environment
sudo -u docqa cp .env.example .env
# Edit .env with your settings

# 5. Enable and start
sudo systemctl daemon-reload
sudo systemctl enable --now goblin-docqa.socket
sudo systemctl start goblin-docqa.service
sudo systemctl enable --now goblin-docqa-worker.service
```

#### Why Socket Activation Works

- **Atomic handoff**: systemd owns the socket; only one service gets it
- **No race conditions**: Service starts only when socket receives connections
- **Clean restarts**: Socket persists across service restarts
- **Resource efficiency**: Service starts on-demand
- **Security**: Socket permissions instead of network exposure

#### Testing Socket Activation

```bash

# Check socket is listening
sudo ss -l | grep goblinmini-docqa.sock

# View service status
sudo systemctl status goblin-docqa.service

# Check logs
sudo journalctl -u goblin-docqa.service -f

# Test connection
curl -s -H "Authorization: Bearer YOUR_TOKEN" --unix-socket /run/goblinmini-docqa.sock <http://localhost/health>
```

### Option 2: Docker Compose

#### Quick Start

1. Set environment variables:

```bash
export DOCQA_TOKEN="your-secure-token-here"
export COPILOT_API_URL="https://api.github.com/copilot"
export COPILOT_API_KEY="your-copilot-key"
```

2. Start services:
```bash

cd docker
docker compose up -d
```

#### Docker Resource Limits

**Main Application (docqa)**:

- CPU: 2 cores maximum, 0.5 reserved
- Memory: 4GB maximum, 1GB reserved
- Replicas: 1 (single instance)

**Worker Process (worker)**:

- CPU: 1 core maximum, 0.2 reserved
- Memory: 2GB maximum, 512MB reserved
- Replicas: 1 (single instance)

**Redis**:

- CPU: 0.5 cores maximum, 0.1 reserved
- Memory: 512MB maximum, 128MB reserved

#### Docker Commands

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f docqa
docker compose logs -f worker

# Check resource usage
docker stats

# Scale (NOT RECOMMENDED - violates single instance rule)
# docker compose up -d --scale docqa=1  # Keep at 1

# Stop services
docker compose down
```

## Resource Management

### Preventing Runaway Inference

Both deployment methods include resource caps to prevent:
- Memory exhaustion from large document processing
- CPU starvation of host system
- Resource conflicts between main app and workers

### Monitoring Resources

**Docker**:
```bash

docker stats
docker compose exec docqa ps aux
```

**systemd**:

```bash
sudo systemctl status goblinmini-docqa
sudo journalctl -u goblinmini-docqa | grep -i memory
```

## Security Considerations

### systemd Security Features
- Non-root user execution
- Private /tmp directory
- Read-only root filesystem (except allowed paths)
- Limited file descriptor count
- No new privileges after startup

### Docker Security Features
- Read-only root filesystem
- Non-root user execution
- Minimal base image (python:3.11-slim)
- Resource limits and reservations
- Temporary filesystem for /tmp

## Troubleshooting

### Multiple Instances Detected

**systemd**:
```bash

# Check for existing processes
ps aux | grep uvicorn
sudo lsof -i :8000

# Remove stale PID files
sudo rm -f /run/goblinmini-docqa.pid
sudo systemctl restart goblinmini-docqa
```

**Docker**:

```bash
# Check for multiple containers
docker ps | grep docqa

# Remove duplicate containers
docker compose down
docker compose up -d
```

### Resource Limit Issues

**Increase limits if needed**:
```yaml

# docker-compose.yml
deploy:
  resources:
    limits:
      cpus: "4.0"    # Increase CPU limit
      memory: 8G     # Increase memory limit
```

**systemd**:

```ini
# /etc/systemd/system/goblin-docqa.service
MemoryLimit=8G
CPUQuota=400%
```

### Port Conflicts

**Check port usage**:
```bash

sudo lsof -i :8000
sudo netstat -tlnp | grep :8000
```

**Change port**:

```bash
# .env
DOCQA_PORT=8001

# docker-compose.yml
ports:
  - "8001:8000"
```

## Production Checklist

- [ ] Single instance confirmed (no multiple replicas)
- [ ] Resource limits set appropriately for workload
- [ ] Environment variables configured securely
- [ ] Logging configured for monitoring
- [ ] Health checks implemented
- [ ] Backup strategy for Redis data
- [ ] SSL/TLS termination configured (nginx, cloudflare, etc.)

## Release / Canary Deployment Checklist

**⚠️ DO NOT SKIP - Critical for production stability**

### Pre-Release Preparation

- [ ] **Build production image**:
  ```bash

  # Build and tag with date
  export TAG=prod-$(date +%Y%m%d)
  docker build -t goblin/docqa:$TAG -t goblin/docqa:latest .

  # Push to registry
  docker push goblin/docqa:$TAG
  docker push goblin/docqa:latest
  ```

- [ ] **Verify image integrity**:

  ```bash
  # Check image size and layers
  docker inspect goblin/docqa:$TAG | jq '.Size'
  docker history goblin/docqa:$TAG

  # Security scan (optional)
  docker scan goblin/docqa:$TAG
  ```

- [ ] **Update deployment manifests** with new image tag
- [ ] **Backup current production state** (Redis data, configs)

### Canary Deployment (1 Replica)

- [ ] **Deploy single canary instance**:
  ```bash

  # Kubernetes example
  kubectl set image deployment/goblinmini-docqa goblinmini-docqa=goblin/docqa:$TAG
  kubectl scale deployment goblinmini-docqa --replicas=1

  # Or Docker Compose
  export TAG=prod-$(date +%Y%m%d)
  docker-compose up -d --scale goblinmini-docqa=1
  ```

- [ ] **Wait for canary to be ready** (2-3 minutes for model loading)

### Smoke Tests (Must Pass All)

- [ ] **Health endpoint test**:

  ```bash
  curl -f https://api.goblinmini-docqa.com/health
  # Should return 200 with JSON: {"status": "healthy", "queue_depth": 0, ...}
  ```

- [ ] **Metrics endpoint test**:
  ```bash

  curl -f <https://api.goblinmini-docqa.com/metrics> | grep -E "(docqa_|process_|redis_)"
  # Should return Prometheus metrics with non-zero values
  ```

- [ ] **Submit 10 sample jobs**:

  ```bash
  # Test script for submitting sample jobs
  for i in {1..10}; do
    curl -X POST https://api.goblinmini-docqa.com/api/query \
      -H "Content-Type: application/json" \
      -d "{\"query\": \"What is AI?\", \"context\": \"Sample context $i\"}" \
      -w "Job $i: %{http_code}\n" &
  done
  wait
  # All should return 200 or 202 (accepted)
  ```

- [ ] **Verify job processing**:
  ```bash

  # Check queue metrics
  curl <https://api.goblinmini-docqa.com/metrics> | grep docqa_job_queue_length
  # Should show queue processing (length decreasing)

  # Check for completed jobs in logs
  kubectl logs deployment/goblinmini-docqa | grep -i "job.*completed\|processed"
  ```

### Monitoring Phase (5-10 minutes)

- [ ] **Monitor queue depth**:

  ```bash
  # Watch queue metrics
  watch -n 10 'curl -s https://api.goblinmini-docqa.com/metrics | grep docqa_job_queue_length'
  # Should stay low (< 5) and not grow indefinitely
  ```

- [ ] **Monitor memory usage**:
  ```bash

  # Watch memory metrics
  watch -n 10 'curl -s <https://api.goblinmini-docqa.com/metrics> | grep -E "process_resident_memory_bytes|docqa_.*_memory"'
  # Should stay within limits, no memory leaks
  ```

- [ ] **Monitor error rates**:

  ```bash
  # Check for 5xx errors
  curl -s https://api.goblinmini-docqa.com/metrics | grep -E "docqa_requests_total.*[5-9][0-9][0-9]"
  # Should be zero or very low
  ```

- [ ] **Check logs for anomalies**:
  ```bash

  # Recent error logs
  kubectl logs --tail=50 deployment/goblinmini-docqa | grep -i error

  # Model loading status
  kubectl logs deployment/goblinmini-docqa | grep -i "model.*loaded\|inference.*ready"
  ```

### Decision Point

- [ ] **Canary health assessment**:
  - ✅ All smoke tests passed
  - ✅ Queue processing normally
  - ✅ Memory stable, no leaks
  - ✅ No critical errors in logs
  - ✅ Response times acceptable (< 30s for sample jobs)

### Full Rollout (If Canary Passes)

- [ ] **Scale to full production replicas**:

  ```bash
  # Kubernetes
  kubectl scale deployment goblinmini-docqa --replicas=3

  # Docker Compose
  docker-compose up -d --scale goblinmini-docqa=3

  # ECS
  aws ecs update-service --cluster prod --service goblinmini-docqa --desired-count 3
  ```

- [ ] **Verify full rollout**:
  ```bash

  # Wait for all replicas to be ready
  kubectl wait --for=condition=available --timeout=300s deployment/goblinmini-docqa

  # Check pod status
  kubectl get pods -l app=goblinmini-docqa
  # All should show 1/1 Running
  ```

### Post-Mortem Stress Testing

- [ ] **Spike workload test**:

  ```bash
  # Submit burst of requests to test rate limiting
  for i in {1..50}; do
    curl -X POST https://api.goblinmini-docqa.com/api/query \
      -H "Content-Type: application/json" \
      -d "{\"query\": \"Test query $i\", \"context\": \"Test context\"}" \
      --max-time 5 &
  done
  wait
  ```

- [ ] **Verify 429 behavior**:
  ```bash

  # Check metrics for 429 responses
  curl <https://api.goblinmini-docqa.com/metrics> | grep docqa_requests_429_total
  # Should show some 429s during spike

  # Check queue depth during spike
  curl <https://api.goblinmini-docqa.com/metrics> | grep docqa_job_queue_length
  # Should show queue filling up
  ```

- [ ] **Test retry logic** (if implemented):

  ```bash
  # Submit request that should trigger retry
  curl -X POST https://api.goblinmini-docqa.com/api/query \
    -H "Content-Type: application/json" \
    -H "X-Retry-Count: 0" \
    -d "{\"query\": \"Retry test\", \"context\": \"Test\"}"

  # Check logs for retry attempts
  kubectl logs deployment/goblinmini-docqa | grep -i retry
  ```

### Rollback Plan (If Issues Detected)

- [ ] **Immediate rollback commands**:
  ```bash

  # Rollback to previous image
  kubectl rollout undo deployment/goblinmini-docqa

  # Or scale down problematic deployment
  kubectl scale deployment goblinmini-docqa --replicas=0
  kubectl scale deployment goblinmini-docqa-old --replicas=3
  ```

- [ ] **Post-rollback verification**:
  - [ ] Health checks pass
  - [ ] Traffic serving normally
  - [ ] Incident documented

### Success Criteria

- [ ] **Zero downtime** during rollout
- [ ] **All smoke tests pass** on canary
- [ ] **Queue processing** within expected bounds
- [ ] **Memory usage** stable during monitoring period
- [ ] **429 rate limiting** working correctly
- [ ] **Full rollout** completes successfully
- [ ] **Spike testing** validates system resilience

## CI/CD Pipeline

### GitHub Actions Deployment Workflow

Create `.github/workflows/deploy.yml` for automated container deployment:

```yaml
name: Deploy Goblin Mini DocQA

on:
  push:
    branches: [main]
    paths:
      - 'goblinmini-docqa/**'
      - '.github/workflows/deploy.yml'

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}/goblinmini-docqa

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
    - name: Checkout repository
      uses: actions/checkout@v4

    - name: Log in to Container Registry
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=sha,prefix={{branch}}-
          type=raw,value=latest,enable={{is_default_branch}}

    - name: Build and push Docker image
      uses: docker/build-push-action@v5
      with:
        context: ./goblinmini-docqa
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

  canary-deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    environment: production

    steps:
    - name: Checkout repository
      uses: actions/checkout@v4

    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v4
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-east-1

    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v2

    - name: Deploy to ECS (Canary - 1 replica)
      run: |
        # Update ECS service to 1 replica with new image
        aws ecs update-service \
          --cluster goblinmini-docqa-prod \
          --service goblinmini-docqa-service \
          --task-definition goblinmini-docqa-task \
          --desired-count 1 \
          --force-new-deployment

    - name: Wait for deployment
      run: |
        aws ecs wait services-stable \
          --cluster goblinmini-docqa-prod \
          --services goblinmini-docqa-service

    - name: Smoke Test Canary Deployment
      run: |
        # Wait for service to be healthy
        sleep 30

        # Test health endpoint
        HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://api.goblinmini-docqa.com/health)
        if [ "$HEALTH_STATUS" -ne 200 ]; then
          echo "Health check failed: $HEALTH_STATUS"
          exit 1
        fi

        # Test metrics endpoint
        METRICS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://api.goblinmini-docqa.com/metrics)
        if [ "$METRICS_STATUS" -ne 200 ]; then
          echo "Metrics check failed: $METRICS_STATUS"
          exit 1
        fi

        # Test basic API functionality
        API_STATUS=$(curl -s -X POST \
          -H "Content-Type: application/json" \
          -d '{"query": "test", "context": "test context"}' \
          -o /dev/null -w "%{http_code}" \
          https://api.goblinmini-docqa.com/api/query)

        if [ "$API_STATUS" -ne 200 ] && [ "$API_STATUS" -ne 429 ]; then
          echo "API test failed: $API_STATUS"
          exit 1
        fi

        echo "✅ Canary deployment smoke tests passed"

  promote-full-rollout:
    needs: canary-deploy
    runs-on: ubuntu-latest
    environment: production

    steps:
    - name: Checkout repository
      uses: actions/checkout@v4

    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v4
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-east-1

    - name: Promote to Full Rollout (3 replicas)
      run: |
        aws ecs update-service \
          --cluster goblinmini-docqa-prod \
          --service goblinmini-docqa-service \
          --task-definition goblinmini-docqa-task \
          --desired-count 3 \
          --force-new-deployment

    - name: Wait for full rollout
      run: |
        aws ecs wait services-stable \
          --cluster goblinmini-docqa-prod \
          --services goblinmini-docqa-service

    - name: Verify full rollout
      run: |
        # Check that all 3 replicas are running
        RUNNING_COUNT=$(aws ecs describe-services \
          --cluster goblinmini-docqa-prod \
          --services goblinmini-docqa-service \
          --query 'services[0].runningCount' \
          --output text)

        if [ "$RUNNING_COUNT" -ne 3 ]; then
          echo "Full rollout failed: expected 3 running tasks, got $RUNNING_COUNT"
          exit 1
        fi

        echo "✅ Full rollout completed successfully"

  rollback:
    needs: [canary-deploy, promote-full-rollout]
    runs-on: ubuntu-latest
    if: failure()

    steps:
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v4
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-east-1

    - name: Rollback to previous version
      run: |
        # Rollback ECS service to previous task definition
        aws ecs update-service \
          --cluster goblinmini-docqa-prod \
          --service goblinmini-docqa-service \
          --task-definition goblinmini-docqa-task \
          --desired-count 3 \
          --force-new-deployment \
          --deployment-configuration "maximumPercent=200,minimumHealthyPercent=50"
```

### Docker Compose for Local Testing

For local development and testing of the deployment pipeline:

```yaml

# docker-compose.deploy.yml
version: '3.8'

services:
  goblinmini-docqa:
    build:
      context: .
      dockerfile: Dockerfile
    image: goblinmini-docqa:${TAG:-latest}
    ports:

      - "8000:8000"
    environment:

      - DOCQA_ENV=production
      - REDIS_URL=redis://redis:6379
    depends_on:

      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "<http://localhost:8000/health"]>
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      replicas: 1  # Start with 1 for canary testing

  redis:
    image: redis:7-alpine
    ports:

      - "6379:6379"
    volumes:

      - redis_data:/data
    command: redis-server --appendonly yes

volumes:
  redis_data:
```

## Disaster Recovery & Backup Strategy

### Redis Persistence & Backups

**Configure Redis persistence** for job/result store durability:

```bash
# redis.conf for production
# RDB snapshots (point-in-time backups)
save 900 1          # Save after 900 sec (15 min) if at least 1 key changed
save 300 10         # Save after 300 sec (5 min) if at least 10 keys changed
save 60 10000       # Save after 60 sec (1 min) if at least 10000 keys changed

# AOF (Append Only File) for better durability
appendonly yes
appendfsync everysec  # fsync every second

# Memory management
maxmemory 1gb
maxmemory-policy allkeys-lru
```

**Automated Redis backups**:

```bash

#!/bin/bash

# backup-redis.sh
BACKUP_DIR="/opt/backups/redis"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REDIS_HOST="localhost"
REDIS_PORT="6379"

# Create backup directory
mkdir -p $BACKUP_DIR

# RDB snapshot backup
redis-cli -h $REDIS_HOST -p $REDIS_PORT --rdb $BACKUP_DIR/redis_$TIMESTAMP.rdb

# AOF backup (if using AOF)
cp /var/lib/redis/appendonly.aof $BACKUP_DIR/redis_aof_$TIMESTAMP.aof

# Compress backups
gzip $BACKUP_DIR/redis_$TIMESTAMP.rdb
gzip $BACKUP_DIR/redis_aof_$TIMESTAMP.aof

# Rotate old backups (keep last 7 days)
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete

echo "Redis backup completed: $TIMESTAMP"
```

**Schedule automated backups**:

```bash
# Add to crontab for daily backups at 2 AM
0 2 * * * /opt/goblinmini-docqa/backup-redis.sh

# Or use systemd timer
# /etc/systemd/system/redis-backup.timer
[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target

# /etc/systemd/system/redis-backup.service
[Service]
ExecStart=/opt/goblinmini-docqa/backup-redis.sh
```

### Model Artifact Snapshots

**Snapshot model artifacts** with checksums for reproducibility:

```bash

#!/bin/bash

# snapshot-models.sh
MODEL_DIR="/opt/goblinmini-docqa/models"
SNAPSHOT_DIR="/opt/backups/models"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create snapshot directory
SNAPSHOT_PATH="$SNAPSHOT_DIR/snapshot_$TIMESTAMP"
mkdir -p $SNAPSHOT_PATH

# Copy model files
cp -r $MODEL_DIR/* $SNAPSHOT_PATH/

# Generate checksums for all model files
find $SNAPSHOT_PATH -type f -exec sha256sum {} \; > $SNAPSHOT_PATH/checksums.sha256

# Create metadata file
cat > $SNAPSHOT_PATH/metadata.json << EOF
{
  "timestamp": "$TIMESTAMP",
  "source_dir": "$MODEL_DIR",
  "files": $(find $SNAPSHOT_PATH -type f -name "*.gguf" -o -name "*.pt" -o -name "*.bin" | wc -l),
  "total_size": $(du -sb $SNAPSHOT_PATH | cut -f1),
  "git_commit": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
  "checksum_file": "checksums.sha256"
}
EOF

# Compress snapshot
tar -czf ${SNAPSHOT_PATH}.tar.gz -C $SNAPSHOT_DIR snapshot_$TIMESTAMP
rm -rf $SNAPSHOT_PATH

# Rotate old snapshots (keep last 5)
ls -t $SNAPSHOT_DIR/*.tar.gz | tail -n +6 | xargs rm -f

echo "Model snapshot completed: $TIMESTAMP"
```

**Verify model integrity**:

```bash
#!/bin/bash
# verify-models.sh
SNAPSHOT_FILE="$1"
EXTRACT_DIR="/tmp/model_verify"

# Extract snapshot
mkdir -p $EXTRACT_DIR
tar -xzf $SNAPSHOT_FILE -C $EXTRACT_DIR

# Verify checksums
cd $EXTRACT_DIR
if sha256sum -c checksums.sha256; then
    echo "✅ Model snapshot integrity verified"
    exit 0
else
    echo "❌ Model snapshot integrity check failed"
    exit 1
fi
```

**Automated model snapshots**:

```bash

# Weekly model snapshots (Sundays at 3 AM)
0 3 * * 0 /opt/goblinmini-docqa/snapshot-models.sh

# After model updates (manual trigger)

# /opt/goblinmini-docqa/snapshot-models.sh
```

### Backup Storage Strategy

**Multi-tier backup storage**:

```bash
# Local backups (fast recovery)
# /opt/backups/ - Daily Redis, Weekly models

# Remote backups (disaster recovery)
# AWS S3 or similar
aws s3 sync /opt/backups/ s3://goblinmini-docqa-backups/

# Offsite backups (compliance)
# Azure Blob Storage or tape backups
az storage blob upload-batch \
  --destination backups \
  --source /opt/backups/ \
  --account-name goblinmini \
  --account-key $AZURE_STORAGE_KEY
```

**Backup retention policy**:

- **Daily Redis backups**: 7 days local, 30 days remote
- **Model snapshots**: 5 versions local, unlimited remote
- **Application logs**: 30 days local, 1 year remote
- **Configuration files**: All versions in git, daily snapshots

### Recovery Procedures

**Redis data recovery**:

```bash

# Stop Redis service
sudo systemctl stop redis

# Restore from RDB backup
cp /opt/backups/redis/redis_20241210_020000.rdb.gz /var/lib/redis/
gunzip /var/lib/redis/dump.rdb.gz
mv /var/lib/redis/dump.rdb /var/lib/redis/dump.rdb.backup

# Start Redis service
sudo systemctl start redis
```

**Model artifact recovery**:

```bash
# Extract model snapshot
tar -xzf /opt/backups/models/snapshot_20241210_030000.tar.gz -C /opt/goblinmini-docqa/

# Verify integrity
/opt/goblinmini-docqa/verify-models.sh /opt/backups/models/snapshot_20241210_030000.tar.gz

# Restart service
sudo systemctl restart goblinmini-docqa
```

**Complete system recovery** (from scratch):

```bash

# 1. Restore from infrastructure as code
terraform apply

# 2. Restore Redis data

# (Follow Redis recovery steps above)

# 3. Restore model artifacts

# (Follow model recovery steps above)

# 4. Restore application configuration
git checkout main
ansible-playbook deploy.yml

# 5. Verify system health
curl <https://api.goblinmini-docqa.com/health>
```

## Scaling Considerations

For high-traffic deployments:

1. **Keep web server single instance** (single listener rule)
2. **Scale inference services separately** (model sharding)
3. **Use load balancer** for multiple web servers (if needed)
4. **Implement caching** (Redis, CDN)
5. **Monitor resource usage** continuously

## Backup and Recovery

**Redis Data**:

```bash
# Docker
docker compose exec redis redis-cli save

# systemd
redis-cli -s /run/redis.sock save
```

**Application Logs**:

- systemd: `journalctl`
- Docker: `docker compose logs`
