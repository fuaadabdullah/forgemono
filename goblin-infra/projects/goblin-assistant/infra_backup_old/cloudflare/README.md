# Cloudflare Infrastructure for Goblin Assistant

This directory contains the complete Cloudflare edge infrastructure for Goblin Assistant. All services sit behind Cloudflare for DDoS protection, caching, bot filtering, and faster global routing.

## 🎯 Overview

Your Goblin Assistant uses Cloudflare's edge network to:
- **Protect**: DDoS protection, **Turnstile bot verification**, rate limiting
- **Accelerate**: Global caching, edge compute, reduced latency
- **Scale**: Serverless compute, distributed storage, zero backend load
- **Secure**: Zero Trust access, tunnel-based connections

**💰 Cost Savings**: Turnstile blocks bot traffic before hitting your LLM, saving ~$70/day ($2,100/month) in wasted inference costs.

## 📁 Files

### Core Infrastructure
- `worker.js` - Edge logic (rate limiting, sanitization, caching, analytics)
- `worker_with_turnstile.js` - Enhanced worker with Turnstile bot protection
- `worker_with_model_gateway.js` - Intelligent LLM routing with failover (v1.2.0)
- `wrangler.toml` - Worker configuration and bindings
- `schema.sql` - D1 database schema for structured data
- `schema_model_gateway.sql` - Model gateway database schema (inference logs, health monitoring)
- `durable-object.js` - Real-time state management (WebSockets, chat rooms)
- `.env` - Environment variables and API tokens

### Setup Scripts
- `setup_proxy.sh` - DNS configuration script
- `setup_zerotrust.sh` - Zero Trust Access setup script
- `setup_tunnel.sh` - Cloudflare Tunnel setup (Area 51 mode)
- `setup_turnstile.sh` - Cloudflare Turnstile bot protection setup
- `setup_model_gateway.sh` - Model gateway deployment automation
- `setup_subdomains.sh` - **NEW** Automated subdomain DNS configuration
- `test_worker.sh` - Automated testing script

### Documentation
- `README.md` - This file (infrastructure overview)
- `TURNSTILE_INTEGRATION.md` - Complete Turnstile integration guide
- `TURNSTILE_QUICK_START.md` - Quick reference for Turnstile testing
- `FRONTEND_INTEGRATION_COMPLETE.md` - Frontend Turnstile integration guide
- `MODEL_GATEWAY_SETUP.md` - Model gateway architecture and configuration
- `SUBDOMAIN_SETUP.md` - Subdomain DNS configuration guide
- `SUBDOMAIN_QUICK_START.md` - **NEW** 5-minute subdomain setup guide
- `MEMORY_SHARDS.md` - Documentation for KV/D1 storage patterns

## 🚀 Quick Start

### 1. Prerequisites

Install dependencies:
```bash
npm install -g wrangler
brew install cloudflared
```

### 2. Configure Tokens

Update `.env` with your Cloudflare API tokens:
```bash
CF_ACCOUNT_ID="your-account-id"
CF_API_TOKEN_WORKERS="token-with-workers-and-d1-permissions"
CF_API_TOKEN_ACCESS="token-with-tunnel-and-access-permissions"
CF_API_TOKEN_DNS="token-with-dns-permissions"
```

### 3. Deploy Infrastructure

**Option A: Automated Subdomain Setup (Recommended)**
```bash
# Set up production subdomains (goblin.fuaad.ai, api.goblin.fuaad.ai, etc.)
./setup_subdomains.sh
```
See [SUBDOMAIN_QUICK_START.md](./SUBDOMAIN_QUICK_START.md) for complete guide.

**Option B: Manual Deployment**
```bash
# Deploy Worker (KV + D1 already configured)
wrangler deploy

# Start Tunnel (Area 51 mode - optional)
cloudflared tunnel --config tunnel-config.yml run
```

### 4. Deploy Model Gateway (Optional)

For intelligent LLM routing across multiple providers:
```bash
./setup_model_gateway.sh
```
See [MODEL_GATEWAY_SETUP.md](./MODEL_GATEWAY_SETUP.md) for complete guide.

## 🌐 Subdomain Architecture (Production)

**NEW**: Clean subdomain structure for production deployment:

- `goblin.fuaad.ai` - Frontend application
- `api.goblin.fuaad.ai` - Backend API
- `brain.goblin.fuaad.ai` - LLM inference gateway (Worker)
- `ops.goblin.fuaad.ai` - Admin panel (Zero Trust protected)

**Quick Setup**:
```bash
./setup_subdomains.sh
```

**Benefits**:
- ✅ Professional URLs for each service
- ✅ Proper CORS with same parent domain
- ✅ Zero Trust security for admin access
- ✅ Independent scaling per service
- ✅ Optimized Cloudflare edge features per subdomain

**Documentation**: [SUBDOMAIN_SETUP.md](./SUBDOMAIN_SETUP.md) | [SUBDOMAIN_QUICK_START.md](./SUBDOMAIN_QUICK_START.md)

## 🧠 Architecture

### Edge Workers (Serverless Goblins)

**URL**: https://goblin-assistant-edge.fuaadabdullah.workers.dev

**What They Do**:
1. **Rate Limiting** - 100 requests/60s per IP (KV-backed)
2. **Prompt Sanitization** - Block jailbreaks, injection attempts
3. **Session Validation** - Edge-level auth (no backend hit)
4. **Response Caching** - 5min cache for GET endpoints
5. **Analytics** - Log all requests asynchronously
6. **Feature Flags** - Dynamic feature toggles

### Storage (Memory Shards)

#### KV (Key-Value Store)
- **Binding**: `GOBLIN_CACHE`
- **ID**: `9e1c27d3eda84c759383cb2ac0b15e4c`
- **Use Cases**: Rate limits, sessions, cache, analytics

#### D1 (SQLite at Edge)
- **Binding**: `DB`
- **Database**: `goblin-assistant-db`
- **ID**: `8af5cf0e-f749-47ab-b7ad-22daa135fb75`
- **Tables**: user_preferences, audit_logs, feature_flags, sessions, api_usage

### Tunnel (Area 51 Mode)

- **Tunnel ID**: `9c780bd1-ac63-4d6c-afb1-787a2867e5dd`
- **Config**: `tunnel-config.yml`
- **Credentials**: `goblin-tunnel-creds.json`
- **Purpose**: Secure backend access without public ports

### Zero Trust Access (Identity Shield)

- **Access Group**: "Goblin Admins"
- **Group ID**: `1eac441b-55ad-4be9-9259-573675e2d993`
- **Members**: Fuaadabdullah@gmail.com
- **Purpose**: Identity-based access control for admin endpoints
- **Status**: Group created, applications require domain

## 📊 Current Deployment Status

✅ **Worker Deployed**: https://goblin-assistant-edge.fuaadabdullah.workers.dev
✅ **KV Namespace Created**: 9e1c27d3eda84c759383cb2ac0b15e4c
✅ **D1 Database Created**: 8af5cf0e-f749-47ab-b7ad-22daa135fb75
✅ **Tunnel Created**: 9c780bd1-ac63-4d6c-afb1-787a2867e5dd
✅ **Zero Trust Group Created**: 1eac441b-55ad-4be9-9259-573675e2d993
⚠️ **DNS Proxy**: Requires domain and Zone ID
⚠️ **Access Applications**: Requires domain for protected endpoints

## 🔧 Common Operations

### Deploy Worker Updates

```bash
wrangler deploy
```

### Query D1 Database

```bash
# Local
wrangler d1 execute goblin-assistant-db --command "SELECT * FROM feature_flags"

# Remote
wrangler d1 execute goblin-assistant-db --remote --command "SELECT * FROM feature_flags"
```

### View KV Data

```bash
# List keys
wrangler kv key list --namespace-id=9e1c27d3eda84c759383cb2ac0b15e4c

# Get value
wrangler kv key get "feature_flags" --namespace-id=9e1c27d3eda84c759383cb2ac0b15e4c
```

### Update Feature Flags

```bash
wrangler d1 execute goblin-assistant-db --remote --command \
  "UPDATE feature_flags SET enabled=1, rollout_percentage=50 WHERE flag_name='new_ui_enabled'"
```

### Start Tunnel

```bash
cloudflared tunnel --config tunnel-config.yml run
```

### View Logs

```bash
wrangler tail
```

## 🔒 Security Features

### Rate Limiting
- IP-based: 100 requests per 60 seconds
- Returns `429` with `Retry-After` header
- Tracked in KV (key: `ratelimit:{ip}`)

### Prompt Sanitization
Blocks patterns:
- System prompt injection
- "Ignore previous instructions" jailbreaks
- API keys/secrets in prompts
- Returns `400` for blocked requests

### Session Validation
- Edge-level token validation
- Expired sessions rejected immediately
- No backend processing for invalid sessions

### Security Event Logging
- All blocked requests logged
- 7-day retention in KV
- Key pattern: `security:{timestamp}:{ip}`

## 📈 Monitoring

### Headers to Check

Every response includes:
- `X-Goblin-Edge: active` - Confirms edge processing
- `X-Response-Time: Xms` - Request duration
- `X-Cache: HIT/MISS` - Cache status
- `X-RateLimit-Limit` - Rate limit maximum
- `X-RateLimit-Remaining` - Remaining requests

### Analytics Data

Stored in KV (24h retention):
```json
{
  "timestamp": "2025-12-02T...",
  "ip": "1.2.3.4",
  "method": "POST",
  "path": "/chat",
  "event_type": "request_complete",
  "duration_ms": 150,
  "user_agent": "..."
}
```

## 🎛️ Configuration

### Environment Variables (wrangler.toml)

```toml
[vars]
API_URL = "https://api.yourdomain.com"
FRONTEND_URL = "https://app.yourdomain.com"
```

### Feature Flags (D1)

Query current flags:
```bash
wrangler d1 execute goblin-assistant-db --remote \
  --command "SELECT * FROM feature_flags"
```

Available flags:
- `api_enabled` - Main API toggle
- `rate_limiting_enabled` - Rate limit enforcement
- `new_ui_enabled` - New UI rollout (with percentage)
- `experimental_features` - Experimental features toggle

## 🐛 Troubleshooting

### Worker not updating?
```bash
# Force deploy
wrangler deploy --force
```

### D1 queries failing?
```bash
# Check connection
wrangler d1 execute goblin-assistant-db --remote --command "SELECT 1"

# Verify schema
wrangler d1 execute goblin-assistant-db --remote \
  --command "SELECT name FROM sqlite_master WHERE type='table'"
```

### Tunnel not connecting?
```bash
# Check tunnel status
cloudflared tunnel info 9c780bd1-ac63-4d6c-afb1-787a2867e5dd

# Test credentials
cloudflared tunnel --config tunnel-config.yml run
```

### Token permissions?
Visit: https://dash.cloudflare.com/profile/api-tokens

Required permissions:
- **Workers**: `Account > Workers Scripts > Edit`
- **D1**: `Account > D1 > Edit`
- **KV**: `Account > Workers KV Storage > Edit`
- **Tunnel**: `Account > Cloudflare Tunnel > Edit`
- **Access**: `Account > Access: Apps and Policies > Edit`
- **DNS**: `Zone > DNS > Edit`

## 📚 Additional Documentation

- `MEMORY_SHARDS.md` - Detailed KV/D1 storage patterns
- `README_SETUP.md` - Initial setup instructions
- `README_STATUS.md` - Deployment status and results

## 🔗 Useful Links

- [Cloudflare Dashboard](https://dash.cloudflare.com/a9c52e892f7361bab3bfd084c6ffaccb)
- [Worker URL](https://goblin-assistant-edge.fuaadabdullah.workers.dev)
- [API Tokens](https://dash.cloudflare.com/profile/api-tokens)
- [Wrangler Docs](https://developers.cloudflare.com/workers/wrangler/)
- [D1 Docs](https://developers.cloudflare.com/d1/)
- [KV Docs](https://developers.cloudflare.com/kv/)
