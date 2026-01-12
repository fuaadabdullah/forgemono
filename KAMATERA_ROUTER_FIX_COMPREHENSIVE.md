# 🔧 Kamatera Router Network Fix - Comprehensive Guide

## Executive Summary

The Goblin Assistant chat is failing with **"All servers unavailable"** because:

1. **Firewall Issue**: No traffic allowed between Router (45.61.51.220) and Inference (192.175.23.150) servers
2. **Configuration Issue**: Router is configured to use wrong internal IP (172.16.0.1 instead of 192.175.23.150)
3. **Health Check Failure**: Router cannot verify that Inference server is healthy

## Architecture

```txt
User Frontend
    ↓ (HTTPS)
    ↓
Cloudflare Edge Worker (goblin.fuaad.ai)
    ↓ (HTTPS)
    ↓
Router API Server (45.61.51.220:8000)
    ↓ (HTTP - BLOCKED BY FIREWALL!)
    ↓ ❌ Cannot reach
    ↓
Inference Server (192.175.23.150:8002)
    └─ Ollama LLM with models
```

## Root Causes

### 1. Firewall Blocks Inter-Server Traffic

**Symptom**: TCP connection times out when Router tries to reach Inference on port 8002

**Current State**:

```bash
# On INFERENCE SERVER (192.175.23.150)
sudo ufw status
# Status: active
# (but no rule allows traffic FROM 45.61.51.220)

# On ROUTER SERVER (45.61.51.220)
sudo ufw status
# Status: active
# (but no rule allows outbound to 192.175.23.150:8002)
```

**Fix**:

```bash
# ON INFERENCE SERVER
sudo ufw allow from 45.61.51.220 to any port 8002

# ON ROUTER SERVER
sudo ufw allow out to 192.175.23.150 port 8002
```

### 2. Router Configuration Points to Wrong IP

**File**: `/etc/systemd/system/goblin-router.service`

**Current State**:
```ini
Environment="INFERENCE_URL=http://172.16.0.1:8002"
```

**Problem**: 172.16.0.1 is a private network address, not reachable from 45.61.51.220

**Fix**:
```ini
Environment="INFERENCE_URL=http://192.175.23.150:8002"
```

**How to Update**:
```bash
# SSH to Router Server
ssh root@45.61.51.220

# Update the configuration
sudo sed -i 's|Environment="INFERENCE_URL=.*"|Environment="INFERENCE_URL=http://192.175.23.150:8002"|' /etc/systemd/system/goblin-router.service

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart goblin-router
```

### 3. Health Check Fails Due to No Connectivity

**In Router's bootstrap_router.sh**:
```python
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
```

**Current Behavior**:
1. Health check tries to reach 172.16.0.1:8002 (wrong IP)
2. Connection fails
3. Router thinks Inference is down
4. Sets `FAILOVER_MODE = true`
5. Routes all requests to Ollama on Router server
6. Chat fails because Router's Ollama doesn't have proper models

**Result in Router Logs**:
```
Inference health check failed: Connection refused
FAILOVER ACTIVATED: Inference server down, routing to fallback
```

**Result in Chat Response**:
```json
{"detail":"All servers unavailable"}
```

## Implementation Steps

### Phase 1: Network Configuration (5 minutes)

#### Step 1A: Update Inference Server Firewall

**SSH to Inference Server**:
```bash
ssh root@192.175.23.150
```

**Run**:
```bash
# Allow Router to connect on port 8002
sudo ufw allow from 45.61.51.220 to any port 8002 comment "Router LLM API Access"

# Verify
sudo ufw status | grep 8002
```

**Expected Output**:
```
8002/tcp                   ALLOW       45.61.51.220
```

#### Step 1B: Update Router Server Firewall

**SSH to Router Server**:
```bash
ssh root@45.61.51.220
```

**Run**:
```bash
# Allow outbound to Inference server on port 8002
sudo ufw allow out to 192.175.23.150 port 8002 comment "Inference Server LLM API"

# Verify
sudo ufw status | grep -E "(out|192.175)"
```

**Expected Output**:
```
8002/tcp                   ALLOW OUT   192.175.23.150
```

### Phase 2: Configuration Update (3 minutes)

**On Router Server (45.61.51.220)**:

```bash
# Update systemd service with correct IP
sudo sed -i 's|Environment="INFERENCE_URL=.*"|Environment="INFERENCE_URL=http://192.175.23.150:8002"|' /etc/systemd/system/goblin-router.service

# Reload daemon configuration
sudo systemctl daemon-reload

# Verify the change
sudo grep INFERENCE_URL /etc/systemd/system/goblin-router.service
# Should output:
# Environment="INFERENCE_URL=http://192.175.23.150:8002"
```

### Phase 3: Service Restart (2 minutes)

#### Step 3A: Restart Inference Server Services

**On Inference Server (192.175.23.150)**:

```bash
ssh root@192.175.23.150

# Restart the LLM service
sudo systemctl restart local-llm-proxy

# Wait for startup
sleep 5

# Verify it's running
sudo systemctl status local-llm-proxy --no-pager

# Check if port is listening
sudo ss -tlnp | grep 8002
```

**Expected Output**:
```
LISTEN 0  128  0.0.0.0:8002  0.0.0.0:*  pid=xxxx/python3
```

#### Step 3B: Restart Router Services

**On Router Server (45.61.51.220)**:

```bash
ssh root@45.61.51.220

# Restart the router service
sudo systemctl restart goblin-router

# Wait for startup
sleep 5

# Verify it's running
sudo systemctl status goblin-router --no-pager

# Check if port is listening
sudo ss -tlnp | grep 8000
```

**Expected Output**:
```
LISTEN 0  128  0.0.0.0:8000  0.0.0.0:*  pid=xxxx/python3
```

### Phase 4: Verification (5 minutes)

#### Test 1: Basic Connectivity

**From Router Server**:
```bash
ssh root@45.61.51.220

# Test TCP connection to Inference on port 8002
timeout 5 bash -c 'echo > /dev/tcp/192.175.23.150/8002' && echo "✅ Port open" || echo "❌ Port closed"
```

**Expected**: `✅ Port open`

#### Test 2: Health Check Endpoint

**From Router Server**:
```bash
ssh root@45.61.51.220

# Test Inference health endpoint
curl -v http://192.175.23.150:8002/health \
  -H 'X-API-Key: 206e61fdeda2267c9a4ecac3997c4eae7ebd20038282445f7524a84a78ac0158'
```

**Expected Response**:
```json
{"status":"healthy","service":"local-llm-proxy"}
```

or
```json
{"status":"ok"}
```

#### Test 3: Chat Completion Through Router

**Test chat completion**:
```bash
curl -X POST http://45.61.51.220:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: cef5587890c73a5316a9a2c4ed851d97beb89fd28443885aad6e570dabd5f765' \
  -d '{
    "model": "llama2:7b",
    "messages": [{"role": "user", "content": "Say hello in one word"}],
    "temperature": 0.7,
    "max_tokens": 50
  }'
```

**Expected Response**:
```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "llama2:7b",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello!"
      },
      "finish_reason": "stop"
    }
  ]
}
```

**NOT Expected** (indicates fix didn't work):
```json
{"detail":"All servers unavailable"}
```

#### Test 4: Frontend Chat

Once tests pass on backend:

1. Open frontend at https://goblin.fuaad.ai
2. Send test message
3. Verify response from LLM (not error)

## Automated Fix Scripts

### Option A: Automated Script (Recommended)

Run the provided script that handles all steps:

```bash
bash kamatera_infrastructure_fix.sh
```

This script will:
- ✅ Configure firewall on both servers
- ✅ Update Router configuration
- ✅ Restart services
- ✅ Run connectivity tests
- ✅ Test chat completion
- ✅ Display summary

### Option B: Manual Steps

Follow the step-by-step guide in `kamatera_manual_fix_guide.sh`

## Monitoring & Debugging

### Router Logs

```bash
ssh root@45.61.51.220
sudo journalctl -u goblin-router -f --output=short
```

**Look for**:
- ❌ `Inference health check failed: Connection refused` → Firewall/connectivity issue
- ✅ `FAILOVER DEACTIVATED: Inference server restored` → Health check now passes

### Inference Server Logs

```bash
ssh root@192.175.23.150
sudo journalctl -u local-llm-proxy -f --output=short
```

**Look for**:
- Requests from Router server (45.61.51.220)
- Response times
- Any connection errors

### Network Diagnostics

**From Router Server**:
```bash
ssh root@45.61.51.220

# View firewall rules
sudo ufw show added

# Test route
traceroute 192.175.23.150

# Monitor connections
sudo ss -tan | grep 8002

# Packet capture (advanced)
sudo tcpdump -i any 'tcp port 8002'
```

## Rollback / Revert

If something goes wrong, revert the firewall changes:

```bash
# On Inference Server
ssh root@192.175.23.150
sudo ufw delete allow from 45.61.51.220 to any port 8002

# On Router Server
ssh root@45.61.51.220
sudo ufw delete allow out to 192.175.23.150 port 8002

# Restart services
sudo systemctl restart goblin-router
```

## Expected Behavior After Fix

### Router Health Check Flow

**Before Fix** ❌:
```
Router → Health Check → 172.16.0.1:8002
                        ↓
                    Connection timeout
                        ↓
                    Mark as unhealthy
                        ↓
                    Failover mode active
                        ↓
                    Route to local Ollama (limited models)
                        ↓
                    Chat fails or slow
```

**After Fix** ✅:
```
Router → Health Check → 192.175.23.150:8002
                        ↓
                    HTTP 200 response
                        ↓
                    Mark as healthy
                        ↓
                    Failover mode inactive
                        ↓
                    Route to Inference server (full capability)
                        ↓
                    Chat works with best available model
```

### Chat Flow

**Before Fix** ❌:
```
Frontend → Router API → Check Inference health
                        ↓ (Fails - 172.16.0.1 unreachable)
                        ↓
                    Use local Ollama fallback
                        ↓
                    Response may be incomplete or slow
                        ↓
                    Or "All servers unavailable"
```

**After Fix** ✅:
```
Frontend → Router API → Check Inference health
                        ↓ (Passes - 192.175.23.150 reachable)
                        ↓
                    Route to Inference server intelligently
                        ↓
                    Use best available LLM model
                        ↓
                    Fast, quality response
```

## Prevention for Future

To prevent similar issues:

1. **Document IP Addresses**: Maintain a configuration registry with all IPs and purposes
2. **Test Connectivity**: Include network tests in health checks
3. **Monitor Firewall**: Alert when firewall rules change
4. **Use DNS**: Replace hardcoded IPs with DNS names where possible
5. **Configuration Management**: Use environment variables for all IPs
6. **Health Checks**: Implement comprehensive health checks that include:
   - TCP connectivity
   - HTTP response
   - Response time
   - Error responses

## References

- `bootstrap_router.sh`: Router service implementation
- `kamatera_chat_final_report.md`: Previous analysis of the issue
- `kamatera_router_network_fix.py`: Diagnostic tool
- `deployments/kamatera/docker-compose.kamatera.yml`: Docker compose with correct IPs

## Support

If issues persist after applying these fixes:

1. Check logs on both servers
2. Verify firewall rules with `sudo ufw status`
3. Test with manual curl commands
4. Review network configuration with `ip route show`
5. Run packet capture to see actual traffic

---

**Last Updated**: January 6, 2026
**Status**: Ready for Implementation
