# Kamatera Router Network Fix - Comprehensive Guide

## Executive Summary

The Goblin Assistant chat is failing with **"All servers unavailable"** because:

1. **Firewall Issue**: No traffic allowed between Router (45.61.51.220) and Inference (192.175.23.150) servers
2. **Configuration Issue**: Router is configured to use wrong internal IP (172.16.0.1 instead of 192.175.23.150)
3. **Health Check Failure**: Router cannot verify that Inference server is healthy

---

## Root Causes

### Root Cause 1: Firewall Blocks Inter-Server Traffic

**Symptom**: TCP connection times out when Router tries to reach Inference on port 8002

**Current firewall state on both servers**: UFW is enabled but has no rules allowing traffic between them

**Fix Required**:

On INFERENCE SERVER (192.175.23.150):

```
sudo ufw allow from 45.61.51.220 to any port 8002
```

On ROUTER SERVER (45.61.51.220):

```
sudo ufw allow out to 192.175.23.150 port 8002
```

### Root Cause 2: Router Configuration Points to Wrong IP

**File**: `/etc/systemd/system/goblin-router.service`

**Current Configuration**:

```
Environment="INFERENCE_URL=http://172.16.0.1:8002"
```

**Problem**: 172.16.0.1 is a private network address that cannot be reached from 45.61.51.220

**Correct Configuration**:

```
Environment="INFERENCE_URL=http://192.175.23.150:8002"
```

**How to Update**:

```bash
ssh root@45.61.51.220
sudo sed -i 's|Environment="INFERENCE_URL=.*"|Environment="INFERENCE_URL=http://192.175.23.150:8002"|' /etc/systemd/system/goblin-router.service
sudo systemctl daemon-reload
sudo systemctl restart goblin-router
```

### Root Cause 3: Health Check Fails, Triggers Failover

**Location**: `bootstrap_router.sh` - `check_inference_health()` function

**Current Behavior Flow**:

1. Router tries to check if Inference is healthy
2. Connects to 172.16.0.1:8002 (wrong IP)
3. Connection fails due to firewall + wrong IP
4. Router sets `FAILOVER_MODE = true`
5. Routes all requests to local Ollama fallback
6. Chat returns "All servers unavailable"

**In Logs**:

```
Inference health check failed: Connection refused
FAILOVER ACTIVATED: Inference server down, routing to fallback
```

---

## Implementation Steps

### Step 1: Update Inference Server Firewall

**SSH to Inference Server**:

```bash
ssh root@192.175.23.150
```

**Run firewall command**:

```bash
sudo ufw allow from 45.61.51.220 to any port 8002 comment "Router LLM API Access"
```

**Verify**:

```bash
sudo ufw status | grep 8002
```

### Step 2: Update Router Server Firewall

**SSH to Router Server**:

```bash
ssh root@45.61.51.220
```

**Run firewall command**:

```bash
sudo ufw allow out to 192.175.23.150 port 8002 comment "Inference Server LLM API"
```

**Verify**:

```bash
sudo ufw status | grep -E "(out|192.175)"
```

### Step 3: Update Router Configuration

**On Router Server (45.61.51.220)**:

```bash
# Update the systemd service file
sudo sed -i 's|Environment="INFERENCE_URL=.*"|Environment="INFERENCE_URL=http://192.175.23.150:8002"|' /etc/systemd/system/goblin-router.service

# Reload configuration
sudo systemctl daemon-reload

# Verify the change
sudo grep INFERENCE_URL /etc/systemd/system/goblin-router.service
```

### Step 4: Restart Services

**On Inference Server (192.175.23.150)**:

```bash
ssh root@192.175.23.150
sudo systemctl restart local-llm-proxy
sleep 5
sudo systemctl status local-llm-proxy --no-pager
```

**On Router Server (45.61.51.220)**:

```bash
ssh root@45.61.51.220
sudo systemctl restart goblin-router
sleep 5
sudo systemctl status goblin-router --no-pager
```

---

## Verification Tests

### Test 1: TCP Connectivity

**From Router Server**:

```bash
ssh root@45.61.51.220
timeout 5 bash -c 'echo > /dev/tcp/192.175.23.150/8002' && echo "✅ Port open" || echo "❌ Port closed"
```

**Expected**: `✅ Port open`

### Test 2: Health Endpoint

**From Router Server**:

```bash
ssh root@45.61.51.220
curl http://192.175.23.150:8002/health -H 'X-API-Key: 206e61fdeda2267c9a4ecac3997c4eae7ebd20038282445f7524a84a78ac0158'
```

**Expected**: JSON response with healthy status

### Test 3: Chat Completion

**Test the full chat flow**:

```bash
curl -X POST http://45.61.51.220:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: cef5587890c73a5316a9a2c4ed851d97beb89fd28443885aad6e570dabd5f765' \
  -d '{
    "model": "llama2:7b",
    "messages": [{"role": "user", "content": "Say hello"}],
    "temperature": 0.7
  }'
```

**Expected**: Chat completion response with content, NOT `{"detail":"All servers unavailable"}`

### Test 4: Frontend Chat

1. Open https://goblin.fuaad.ai
2. Send test message
3. Verify response from LLM (not error)

---

## Monitoring

### Check Router Logs

```bash
ssh root@45.61.51.220
sudo journalctl -u goblin-router -f
```

**Look for**:

- `Inference health check failed` = still broken
- `FAILOVER DEACTIVATED` = health check now passes ✅

### Check Inference Logs

```bash
ssh root@192.175.23.150
sudo journalctl -u local-llm-proxy -f
```

---

## Automated Fix Script

Both scripts are provided in the repository:

1. **`kamatera_infrastructure_fix.sh`** - Automated SSH-based fix (recommended)
2. **`kamatera_manual_fix_guide.sh`** - Step-by-step manual instructions

---

## Expected Results After Fix

### Before Fix (Broken)

```
User Frontend sends message
  ↓
Router receives request
  ↓
Router tries health check on 172.16.0.1:8002
  ↓
Connection fails (firewall + wrong IP)
  ↓
Failover mode activated
  ↓
Message: "All servers unavailable"
```

### After Fix (Working)

```
User Frontend sends message
  ↓
Router receives request
  ↓
Router tries health check on 192.175.23.150:8002
  ↓
Connection succeeds (firewall allowed + correct IP)
  ↓
Routes to Inference Server
  ↓
LLM generates response
  ↓
Response sent to user
```

---

## Rollback Instructions

If something goes wrong:

```bash
# On Inference Server
ssh root@192.175.23.150
sudo ufw delete allow from 45.61.51.220 to any port 8002

# On Router Server
ssh root@45.61.51.220
sudo ufw delete allow out to 192.175.23.150 port 8002
sudo systemctl restart goblin-router
```

---

## Document Version

**Last Updated**: January 6, 2026  
**Status**: Ready for Implementation  
**Affected Servers**:

- Router: 45.61.51.220:8000
- Inference: 192.175.23.150:8002
