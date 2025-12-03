# Goblin Assistant Infrastructure - Deployment Checklist

## 🚨 Current Status: Subdomain Setup

**Action Required**: Get a new Cloudflare API token to proceed with DNS setup.

### Quick Options

**Option 1: Get New API Token (Recommended)**
1. Open: https://dash.cloudflare.com/profile/api-tokens
2. Create token with **Zone.DNS (Edit)** permission for `fuaad.ai`
3. Update `.env` file: `CF_API_TOKEN=your-new-token`
4. Run: `./setup_subdomains.sh`

**Option 2: Manual DNS Setup (Backup)**
1. Open: https://dash.cloudflare.com/a9c52e892f7361bab3bfd084c6ffaccb
2. Select `fuaad.ai` zone → DNS → Add records manually
3. See [GET_API_TOKEN.md](./GET_API_TOKEN.md) for record details

### Target Mapping Reference

| Subdomain | Target | Purpose |
|-----------|--------|---------|
| `goblin.fuaad.ai` | `goblin-assistant.fly.dev` (temporary) | Frontend |
| `api.goblin.fuaad.ai` | `goblin-assistant.fly.dev` | Backend API |
| `brain.goblin.fuaad.ai` | `goblin-assistant-edge.fuaadabdullah.workers.dev` | LLM Gateway |
| `ops.goblin.fuaad.ai` | `9c780bd1-ac63-4d6c-afb1-787a2867e5dd.cfargotunnel.com` | Admin Panel |

All records should be:
- Type: `CNAME`
- Proxied: ✅ Yes (orange cloud)
- TTL: Auto

**Files Updated**:
- ✅ `wrangler.toml` - Production subdomain URLs configured
- ✅ `SUBDOMAIN_SETUP_ANSWERS.md` - Quick answers for script
- ✅ `GET_API_TOKEN.md` - Token creation + manual setup guide
- ✅ `DEPLOYMENT_TARGETS.md` - Complete deployment reference

---

## Pre-Deployment Checks

### Prerequisites
- [ ] Cloudflare account configured with `fuaad.ai` domain
- [ ] Cloudflare API token with **Zone.DNS (Edit)** permissions
- [ ] `curl` and `jq` installed (`brew install curl jq`)
- [ ] `wrangler` CLI installed (`npm install -g wrangler`)
- [ ] `cloudflared` installed (`brew install cloudflared`)
- [ ] Wrangler authenticated (`wrangler login`)

### Infrastructure Resources
- [ ] Worker: `goblin-assistant-edge` exists
- [ ] KV Namespace: `9e1c27d3eda84c759383cb2ac0b15e4c` exists
- [ ] D1 Database: `goblin-assistant-db` (`8af5cf0e-f749-47ab-b7ad-22daa135fb75`) exists
- [ ] Cloudflare Tunnel: `9c780bd1-ac63-4d6c-afb1-787a2867e5dd` configured
- [ ] Zero Trust Access Group: "Goblin Admins" (`1eac441b-55ad-4be9-9259-573675e2d993`) created
- [ ] Turnstile Widgets: Managed (`0x4AAAAAACEUKA3R8flZ2Ig0`) + Invisible (`0x4AAAAAACEUKak3TnCntrFv`) created

---

## Phase 1: Subdomain Setup (5 minutes)

### 1.1 Run Automated Script
```bash
cd goblin-infra/projects/goblin-assistant/infra/cloudflare
./setup_subdomains.sh
```

- [ ] API token verified
- [ ] Domain `fuaad.ai` selected
- [ ] Frontend target provided (Vercel CNAME or IP)
- [ ] Backend target provided (Railway CNAME or IP)
- [ ] Brain target confirmed (default Worker URL)
- [ ] Ops target provided (Tunnel CNAME or IP)
- [ ] All 4 DNS records created

### 1.2 Verify DNS Records
```bash
dig goblin.fuaad.ai
dig api.goblin.fuaad.ai
dig brain.goblin.fuaad.ai
dig ops.goblin.fuaad.ai
```

- [ ] `goblin.fuaad.ai` resolves
- [ ] `api.goblin.fuaad.ai` resolves
- [ ] `brain.goblin.fuaad.ai` resolves
- [ ] `ops.goblin.fuaad.ai` resolves

### 1.3 Verify SSL Certificates (15-30 min wait)
```bash
curl -I https://goblin.fuaad.ai
curl -I https://api.goblin.fuaad.ai
curl -I https://brain.goblin.fuaad.ai
curl -I https://ops.goblin.fuaad.ai
```

- [ ] All subdomains return valid SSL certificates
- [ ] No certificate errors

---

## Phase 2: Model Gateway Setup (10 minutes)

### 2.1 Configure Model Endpoints

Edit `wrangler.toml`:
```toml
[vars]
# Local models (free)
OLLAMA_ENDPOINT = "http://localhost:11434"
LLAMACPP_ENDPOINT = "http://localhost:8080"

# Remote models (paid)
KAMATERA_ENDPOINT = "https://your-kamatera-server.com"
OPENAI_ENDPOINT = "https://api.openai.com/v1"
ANTHROPIC_ENDPOINT = "https://api.anthropic.com/v1"
GROQ_ENDPOINT = "https://api.groq.com/openai/v1"

# Subdomain URLs
API_URL = "https://api.goblin.fuaad.ai"
FRONTEND_URL = "https://goblin.fuaad.ai"
OPS_URL = "https://ops.goblin.fuaad.ai"
```

- [ ] All endpoint URLs updated
- [ ] Subdomain URLs configured

### 2.2 Set API Keys
```bash
wrangler secret put OPENAI_API_KEY
wrangler secret put ANTHROPIC_API_KEY
wrangler secret put GROQ_API_KEY
wrangler secret put KAMATERA_AUTH_TOKEN
```

- [ ] OpenAI API key set
- [ ] Anthropic API key set
- [ ] Groq API key set
- [ ] Kamatera auth token set

### 2.3 Deploy Model Gateway
```bash
./setup_model_gateway.sh
```

- [ ] Existing worker backed up
- [ ] D1 schema deployed (inference_logs, provider_health tables)
- [ ] Worker configuration validated
- [ ] Worker deployed successfully
- [ ] Health endpoint returns `{"status": "healthy", "model_gateway": true}`

### 2.4 Verify Model Gateway
```bash
# Check health
curl https://brain.goblin.fuaad.ai/health | jq

# Test local-first routing
curl -X POST https://brain.goblin.fuaad.ai/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-token" \
  -d '{
    "model": "local/llama3.2:latest",
    "messages": [{"role": "user", "content": "Hello!"}],
    "strategy": "local-first"
  }' | jq
```

- [ ] Health endpoint responds
- [ ] Chat completion works
- [ ] Routing uses local model first
- [ ] Fallback to cloud works if local unavailable

---

## Phase 3: Application Configuration (5 minutes)

### 3.1 Frontend Environment Variables

Create/update `apps/goblin-assistant/.env.production`:
```env
VITE_API_URL=https://api.goblin.fuaad.ai
VITE_BRAIN_URL=https://brain.goblin.fuaad.ai
VITE_TURNSTILE_SITE_KEY=0x4AAAAAACEUKA3R8flZ2Ig0
VITE_TURNSTILE_INVISIBLE_KEY=0x4AAAAAACEUKak3TnCntrFv
```

- [ ] API URL updated
- [ ] Brain URL updated
- [ ] Turnstile keys present

### 3.2 Backend Environment Variables

Update backend environment (Railway, .env, etc.):
```env
FRONTEND_URL=https://goblin.fuaad.ai
CORS_ORIGINS=https://goblin.fuaad.ai,https://api.goblin.fuaad.ai,https://ops.goblin.fuaad.ai
DATABASE_URL=your-db-connection-string
SECRET_KEY=your-secret-key
```

- [ ] Frontend URL updated
- [ ] CORS origins updated with all subdomains

### 3.3 FastAPI CORS Configuration

Update `backend/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://goblin.fuaad.ai",
        "https://api.goblin.fuaad.ai",
        "https://ops.goblin.fuaad.ai",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

- [ ] All subdomains in CORS allow_origins
- [ ] Credentials enabled

---

## Phase 4: Application Deployment (10 minutes)

### 4.1 Deploy Frontend
```bash
# If using Vercel
cd apps/goblin-assistant
vercel --prod

# If using Netlify
netlify deploy --prod
```

- [ ] Frontend built successfully
- [ ] Frontend deployed to production
- [ ] Custom domain `goblin.fuaad.ai` configured

### 4.2 Deploy Backend
```bash
# If using Railway
railway up

# If using Docker on VPS
docker-compose up -d --build
```

- [ ] Backend built successfully
- [ ] Backend deployed
- [ ] Custom domain `api.goblin.fuaad.ai` configured

### 4.3 Deploy Worker
```bash
cd goblin-infra/projects/goblin-assistant/infra/cloudflare
wrangler deploy
```

- [ ] Worker deployed
- [ ] Custom domain `brain.goblin.fuaad.ai` configured

---

## Phase 5: Testing (10 minutes)

### 5.1 Test Frontend
```bash
curl -I https://goblin.fuaad.ai
```

- [ ] Frontend returns 200 OK
- [ ] SSL certificate valid
- [ ] Page loads in browser

### 5.2 Test Backend API
```bash
curl https://api.goblin.fuaad.ai/health | jq
```

- [ ] API returns health status
- [ ] No CORS errors

### 5.3 Test Brain (Inference Gateway)
```bash
curl https://brain.goblin.fuaad.ai/health | jq
```

- [ ] Brain returns health status
- [ ] Model gateway active

### 5.4 Test Turnstile Integration

1. Open browser to `https://goblin.fuaad.ai/login`
2. Try to submit login form

- [ ] Turnstile widget appears
- [ ] Challenge completes
- [ ] Token sent to backend
- [ ] Login succeeds

### 5.5 Test Chat with Model Gateway

1. Open chat page: `https://goblin.fuaad.ai/chat`
2. Send a message

- [ ] Invisible Turnstile token generated
- [ ] Message sent to `brain.goblin.fuaad.ai`
- [ ] Model gateway routes to appropriate provider
- [ ] Response received and displayed

### 5.6 Test Model Gateway Routing

```bash
# Test cost-optimized (should use Ollama/llama.cpp)
curl -X POST https://brain.goblin.fuaad.ai/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "local/llama3.2:latest", "messages": [{"role": "user", "content": "Hi"}], "strategy": "cost-optimized"}' | jq

# Test quality-optimized (should use Claude/GPT-4)
curl -X POST https://brain.goblin.fuaad.ai/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4", "messages": [{"role": "user", "content": "Hi"}], "strategy": "quality-optimized"}' | jq
```

- [ ] Cost-optimized uses local models
- [ ] Quality-optimized uses cloud models
- [ ] Failover works if provider unavailable

---

## Phase 6: Zero Trust Setup (10 minutes)

### 6.1 Create Access Application

1. Go to: https://one.dash.cloudflare.com/
2. Navigate to: **Access → Applications → Add an application**
3. Configure:
   - **Type**: Self-hosted
   - **Name**: `Goblin Assistant Ops`
   - **Domain**: `ops.goblin.fuaad.ai`
   - **Session Duration**: 24 hours
   - **Policy Name**: `Allow Goblin Admins`
   - **Action**: Allow
   - **Include**: `Goblin Admins` group (ID: `1eac441b-55ad-4be9-9259-573675e2d993`)

- [ ] Access Application created
- [ ] Domain configured
- [ ] Policy attached

### 6.2 Test Zero Trust Access
```bash
# Should redirect to Cloudflare login
curl -I https://ops.goblin.fuaad.ai
```

- [ ] Returns 302 redirect to Cloudflare Access
- [ ] Login with authorized email works
- [ ] Unauthorized users blocked

---

## Phase 7: Monitoring & Optimization (Ongoing)

### 7.1 Check D1 Logs

```bash
# Check inference logs
wrangler d1 execute goblin-assistant-db --remote --command \
  "SELECT provider, model, strategy, cost_usd, latency_ms, created_at
   FROM inference_logs
   ORDER BY created_at DESC
   LIMIT 10"

# Check provider health
wrangler d1 execute goblin-assistant-db --remote --command \
  "SELECT * FROM provider_health ORDER BY last_checked DESC"
```

- [ ] Inference logs populating
- [ ] Cost tracking working
- [ ] Provider health monitored

### 7.2 Monitor Cost Savings

```bash
# Daily inference cost
wrangler d1 execute goblin-assistant-db --remote --command \
  "SELECT DATE(created_at) as date,
          SUM(cost_usd) as total_cost,
          COUNT(*) as requests
   FROM inference_logs
   WHERE created_at >= DATE('now', '-7 days')
   GROUP BY date"
```

- [ ] Track daily costs
- [ ] Compare to previous costs without gateway
- [ ] Calculate actual savings

### 7.3 Check Turnstile Analytics

1. Go to: https://dash.cloudflare.com/a9c52e892f7361bab3bfd084c6ffaccb/turnstile
2. View analytics for both widgets

- [ ] Bot block rate visible
- [ ] Challenge solve rate healthy (>90%)
- [ ] Cost savings from blocked bots

### 7.4 Monitor Worker Logs

```bash
wrangler tail goblin-assistant-edge
```

- [ ] Rate limiting working
- [ ] Turnstile validation succeeding
- [ ] Model gateway routing correctly
- [ ] No excessive errors

---

## Success Metrics

### Cost Savings
- [ ] Turnstile blocks 60-80% bot traffic → ~$70/day savings
- [ ] Model gateway uses local models for 95% requests → $150-300/month savings
- [ ] **Total**: $2,250-2,400/month saved

### Performance
- [ ] Average latency: <500ms (improved 20-40% with local-first routing)
- [ ] Availability: >99.9% (with automatic failover)
- [ ] Cache hit rate: >70% (5-minute cache)

### Security
- [ ] Bot traffic blocked at edge (before LLM calls)
- [ ] Rate limiting prevents abuse (100 req/60s)
- [ ] Zero Trust protects admin panel
- [ ] All traffic over HTTPS (Full strict mode)

---

## Rollback Plan

### If Something Goes Wrong

**Rollback Worker**:
```bash
cd goblin-infra/projects/goblin-assistant/infra/cloudflare
cp worker.js.backup worker.js
wrangler deploy
```

**Rollback DNS**:
```bash
# Delete custom domains in Cloudflare Dashboard
# Workers & Pages → goblin-assistant-edge → Settings → Triggers
```

**Rollback Application Configs**:
```bash
# Revert .env.production to old URLs
git checkout HEAD~1 -- apps/goblin-assistant/.env.production
```

---

## Post-Deployment

### Documentation
- [ ] Update team wiki with new subdomain URLs
- [ ] Document model gateway routing strategies
- [ ] Share Turnstile dashboard access
- [ ] Create runbook for common issues

### Monitoring
- [ ] Set up alerts for Worker errors
- [ ] Monitor D1 database size
- [ ] Track cost savings weekly
- [ ] Review provider health daily

### Optimization
- [ ] Tune routing strategies based on usage
- [ ] Adjust rate limits if needed
- [ ] Add more models as needed
- [ ] Optimize cache TTLs

---

## 🎉 Deployment Complete!

**Infrastructure Version**: v1.2.0
**Deployment Date**: _______________
**Deployed By**: _______________

### Final Verification Checklist
- [ ] All 4 subdomains accessible (goblin, api.goblin, brain.goblin, ops.goblin)
- [ ] SSL certificates valid on all subdomains
- [ ] Turnstile working on login + chat
- [ ] Model gateway routing intelligently
- [ ] Zero Trust protecting ops panel
- [ ] Monitoring dashboards configured
- [ ] Cost savings tracking active

**Status**: ✅ PRODUCTION READY

---

**Last Updated**: December 1, 2025
**Next Review**: 1 week after deployment
