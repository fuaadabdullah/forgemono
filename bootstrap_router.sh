#!/usr/bin/env bash
set -euo pipefail
# bootstrap_router.sh - run as root or with sudo

## CONFIG - edit if needed
ROUTER_USER="fuaad"
INFERENCE_INTERNAL_IP="172.16.0.1"
INFERENCE_API_PORT=8002
PUBLIC_DOMAIN="yourdomain.com"   # set if you have domain
LOCAL_API_PORT=443
DB_NAME="goblin"
DB_USER="goblin"
DB_PASS="$(openssl rand -hex 16)"

echo "Starting router/control-plane bootstrap..."

# 1) basic packages
apt update 2>/dev/null || apt update --allow-releaseinfo-change 2>/dev/null || true
apt upgrade -y
apt install -y build-essential git curl wget python3 python3-venv python3-pip \
  nginx ufw rclone redis-server postgresql postgresql-contrib certbot python3-certbot-nginx

# 1.5) Install Ollama for fallback model
echo "Installing Ollama for local LLM fallback..."
curl -fsSL https://ollama.ai/install.sh | sh
systemctl enable ollama
systemctl start ollama
sleep 5
# Pull small fallback model
ollama pull llama3.2:1b

# 1.6) Start Redis for caching
echo "Starting Redis for response caching..."
systemctl enable redis-server
systemctl start redis-server

# 2) create user
id -u $ROUTER_USER &>/dev/null || adduser --disabled-password --gecos "" $ROUTER_USER
usermod -aG sudo $ROUTER_USER

# 3) postgres setup (simple local install)
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';" || true
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" || true

# 4) python env for router
sudo -u $ROUTER_USER bash <<'BASH'
cd ~
python3 -m venv router-venv
source router-venv/bin/activate
pip install --upgrade pip
pip install fastapi uvicorn httpx python-dotenv psycopg2-binary redis
deactivate
BASH

# 5) small router skeleton (forwards to inference with intent classification)
ROUTER_DIR="/home/$ROUTER_USER/goblin_router"
mkdir -p $ROUTER_DIR
cat > $ROUTER_DIR/app.py <<'PY'
from fastapi import FastAPI, Request, HTTPException
import os, httpx, json, re, redis, hashlib, time, asyncio

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    """Start background health monitoring on app startup"""
    asyncio.create_task(health_monitor())

INFERENCE_URL = os.getenv("INFERENCE_URL","http://172.16.0.1:8002")
INFERENCE_API_KEY = os.getenv("INFERENCE_API_KEY","changeme")
PUBLIC_API_KEY = os.getenv("PUBLIC_API_KEY","publicchangeme")  # used by clients
OLLAMA_URL = "http://localhost:11434"

# Redis for caching
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
CACHE_TTL = 3600  # 1 hour cache for responses

# Metrics tracking
METRICS_PREFIX = "goblin_router:metrics:"

def increment_metric(metric_name, amount=1):
    """Increment a metric counter in Redis"""
    try:
        key = f"{METRICS_PREFIX}{metric_name}"
        redis_client.incrby(key, amount)
        # Set expiry to prevent unbounded growth (30 days)
        redis_client.expire(key, 2592000)
    except Exception as e:
        print(f"Metrics error: {e}")

def get_metric(metric_name):
    """Get a metric value"""
    try:
        key = f"{METRICS_PREFIX}{metric_name}"
        return int(redis_client.get(key) or 0)
    except Exception as e:
        print(f"Metrics get error: {e}")
        return 0

def record_response_time(server, duration_ms):
    """Record response time for a server"""
    try:
        # Store in a sorted set for percentile calculations
        key = f"{METRICS_PREFIX}response_times:{server}"
        timestamp = int(time.time() * 1000)  # milliseconds
        redis_client.zadd(key, {f"{timestamp}:{duration_ms}": timestamp})
        # Keep only last 1000 entries to prevent unbounded growth
        redis_client.zremrangebyrank(key, 0, -1001)
        redis_client.expire(key, 2592000)
    except Exception as e:
        print(f"Response time recording error: {e}")

# Health monitoring and failover
INFERENCE_HEALTH_KEY = f"{METRICS_PREFIX}inference_health"
FAILOVER_MODE_KEY = f"{METRICS_PREFIX}failover_mode"
HEALTH_CHECK_INTERVAL = 30  # seconds
HEALTH_TIMEOUT = 10  # seconds
MAX_FAILURES = 3  # consecutive failures before failover

async def check_inference_health():
    """Check if inference server is healthy"""
    try:
        async with httpx.AsyncClient(timeout=HEALTH_TIMEOUT) as client:
            response = await client.get(f"{INFERENCE_URL}/health",
                                     headers={"x-api-key": INFERENCE_API_KEY})
            return response.status_code == 200
    except Exception as e:
        print(f"Inference health check failed: {e}")
        return False

def get_inference_health_status():
    """Get current inference server health status"""
    try:
        status = redis_client.get(INFERENCE_HEALTH_KEY)
        return status == "healthy" if status else False
    except:
        return False

def set_inference_health_status(healthy):
    """Set inference server health status"""
    try:
        status = "healthy" if healthy else "unhealthy"
        redis_client.set(INFERENCE_HEALTH_KEY, status, ex=HEALTH_CHECK_INTERVAL * 2)
    except Exception as e:
        print(f"Failed to set health status: {e}")

def is_failover_mode():
    """Check if we're in failover mode"""
    try:
        return redis_client.get(FAILOVER_MODE_KEY) == "active"
    except:
        return False

def set_failover_mode(active):
    """Set failover mode"""
    try:
        mode = "active" if active else "inactive"
        redis_client.set(FAILOVER_MODE_KEY, mode)
        if active:
            increment_metric("failover_activations")
            print("🚨 FAILOVER ACTIVATED: Inference server down, routing to fallback")
        else:
            increment_metric("failover_deactivations")
            print("✅ FAILOVER DEACTIVATED: Inference server restored")
    except Exception as e:
        print(f"Failed to set failover mode: {e}")

async def send_alert(message):
    """Send alert about failover status"""
    try:
        # For now, just log the alert. In production, you could:
        # - Send email via SMTP
        # - Send webhook to monitoring service
        # - Send SMS via Twilio
        # - Post to Slack/Discord webhook
        print(f"🚨 ALERT: {message}")

        # Store alert in Redis for monitoring
        alert_key = f"{METRICS_PREFIX}alerts:{int(time.time())}"
        redis_client.set(alert_key, message, ex=86400)  # Keep alerts for 24 hours

    except Exception as e:
        print(f"Failed to send alert: {e}")

async def health_monitor():
    """Background health monitoring task"""
    consecutive_failures = 0

    while True:
        try:
            healthy = await check_inference_health()
            set_inference_health_status(healthy)

            if healthy:
                consecutive_failures = 0
                if is_failover_mode():
                    set_failover_mode(False)
                    await send_alert("Inference server restored - failover deactivated")
            else:
                consecutive_failures += 1
                increment_metric("inference_health_failures")

                if consecutive_failures >= MAX_FAILURES and not is_failover_mode():
                    set_failover_mode(True)
                    await send_alert(f"Inference server failed {MAX_FAILURES} consecutive health checks - activating failover")

        except Exception as e:
            print(f"Health monitor error: {e}")

        await asyncio.sleep(HEALTH_CHECK_INTERVAL)

def generate_cache_key(messages, model="auto"):
    """Generate a cache key from the conversation messages"""
    # Use the last user message + model as cache key
    last_user_msg = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            last_user_msg = msg.get("content", "").strip()
            break

    # Create hash of the message + model
    key_content = f"{model}:{last_user_msg}"
    return hashlib.md5(key_content.encode()).hexdigest()

def get_cached_response(cache_key):
    """Get cached response if available"""
    try:
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception as e:
        print(f"Cache read error: {e}")
    return None

def cache_response(cache_key, response):
    """Cache the response"""
    try:
        redis_client.setex(cache_key, CACHE_TTL, json.dumps(response))
    except Exception as e:
        print(f"Cache write error: {e}")

def classify_intent(messages):
    """Three-tier intent classification: simple, medium, complex"""
    if not messages:
        return "medium"

    # Get the last user message
    last_msg = None
    for msg in reversed(messages):
        if msg.get("role") == "user":
            last_msg = msg.get("content", "").lower()
            break

    if not last_msg:
        return "medium"

    # Simple patterns - basic conversational queries
    simple_patterns = [
        r'\b(hello|hi|hey|greetings)\b',
        r'\b(what.*time|what.*date|current time)\b',
        r'\b(how.*are.*you|how.*doing|how.*going)\b',
        r'\b(thank.*you|thanks|appreciate)\b',
        r'\b(yes|no|okay|sure|correct|right)\b',
        r'\b(weather|temperature|forecast)\b',
        r'\b(simple|basic|easy|quick)\b',
        r'\b(help|assist|support)\b'
    ]

    # Medium patterns - moderately complex queries
    medium_patterns = [
        r'\b(explain|describe|tell me about)\b',
        r'\b(what.*is|how.*works|why.*does)\b',
        r'\b(calculate|compute|math|formula)\b',
        r'\b(translate|convert|change)\b',
        r'\b(list|show|find|search|get)\b',
        r'\b(summary|overview|brief)\b',
        r'\b(medium|moderate|normal|average)\b',
        r'\b(question|answer|clarify)\b',
        r'\b(example|instance|case)\b'
    ]

    # Complex patterns - advanced reasoning, coding, analysis
    complex_patterns = [
        r'\b(code|programming|function|class|algorithm|script)\b',
        r'\b(analyze|research|study|investigate|deep dive)\b',
        r'\b(write|create|generate|design|build|develop)\b',
        r'\b(complex|advanced|difficult|challenging)\b',
        r'\b(compare|contrast|evaluate|assess)\b',
        r'\b(multiple|several|many|various|diverse)\b',
        r'\b(strategy|plan|approach|methodology)\b',
        r'\b(optimize|improve|enhance|refactor)\b',
        r'\b(debug|troubleshoot|fix|resolve)\b',
        r'\b(architecture|system|framework|infrastructure)\b'
    ]

    # Check for complex intent first (highest priority)
    for pattern in complex_patterns:
        if re.search(pattern, last_msg):
            return "complex"

    # Check for medium intent
    for pattern in medium_patterns:
        if re.search(pattern, last_msg):
            return "medium"

    # Check for simple intent
    for pattern in simple_patterns:
        if re.search(pattern, last_msg):
            return "simple"

    # Default to medium for unknown patterns
    return "medium"

async def call_ollama(payload):
    """Call local Ollama for simple queries"""
    try:
        # Convert OpenAI format to Ollama format
        ollama_payload = {
            "model": "llama3.2:1b",
            "prompt": payload["messages"][-1]["content"] if payload.get("messages") else "Hello",
            "stream": False
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(f"{OLLAMA_URL}/api/generate", json=ollama_payload)
            response.raise_for_status()
            result = response.json()

            # Convert back to OpenAI format
            return {
                "id": f"ollama-{hash(str(payload))}",
                "object": "chat.completion",
                "created": 1234567890,
                "model": "llama3.2:1b",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": result.get("response", "I couldn't generate a response.")
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": len(ollama_payload["prompt"]),
                    "completion_tokens": len(result.get("response", "")),
                    "total_tokens": len(ollama_payload["prompt"]) + len(result.get("response", ""))
                }
            }
    except Exception as e:
        # Fallback to inference server if Ollama fails
        print(f"Ollama failed: {e}")
        return None

@app.get("/health")
async def health():
    redis_status = "ok"
    try:
        redis_client.ping()
    except Exception as e:
        redis_status = f"error: {str(e)}"

    inference_healthy = get_inference_health_status()
    failover_active = is_failover_mode()

    return {
        "ok": True,
        "inference": {
            "url": INFERENCE_URL,
            "healthy": inference_healthy,
            "status": "healthy" if inference_healthy else "unhealthy"
        },
        "ollama": OLLAMA_URL,
        "redis": redis_status,
        "failover": {
            "active": failover_active,
            "mode": "active" if failover_active else "normal"
        }
    }

@app.post("/v1/chat/completions")
async def chat(request: Request):
    start_time = time.time()

    key = request.headers.get("x-api-key")
    if key != PUBLIC_API_KEY:
        increment_metric("auth_failures")
        raise HTTPException(status_code=401, detail="invalid public api key")

    payload = await request.json()
    messages = payload.get("messages", [])

    increment_metric("total_requests")

    # Check cache first
    cache_key = generate_cache_key(messages, payload.get("model", "auto"))
    cached_response = get_cached_response(cache_key)
    if cached_response:
        increment_metric("cache_hits")
        duration_ms = int((time.time() - start_time) * 1000)
        record_response_time("cache", duration_ms)
        print(f"Cache hit for key: {cache_key} ({duration_ms}ms)")
        return cached_response

    increment_metric("cache_misses")
    print(f"Cache miss for key: {cache_key}")

    # Classify intent
    intent = classify_intent(messages)
    increment_metric(f"intent_{intent}")

    server_used = "unknown"
    response = None

    try:
        # Check if we're in failover mode
        failover_active = is_failover_mode()
        if failover_active:
            increment_metric("failover_requests")
            print(f"🔄 FAILOVER MODE: Routing {intent} request to Ollama")

        if intent == "simple" or failover_active:
            # Try local Ollama for simple queries or all queries in failover mode
            server_start = time.time()
            ollama_response = await call_ollama(payload)
            if ollama_response:
                response = ollama_response
                server_used = "ollama_simple" if intent == "simple" else "ollama_failover"
                increment_metric(f"server_{server_used.replace('_', '_')}")
                ollama_duration = int((time.time() - server_start) * 1000)
                record_response_time(server_used, ollama_duration)

        elif intent == "medium" and not failover_active:
            # Route medium complexity to inference server with medium model (only if not in failover)
            server_start = time.time()
            payload_with_hint = payload.copy()
            payload_with_hint["model_hint"] = "medium"
            headers = {"x-api-key": INFERENCE_API_KEY, "Content-Type": "application/json"}
            async with httpx.AsyncClient(timeout=120) as c:
                r = await c.post(INFERENCE_URL + "/v1/chat/completions", json=payload_with_hint, headers=headers)
                r.raise_for_status()
                response = r.json()
                server_used = "inference_medium"
                increment_metric("server_inference_medium")
                inference_duration = int((time.time() - server_start) * 1000)
                record_response_time("inference_medium", inference_duration)

        elif intent == "complex" and not failover_active:
            # Route complex queries to inference server with complex model (only if not in failover)
            server_start = time.time()
            payload_with_hint = payload.copy()
            payload_with_hint["model_hint"] = "complex"
            headers = {"x-api-key": INFERENCE_API_KEY, "Content-Type": "application/json"}
            async with httpx.AsyncClient(timeout=120) as c:
                r = await c.post(INFERENCE_URL + "/v1/chat/completions", json=payload_with_hint, headers=headers)
                r.raise_for_status()
                response = r.json()
                server_used = "inference_complex"
                increment_metric("server_inference_complex")
                inference_duration = int((time.time() - server_start) * 1000)
                record_response_time("inference_complex", inference_duration)

        # Final fallback: if no response yet, try Ollama as last resort
        if response is None:
            print("⚠️  No response from primary servers, trying Ollama fallback")
            server_start = time.time()
            ollama_response = await call_ollama(payload)
            if ollama_response:
                response = ollama_response
                server_used = "ollama_fallback"
                increment_metric("server_ollama_fallback")
                ollama_duration = int((time.time() - server_start) * 1000)
                record_response_time("ollama_fallback", ollama_duration)
            else:
                raise HTTPException(status_code=503, detail="All servers unavailable")

        increment_metric("successful_responses")

        # Cache the response
        cache_response(cache_key, response)

    except Exception as e:
        increment_metric("errors_total")
        increment_metric(f"errors_{server_used}")
        print(f"Error with {server_used}: {e}")
        raise

    total_duration = int((time.time() - start_time) * 1000)
    record_response_time("total", total_duration)

    print(f"Request completed: intent={intent}, server={server_used}, duration={total_duration}ms")

    return response

@app.get("/cache/stats")
async def cache_stats():
    """Get cache statistics"""
    try:
        info = redis_client.info()
        keys = redis_client.dbsize()
        return {
            "total_keys": keys,
            "redis_info": {
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human"),
                "total_connections_received": info.get("total_connections_received")
            }
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/cache/clear")
async def clear_cache():
    """Clear all cached responses"""
    try:
        redis_client.flushdb()
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def get_metrics():
    """Get comprehensive load metrics"""
    try:
        # Get all metrics keys
        keys = redis_client.keys(f"{METRICS_PREFIX}*")
        metrics = {}

        for key in keys:
            metric_name = key.replace(METRICS_PREFIX, "")
            if metric_name.startswith("response_times:"):
                # Calculate percentiles for response times
                server = metric_name.replace("response_times:", "")
                times = redis_client.zrange(key, 0, -1, withscores=False)
                if times:
                    durations = [int(t.split(":")[1]) for t in times[-100:]]  # Last 100 samples
                    durations.sort()
                    metrics[f"{server}_response_times"] = {
                        "count": len(durations),
                        "p50": durations[len(durations)//2] if durations else 0,
                        "p95": durations[int(len(durations)*0.95)] if durations else 0,
                        "p99": durations[int(len(durations)*0.99)] if durations else 0,
                        "avg": sum(durations)//len(durations) if durations else 0
                    }
            else:
                metrics[metric_name] = get_metric(metric_name)

        # Calculate derived metrics
        total_requests = metrics.get("total_requests", 0)
        cache_hits = metrics.get("cache_hits", 0)
        cache_misses = metrics.get("cache_misses", 0)

        if total_requests > 0:
            metrics["cache_hit_rate"] = round(cache_hits / total_requests * 100, 2)

        intent_simple = metrics.get("intent_simple", 0)
        intent_medium = metrics.get("intent_medium", 0)
        intent_complex = metrics.get("intent_complex", 0)
        total_intents = intent_simple + intent_medium + intent_complex

        if total_intents > 0:
            metrics["intent_distribution"] = {
                "simple_percent": round(intent_simple / total_intents * 100, 2),
                "medium_percent": round(intent_medium / total_intents * 100, 2),
                "complex_percent": round(intent_complex / total_intents * 100, 2)
            }

        # Calculate server usage including failover metrics
        server_ollama_simple = metrics.get("server_ollama_simple", 0)
        server_ollama_failover = metrics.get("server_ollama_failover", 0)
        server_ollama_fallback = metrics.get("server_ollama_fallback", 0)
        server_inference_medium = metrics.get("server_inference_medium", 0)
        server_inference_complex = metrics.get("server_inference_complex", 0)
        server_inference_fallback = metrics.get("server_inference_fallback", 0)

        total_servers = (server_ollama_simple + server_ollama_failover + server_ollama_fallback +
                        server_inference_medium + server_inference_complex + server_inference_fallback)

        if total_servers > 0:
            metrics["server_distribution"] = {
                "ollama_simple_percent": round(server_ollama_simple / total_servers * 100, 2),
                "ollama_failover_percent": round(server_ollama_failover / total_servers * 100, 2),
                "ollama_fallback_percent": round(server_ollama_fallback / total_servers * 100, 2),
                "inference_medium_percent": round(server_inference_medium / total_servers * 100, 2),
                "inference_complex_percent": round(server_inference_complex / total_servers * 100, 2),
                "inference_fallback_percent": round(server_inference_fallback / total_servers * 100, 2)
            }

        # Add failover status
        metrics["failover"] = {
            "active": is_failover_mode(),
            "activations": metrics.get("failover_activations", 0),
            "deactivations": metrics.get("failover_deactivations", 0),
            "requests_during_failover": metrics.get("failover_requests", 0),
            "inference_health_failures": metrics.get("inference_health_failures", 0)
        }

        return metrics

    except Exception as e:
        return {"error": str(e)}
PY

chown -R $ROUTER_USER:$ROUTER_USER $ROUTER_DIR
chmod 750 $ROUTER_DIR

# 6) systemd for router
cat >/etc/systemd/system/goblin-router.service <<'UNIT'
[Unit]
Description=Goblin Router API
After=network.target ollama.service redis-server.service

[Service]
User=ROUTER_USER_REPLACE
WorkingDirectory=/home/ROUTER_USER_REPLACE/goblin_router
Environment="INFERENCE_URL=http://INFERENCE_IP_REPLACE:8002"
Environment="INFERENCE_API_KEY=REPLACE_WITH_INFERENCE_KEY"
Environment="PUBLIC_API_KEY=REPLACE_WITH_PUBLIC_KEY"
ExecStart=/home/ROUTER_USER_REPLACE/router-venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000 --workers 1
Restart=on-failure
LimitNOFILE=65536
MemoryMax=8G
[Install]
WantedBy=multi-user.target
UNIT

# replace placeholders
sed -i "s|ROUTER_USER_REPLACE|$ROUTER_USER|g" /etc/systemd/system/goblin-router.service
sed -i "s|INFERENCE_IP_REPLACE|$INFERENCE_INTERNAL_IP|g" /etc/systemd/system/goblin-router.service
sed -i "s|REPLACE_WITH_INFERENCE_KEY|$(openssl rand -hex 32)|g" /etc/systemd/system/goblin-router.service
sed -i "s|REPLACE_WITH_PUBLIC_KEY|$(openssl rand -hex 32)|g" /etc/systemd/system/goblin-router.service

# 7) nginx config - public endpoint and proxy to router
cat >/etc/nginx/sites-available/goblin-router.conf <<'NGINX'
server {
    listen 80;
    server_name PUBLIC_HOST;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 300s;
    }
}
NGINX

sed -i "s|PUBLIC_HOST|$PUBLIC_DOMAIN|g" /etc/nginx/sites-available/goblin-router.conf
ln -sf /etc/nginx/sites-available/goblin-router.conf /etc/nginx/sites-enabled/goblin-router.conf
rm -f /etc/nginx/sites-enabled/default || true
systemctl restart nginx

# 8) firewall: open SSH + HTTP/HTTPS; allow router -> inference internal access + logging ports
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
# Loki ports (for Promtail from inference server)
ufw allow from $INFERENCE_INTERNAL_IP to any port 3100
ufw allow from $INFERENCE_INTERNAL_IP to any port 9096
# Grafana port (local access)
ufw allow 3000/tcp
# ensure router can reach inference's port on the LAN (already covered by LAN)
ufw --force enable

# 9) enable services
systemctl daemon-reload
systemctl enable --now goblin-router

# 10) Deploy Loki + Grafana for centralized logging
echo "Setting up Loki + Grafana for centralized logging..."

# Install Docker for containerized Loki/Grafana
apt install -y docker.io
systemctl enable docker
systemctl start docker

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose

# Create logging stack directory
LOGGING_DIR="/opt/goblin-logging"
mkdir -p "$LOGGING_DIR"

# Loki configuration
cat > "$LOGGING_DIR/loki-config.yaml" <<'LOKI_EOF'
auth_enabled: false

server:
  http_listen_port: 3100
  grpc_listen_port: 9096

common:
  instance_addr: 127.0.0.1
  path_prefix: /tmp/loki
  storage:
    filesystem:
      chunks_directory: /tmp/loki/chunks
      rules_directory: /tmp/loki/rules
  replication_factor: 1
  ring:
    kvstore:
      store: inmemory

query_range:
  results_cache:
    cache:
      embedded_cache:
        enabled: true
        max_size_mb: 100

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

ruler:
  alertmanager_url: http://localhost:9093

# Enable analytics for better query performance
analytics:
  reporting_enabled: false
LOKI_EOF

# Grafana configuration
cat > "$LOGGING_DIR/grafana-config.ini" <<'GRAFANA_EOF'
[server]
http_port = 3000
domain = localhost

[security]
admin_user = admin
admin_password = goblin_logs_2025!

[users]
allow_sign_up = false

[auth.anonymous]
enabled = true
org_role = Viewer

[log]
level = info
mode = console

[analytics]
reporting_enabled = false
GRAFANA_EOF

# Docker Compose for Loki + Grafana
cat > "$LOGGING_DIR/docker-compose.yml" <<'COMPOSE_EOF'
version: '3.8'

services:
  loki:
    image: grafana/loki:2.9.0
    container_name: goblin-loki
    ports:
      - "3100:3100"
      - "9096:9096"
    volumes:
      - ./loki-config.yaml:/etc/loki/local-config.yaml
      - loki_data:/tmp/loki
    command: -config.file=/etc/loki/local-config.yaml
    restart: unless-stopped
    networks:
      - logging

  grafana:
    image: grafana/grafana:10.2.0
    container_name: goblin-grafana
    ports:
      - "3000:3000"
    volumes:
      - ./grafana-config.ini:/etc/grafana/grafana.ini
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
      - ./grafana/dashboards:/var/lib/grafana/dashboards
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=goblin_logs_2025!
    restart: unless-stopped
    depends_on:
      - loki
    networks:
      - logging

volumes:
  loki_data:
    driver: local
  grafana_data:
    driver: local

networks:
  logging:
    driver: bridge
COMPOSE_EOF

# Create Grafana provisioning directories
mkdir -p "$LOGGING_DIR/grafana/provisioning/datasources"
mkdir -p "$LOGGING_DIR/grafana/provisioning/dashboards"
mkdir -p "$LOGGING_DIR/grafana/dashboards"

# Grafana Loki datasource
cat > "$LOGGING_DIR/grafana/provisioning/datasources/loki.yml" <<'DATASOURCE_EOF'
apiVersion: 1

datasources:
  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    isDefault: true
    editable: true
DATASOURCE_EOF

# Grafana dashboard provisioning
cat > "$LOGGING_DIR/grafana/provisioning/dashboards/dashboard.yml" <<'DASHBOARD_EOF'
apiVersion: 1

providers:
  - name: 'Goblin AI Logs'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
DASHBOARD_EOF

# Create main dashboard
cat > "$LOGGING_DIR/grafana/dashboards/goblin-overview.json" <<'DASHBOARD_EOF'
{
  "dashboard": {
    "id": null,
    "title": "Goblin AI System Overview",
    "tags": ["goblin", "ai", "logs"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Error Rate by Service",
        "type": "stat",
        "targets": [
          {
            "expr": "rate({job=~\"goblin.*\"} |= \"ERROR\" [5m])",
            "legendFormat": "{{job}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "thresholds"
            },
            "thresholds": {
              "mode": "absolute",
              "steps": [
                { "color": "green", "value": null },
                { "color": "orange", "value": 0.1 },
                { "color": "red", "value": 1 }
              ]
            }
          }
        }
      },
      {
        "id": 2,
        "title": "Log Volume by Service",
        "type": "bargauge",
        "targets": [
          {
            "expr": "rate({job=~\"goblin.*\"} [5m])",
            "legendFormat": "{{job}}"
          }
        ]
      },
      {
        "id": 3,
        "title": "Recent Errors",
        "type": "logs",
        "targets": [
          {
            "expr": "{job=~\"goblin.*\"} |= \"ERROR\"",
            "legendFormat": ""
          }
        ]
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "30s"
  }
}
DASHBOARD_EOF

# Start logging stack
cd "$LOGGING_DIR"
docker-compose up -d

# Wait for services to be ready
sleep 10

# 11) Deploy Promtail for log collection
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

# Promtail configuration
mkdir -p /etc/promtail
cat > /etc/promtail/config.yml <<PROMTAIL_EOF
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://localhost:3100/loki/api/v1/push

scrape_configs:
  # System logs
  - job_name: systemd-router
    journal:
      max_age: 12h
      labels:
        job: goblin-router
        host: router
    relabel_configs:
      - source_labels: ['__journal__systemd_unit']
        target_label: 'unit'
      - source_labels: ['__journal__hostname']
        target_label: 'hostname'

  # Application logs
  - job_name: app-logs-router
    static_configs:
      - targets:
          - localhost
        labels:
          job: goblin-router-app
          host: router
          __path__: /var/log/goblin-router/*.log
    pipeline_stages:
      - match:
          selector: '{job="goblin-router-app"}'
          stages:
            - regex:
                expression: '^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (?P<level>\w+) (?P<message>.+)$'
            - labels:
                level: level

  # Nginx access logs
  - job_name: nginx-access
    static_configs:
      - targets:
          - localhost
        labels:
          job: goblin-router-nginx
          host: router
          __path__: /var/log/nginx/access.log
    pipeline_stages:
      - match:
          selector: '{job="goblin-router-nginx"}'
          stages:
            - regex:
                expression: '(?P<ip>\S+) - - \[(?P<timestamp>\d{2}\/\w{3}\/\d{4}:\d{2}:\d{2}:\d{2} \+\d{4})\] "(?P<method>\w+) (?P<path>\S+) (?P<protocol>\S+)" (?P<status>\d+) (?P<size>\d+)'
            - labels:
                method: method
                status: status
            - metrics:
                nginx_requests_total:
                  type: Counter
                  description: "Total nginx requests"
                  source: status
                  config:
                    action: inc

  # Docker container logs (if any)
  - job_name: docker-logs
    static_configs:
      - targets:
          - localhost
        labels:
          job: goblin-docker
          host: router
          __path__: /var/lib/docker/containers/*/*.log
    pipeline_stages:
      - docker: {}
PROMTAIL_EOF

# Create log directories
mkdir -p /var/log/goblin-router

# Enable and start Promtail
systemctl enable promtail
systemctl start promtail

# 12) Set up log rotation and archiving
echo "Setting up log rotation and cold storage..."

# Install awscli for S3 uploads
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
./aws/install --update
rm -rf aws awscliv2.zip

# Logrotate configuration for application logs
cat > /etc/logrotate.d/goblin-router <<'LOGROTATE_EOF'
/var/log/goblin-router/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
    postrotate
        systemctl reload goblin-router || true
    endscript
}
LOGROTATE_EOF

# Loki log retention script
cat > /usr/local/bin/loki-retention.sh <<'RETENTION_EOF'
#!/bin/bash
# Loki retention management script

LOKI_DATA_DIR="/opt/goblin-logging/loki_data"
S3_BUCKET="goblin-logs-archive"
RETENTION_DAYS=90

# Clean old Loki data (keep 7 days hot)
find "$LOKI_DATA_DIR" -name "*.gz" -mtime +7 -delete

# Archive and upload to S3 (keep 90 days cold)
ARCHIVE_DIR="/tmp/loki-archive"
mkdir -p "$ARCHIVE_DIR"

# Bundle logs older than 7 days
find "$LOKI_DATA_DIR" -name "*.gz" -mtime +7 -exec tar -czf "$ARCHIVE_DIR/loki-$(date +%Y%m%d).tar.gz" {} +

# Upload to S3
if [ -n "$(ls -A $ARCHIVE_DIR)" ]; then
    aws s3 sync "$ARCHIVE_DIR" "s3://$S3_BUCKET/$(date +%Y/%m)/" --delete
    # Clean up uploaded archives
    rm -f "$ARCHIVE_DIR"/*.tar.gz
fi

# Clean archives older than retention period
aws s3 rm "s3://$S3_BUCKET/" --recursive --exclude "*" --include "*/$(date -d "$RETENTION_DAYS days ago" +%Y%m%d)*"
RETENTION_EOF

chmod +x /usr/local/bin/loki-retention.sh

# Add to cron for daily execution
echo "0 2 * * * root /usr/local/bin/loki-retention.sh" > /etc/cron.d/loki-retention

# 13) Configure Grafana alerts
echo "Setting up Grafana alerts..."

# Create alert rules
mkdir -p "$LOGGING_DIR/grafana/provisioning/alerting"
cat > "$LOGGING_DIR/grafana/provisioning/alerting/alerts.yml" <<'ALERT_EOF'
apiVersion: 1

groups:
  - name: goblin-alerts
    rules:
      - alert: HighErrorRate
        expr: rate({job=~\"goblin.*\"} |= \"ERROR\" [5m]) > 0.5
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"

      - alert: ServiceDown
        expr: rate({job=~\"goblin.*\"} [5m]) == 0
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Service appears to be down"
          description: "No logs received from {{ $labels.job }} for 10 minutes"

      - alert: AuthFailures
        expr: rate({job=~\"goblin.*\"} |= \"auth\" |= \"401\" [5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High authentication failure rate"
          description: "Auth failures: {{ $value }} per second"

      - alert: StoragePressure
        expr: (1 - (disk_available_bytes / disk_total_bytes)) > 0.85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High disk usage"
          description: "Disk usage is {{ $value | humanizePercentage }}"
ALERT_EOF

# Restart Grafana to pick up new configuration
docker-compose restart grafana

echo "ROUTER BOOTSTRAP FINISHED."
echo "DB credentials:"
echo "  POSTGRES_DB=$DB_NAME"
echo "  POSTGRES_USER=$DB_USER"
echo "  POSTGRES_PASS=$DB_PASS"
echo ""
echo "Logging Infrastructure:"
echo "  Grafana: http://localhost:3000 (admin/goblin_logs_2025!)"
echo "  Loki: http://localhost:3100"
echo "  Promtail: localhost:9080"
echo ""
echo "Edit /etc/nginx/sites-available/goblin-router.conf and set PUBLIC_DOMAIN, then run certbot for TLS."
echo "Public API key stored in systemd unit. Keep it safe."
