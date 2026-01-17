#!/bin/bash
# Project: Goblin Assistant
# Script: server2-data-setup.sh
# Purpose: Setup Data/Compute Server (45.61.51.220) with Redis, PostgreSQL, Background Workers
# Date: 2025-12-18
# Maintainer: fuaadabdullah

set -e

SERVER_IP="45.61.51.220"
SERVER_NAME="goblin-data-compute"
USER="root"

echo "🚀 Setting up Data/Compute Server: $SERVER_NAME ($SERVER_IP)"
echo "============================================================"

# Update system
echo "📦 Updating system packages..."
apt update && apt upgrade -y

# Install essential packages
echo "🔧 Installing essential packages..."
apt install -y curl wget git build-essential cmake pkg-config \
    libssl-dev libffi-dev python3-dev python3-pip \
    nginx ufw fail2ban postgresql postgresql-contrib \
    redis-server docker.io docker-compose

# Enable and start services
echo "🚀 Starting essential services..."
systemctl enable postgresql
systemctl start postgresql
systemctl enable redis-server
systemctl start redis-server
systemctl enable docker
systemctl start docker

# Setup firewall
echo "🔥 Configuring firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 6379/tcp  # Redis
ufw allow 5432/tcp  # PostgreSQL
ufw allow 8000/tcp  # API Router
ufw allow 80/tcp    # Nginx
ufw allow 443/tcp   # Nginx
ufw --force enable

# Configure PostgreSQL
echo "🗄️ Configuring PostgreSQL..."
sudo -u postgres psql -c "CREATE DATABASE goblin_data;" || true
sudo -u postgres psql -c "CREATE USER goblin_user WITH PASSWORD 'REPLACE_WITH_SECURE_PASSWORD';" || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE goblin_data TO goblin_user;" || true

# Configure PostgreSQL to accept connections from Fly.io
echo "🔧 Updating PostgreSQL configuration..."
cat > /etc/postgresql/*/main/pg_hba.conf << 'EOF'
# PostgreSQL Client Authentication Configuration File
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             postgres                                peer
local   all             all                                     md5
host    all             all             127.0.0.1/32            md5
host    all             all             ::1/128                 md5
# Allow Fly.io connections
host    goblin_data     goblin_user     0.0.0.0/0               md5
# Allow all connections from anywhere (adjust as needed)
host    all             all             0.0.0.0/0               md5
EOF

# Configure PostgreSQL to listen on all interfaces
echo "🔧 Updating PostgreSQL to listen on all interfaces..."
sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/g" /etc/postgresql/*/main/postgresql.conf

# Restart PostgreSQL to apply changes
systemctl restart postgresql

# Configure Redis
echo "🔧 Configuring Redis..."
cat > /etc/redis/redis.conf << 'EOF'
# Redis Configuration for Goblin Assistant
bind 0.0.0.0
port 6379
timeout 0
tcp-keepalive 300
databases 16
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir /var/lib/redis
maxmemory 2gb
maxmemory-policy allkeys-lru
appendonly yes
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb
EOF

# Restart Redis with new configuration
systemctl restart redis

# Create Goblin Router API service
echo "🌐 Creating Goblin Router API service..."
mkdir -p /opt/goblin-router
cd /opt/goblin-router

# Create simple FastAPI router with authentication
cat > router.py << 'EOF'
#!/usr/bin/env python3
"""
Goblin Router API - Routes requests to appropriate services with API key authentication
"""

import os
import asyncio
import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import json

app = FastAPI(title="Goblin Router API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
LLM_SERVER_1 = os.getenv("LLM_SERVER_1", "http://192.175.23.150:8002")
LLM_SERVER_2 = os.getenv("LLM_SERVER_2", "http://192.175.23.150:8003")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
API_KEY = os.getenv("LOCAL_LLM_API_KEY", "")

# Authentication middleware
@app.middleware("http")
async def authenticate_request(request: Request, call_next):
    # Skip authentication for health checks
    if request.url.path in ["/health", "/docs", "/openapi.json", "/redoc"]:
        return await call_next(request)
    
    # Check API key
    if API_KEY:
        api_key_header = request.headers.get("x-api-key") or request.headers.get("authorization", "")
        if api_key_header.startswith("Bearer "):
            api_key_header = api_key_header[7:]  # Remove "Bearer " prefix
            
        if not api_key_header or api_key_header != API_KEY:
            return JSONResponse(
                status_code=401,
                content={
                    "error": {
                        "code": "authentication_required", 
                        "message": "Valid API key required",
                        "details": "Provide API key in x-api-key header or Authorization: Bearer <key> header"
                    }
                }
            )
    
    return await call_next(request)

class ChatRequest(BaseModel):
    model: str
    messages: list
    temperature: float = 0.7
    max_tokens: int = 2048

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "goblin-router"}

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    """Route chat completion requests to appropriate LLM server"""
    try:
        # Simple routing logic based on model size
        large_models = ["llama3.1:8b", "mistral:7b", "codellama:7b"]
        
        if any(model in request.model for model in large_models):
            # Route to primary LLM server (Ollama)
            target_server = LLM_SERVER_1
        else:
            # Route to secondary server or default
            target_server = LLM_SERVER_2
        
        # Forward request to target server with API key
        headers = {}
        if API_KEY:
            headers["x-api-key"] = API_KEY
            
        # Forward request to target server
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{target_server}/v1/chat/completions",
                json={
                    "model": request.model,
                    "messages": request.messages,
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens
                },
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail="LLM request failed")
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/models")
async def list_models():
    """List available models from both servers"""
    models = []
    
    headers = {}
    if API_KEY:
        headers["x-api-key"] = API_KEY
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Get models from primary server
            response1 = await client.get(f"{LLM_SERVER_1}/api/tags", headers=headers)
            if response1.status_code == 200:
                data1 = response1.json()
                models.extend([{"name": m["name"], "server": "primary"} for m in data1.get("models", [])])
            
            # Get models from secondary server
            response2 = await client.get(f"{LLM_SERVER_2}/api/tags", headers=headers)
            if response2.status_code == 200:
                data2 = response2.json()
                models.extend([{"name": m["name"], "server": "secondary"} for m in data2.get("models", [])])
    except:
        pass
    
    return {"models": models}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF

# Create requirements.txt
cat > requirements.txt << 'EOF'
fastapi
uvicorn[standard]
httpx
redis
celery
psycopg2-binary
sqlalchemy
pydantic
python-multipart
EOF

# Install Python dependencies
pip3 install -r requirements.txt

# Create Goblin Router systemd service
cat > /etc/systemd/system/goblin-router.service << 'EOF'
[Unit]
Description=Goblin Router API Service
After=network.target redis.service

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/goblin-router
ExecStart=/usr/bin/python3 /opt/goblin-router/router.py
Environment="LLM_SERVER_1=http://192.175.23.150:8002"
Environment="LLM_SERVER_2=http://192.175.23.150:8003"
Environment="REDIS_URL=redis://localhost:6379"
Environment="LOCAL_LLM_API_KEY=206e61fdeda2267c9a4ecac3997c4eae7ebd20038282445f7524a84a78ac0158"
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create Celery worker setup for background tasks
echo "⚙️ Setting up Celery background workers..."
mkdir -p /opt/celery
cd /opt/celery

# Create Celery app
cat > celery_app.py << 'EOF'
#!/usr/bin/env python3
"""
Celery app for Goblin Assistant background tasks
"""

import os
from celery import Celery

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
app = Celery('goblin_tasks', broker=REDIS_URL, backend=REDIS_URL)

# Configure Celery
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_routes={
        'tasks.high_priority': {'queue': 'high_priority'},
        'tasks.default': {'queue': 'default'},
        'tasks.low_priority': {'queue': 'low_priority'},
    },
)

@app.task(bind=True, name='tasks.high_priority')
def high_priority_task(self, data):
    """High priority background task"""
    try:
        # Process high priority task
        result = f"Processed high priority task: {data}"
        return result
    except Exception as exc:
        self.retry(countdown=60, exc=exc)

@app.task(bind=True, name='tasks.default')
def default_task(self, data):
    """Default priority background task"""
    try:
        # Process default task
        result = f"Processed default task: {data}"
        return result
    except Exception as exc:
        self.retry(countdown=120, exc=exc)

@app.task(bind=True, name='tasks.low_priority')
def low_priority_task(self, data):
    """Low priority background task"""
    try:
        # Process low priority task
        result = f"Processed low priority task: {data}"
        return result
    except Exception as exc:
        self.retry(countdown=300, exc=exc)

if __name__ == '__main__':
    app.start()
EOF

# Create Celery worker services
cat > /etc/systemd/system/celery-worker-high.service << 'EOF'
[Unit]
Description=Celery High Priority Worker
After=network.target redis.service

[Service]
Type=forking
User=root
Group=root
WorkingDirectory=/opt/celery
ExecStart=/usr/bin/celery -A celery_app worker --loglevel=info --concurrency=2 --pool=prefork -Q high_priority --detach
ExecStop=/usr/bin/celery -A celery_app control shutdown
ExecReload=/usr/bin/celery -A celery_app control reload

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/celery-worker-default.service << 'EOF'
[Unit]
Description=Celery Default Priority Worker
After=network.target redis.service

[Service]
Type=forking
User=root
Group=root
WorkingDirectory=/opt/celery
ExecStart=/usr/bin/celery -A celery_app worker --loglevel=info --concurrency=4 --pool=prefork -Q default --detach
ExecStop=/usr/bin/celery -A celery_app control shutdown
ExecReload=/usr/bin/celery -A celery_app control reload

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/celery-worker-low.service << 'EOF'
[Unit]
Description=Celery Low Priority Worker
After=network.target redis.service

[Service]
Type=forking
User=root
Group=root
WorkingDirectory=/opt/celery
ExecStart=/usr/bin/celery -A celery_app worker --loglevel=info --concurrency=2 --pool=prefork -Q low_priority --detach
ExecStop=/usr/bin/celery -A celery_app control shutdown
ExecReload=/usr/bin/celery -A celery_app control reload

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/celery-beat.service << 'EOF'
[Unit]
Description=Celery Beat Scheduler
After=network.target redis.service

[Service]
Type=forking
User=root
Group=root
WorkingDirectory=/opt/celery
ExecStart=/usr/bin/celery -A celery_app beat --loglevel=info --detach
ExecStop=/usr/bin/celery -A celery_app control shutdown
ExecReload=/usr/bin/celery -A celery_app control reload

[Install]
WantedBy=multi-user.target
EOF

# Install Celery
pip3 install celery redis

# Configure Nginx reverse proxy for API services
echo "🌐 Configuring Nginx reverse proxy..."
cat > /etc/nginx/sites-available/goblin-data << 'EOF'
server {
    listen 80;
    server_name localhost;

    # Goblin Router API
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
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

    # Redis connection (if needed for WebSocket)
    location /redis/ {
        proxy_pass http://127.0.0.1:6379/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
EOF

ln -sf /etc/nginx/sites-available/goblin-data /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
nginx -t

# Create monitoring script
cat > /opt/goblin-monitor.sh << 'EOF'
#!/bin/bash
# Monitor Data/Compute server health

echo "=== Goblin Data/Compute Server Health Check ==="
echo "Time: $(date)"
echo

echo "🗄️ PostgreSQL Status:"
systemctl is-active postgresql
echo "🔴 Redis Status:"
systemctl is-active redis
echo "🐳 Docker Status:"
systemctl is-active docker
echo "🌐 Goblin Router Status:"
systemctl is-active goblin-router
echo "⚙️ Celery Workers Status:"
systemctl is-active celery-worker-high
systemctl is-active celery-worker-default
systemctl is-active celery-worker-low
systemctl is-active celery-beat

echo
echo "📊 System Resources:"
echo "CPU: $(top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1)%"
echo "Memory: $(free | grep Mem | awk '{printf("%.1f%%", $3/$2 * 100.0)}')"
echo "Disk: $(df -h / | awk 'NR==2{printf "%s", $5}')"

echo
echo "🔗 Port Status:"
netstat -tlnp | grep -E ':5432|:6379|:8000'

echo
echo "🗄️ PostgreSQL Connections:"
sudo -u postgres psql -c "SELECT count(*) as active_connections FROM pg_stat_activity WHERE state = 'active';" 2>/dev/null || echo "⚠️ Cannot connect to PostgreSQL"

echo
echo "🔴 Redis Info:"
redis-cli info memory 2>/dev/null | grep used_memory_human || echo "⚠️ Redis not responding"

echo
echo "🌐 API Accessibility:"
curl -s -o /dev/null -w "%{http_code}" http://localhost/health || echo "FAIL"

echo
echo "🧠 LLM Server Connectivity:"
curl -s -o /dev/null -w "%{http_code}" http://192.175.23.150:8002/health || echo "FAIL"
EOF

chmod +x /opt/goblin-monitor.sh

# Create backup script for data
cat > /opt/goblin-backup.sh << 'EOF'
#!/bin/bash
# Backup PostgreSQL and Redis data

BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

echo "💾 Creating data backups..."

# Backup PostgreSQL
echo "🗄️ Backing up PostgreSQL..."
pg_dump -U goblin_user -h localhost goblin_data > "$BACKUP_DIR/postgres_$DATE.sql"
echo "✅ PostgreSQL backup: $BACKUP_DIR/postgres_$DATE.sql"

# Backup Redis
echo "🔴 Backing up Redis..."
redis-cli --rdb "$BACKUP_DIR/redis_$DATE.rdb"
echo "✅ Redis backup: $BACKUP_DIR/redis_$DATE.rdb"

# Compress backups
echo "🗜️ Compressing backups..."
gzip "$BACKUP_DIR/postgres_$DATE.sql"
gzip "$BACKUP_DIR/redis_$DATE.rdb"

# Keep only last 10 backups
cd "$BACKUP_DIR"
ls -t postgres_*.sql.gz | tail -n +11 | xargs -r rm
ls -t redis_*.rdb.gz | tail -n +11 | xargs -r rm

echo "🧹 Old backups cleaned up"
echo "🎉 Backup complete!"
EOF

chmod +x /opt/goblin-backup.sh

# Create cron jobs for backups and monitoring
echo "0 3 * *
