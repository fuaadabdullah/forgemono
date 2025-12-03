# Goblin Assistant Subdomain Deployment Guide

## 🎯 Goal
Set up clean production subdomains for Goblin Assistant:
- `goblin.fuaad.ai` → Frontend application
- `api.goblin.fuaad.ai` → Backend API
- `brain.goblin.fuaad.ai` → LLM inference gateway (Cloudflare Worker)
- `ops.goblin.fuaad.ai` → Admin panel (Zero Trust protected)

## 📋 Prerequisites Checklist

- [x] Cloudflare account configured
- [x] `fuaad.ai` domain in Cloudflare
- [x] Cloudflare API token with DNS permissions
- [x] `jq` installed (`/usr/local/bin/jq`)
- [x] `wrangler` installed (latest version)
- [ ] Frontend deployed (Vercel/Netlify/VPS)
- [ ] Backend API deployed (Railway/Render/VPS)
- [ ] Worker deployed (`goblin-assistant-edge.fuaadabdullah.workers.dev`)

## 🚀 Quick Deploy

### Step 1: Run the Setup Script

```bash
cd /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/infra/cloudflare
./setup_subdomains.sh
```

### Step 2: Information You'll Need

When prompted, provide:

#### Frontend Target (`goblin.fuaad.ai`)
**Options:**
- Vercel: `cname.vercel-dns.com` (get from Vercel dashboard)
- Netlify: `your-site.netlify.app`
- VPS: Your server IP (e.g., `123.45.67.89`)
- Railway: `your-app.railway.app`

#### Backend API Target (`api.goblin.fuaad.ai`)
**Options:**
- Railway: `your-backend.railway.app`
- Fly.io: `your-backend.fly.dev` (or the Fly app hostname)
- VPS: Your server IP
- Cloud Run: `your-service-xyz.run.app`

#### Brain Target (`brain.goblin.fuaad.ai`)
**Default:** `goblin-assistant-edge.fuaadabdullah.workers.dev`
- Press Enter to use existing Worker
- Or provide custom Worker URL if you've deployed elsewhere

#### Ops Target (`ops.goblin.fuaad.ai`)
**Options:**
- Cloudflare Tunnel: `9c780bd1-ac63-4d6c-afb1-787a2867e5dd.cfargotunnel.com`
- Same as backend: Use same IP/CNAME as backend
- Separate admin server: Your admin panel IP/URL

## 📦 Deployment Status

### Current Infrastructure
- ✅ Worker: `goblin-assistant-edge.fuaadabdullah.workers.dev`
- ✅ KV Namespace: `9e1c27d3eda84c759383cb2ac0b15e4c`
- ✅ D1 Database: `goblin-assistant-db`
- ✅ Cloudflare Tunnel: `9c780bd1-ac63-4d6c-afb1-787a2867e5dd`
- ✅ Zero Trust Group: `1eac441b-55ad-4be9-9259-573675e2d993` (Goblin Admins)
- ✅ Turnstile Widgets: Managed + Invisible modes configured

### What Needs Deployment
1. **Frontend** - Where is your Goblin Assistant UI hosted?
2. **Backend API** - Where is your FastAPI server running?
3. **Admin Panel** - Do you have a separate ops interface?

## 🔧 Post-Setup Configuration

### 1. Update Frontend Config

Create/update `apps/goblin-assistant/.env.production`:
```env
VITE_API_URL=https://api.goblin.fuaad.ai
VITE_BRAIN_URL=https://brain.goblin.fuaad.ai
VITE_TURNSTILE_SITE_KEY=0x4AAAAAACEUKA3R8flZ2Ig0
VITE_TURNSTILE_INVISIBLE_KEY=0x4AAAAAACEUKak3TnCntrFv
```

### 2. Update Backend Config

Update your backend environment variables:
```env
FRONTEND_URL=https://goblin.fuaad.ai
CORS_ORIGINS=https://goblin.fuaad.ai,https://api.goblin.fuaad.ai,https://ops.goblin.fuaad.ai
API_BASE_URL=https://api.goblin.fuaad.ai
```

### 3. Update Worker Config

Edit `wrangler.toml`:
```toml
[vars]
API_URL = "https://api.goblin.fuaad.ai"
FRONTEND_URL = "https://goblin.fuaad.ai"
OPS_URL = "https://ops.goblin.fuaad.ai"
```

Then redeploy:
```bash
wrangler deploy
```

### 4. Add Custom Domain to Worker (Important!)

The script creates DNS records, but you also need to bind the custom domain to your Worker:

**Option A: Cloudflare Dashboard**
1. Go to Workers & Pages → `goblin-assistant-edge` → Settings → Triggers
2. Click "Add Custom Domain"
3. Enter: `brain.goblin.fuaad.ai`
4. Click "Add Custom Domain"

**Option B: Command Line**
```bash
wrangler domains add brain.goblin.fuaad.ai
```

### 5. Configure CORS in Backend

If using FastAPI (`apps/goblin-assistant/backend/main.py`):
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://goblin.fuaad.ai",
        "https://api.goblin.fuaad.ai",
        "https://brain.goblin.fuaad.ai",
        "https://ops.goblin.fuaad.ai",
        "http://localhost:3000",  # Keep for local dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🧪 Testing

### 1. Test DNS Propagation
```bash
# Check if DNS is resolving
dig goblin.fuaad.ai
dig api.goblin.fuaad.ai
dig brain.goblin.fuaad.ai
dig ops.goblin.fuaad.ai

# Check via Cloudflare DNS
dig @1.1.1.1 goblin.fuaad.ai
```

### 2. Test SSL Certificates
```bash
# Frontend
curl -I https://goblin.fuaad.ai

# Backend
curl -I https://api.goblin.fuaad.ai

# Brain
curl -I https://brain.goblin.fuaad.ai

# Ops
curl -I https://ops.goblin.fuaad.ai
```

### 3. Test API Endpoints
```bash
# Health check (backend)
curl https://api.goblin.fuaad.ai/health | jq

# Health check (worker)
curl https://brain.goblin.fuaad.ai/health | jq

# Test chat endpoint with Turnstile
curl -X POST https://brain.goblin.fuaad.ai/api/chat \
  -H "Content-Type: application/json" \
  -H "CF-Turnstile-Token: test-token" \
  -d '{"message": "Hello Goblin!", "conversation_id": "test-123"}'
```

### 4. Test CORS
```bash
curl -X OPTIONS https://api.goblin.fuaad.ai/health \
  -H "Origin: https://goblin.fuaad.ai" \
  -H "Access-Control-Request-Method: POST" \
  -v
```

## 🔐 Zero Trust Setup (Optional)

Protect your admin panel behind Cloudflare Access:

### 1. Create Access Application
```bash
# Go to Zero Trust dashboard
open https://one.dash.cloudflare.com/
```

### 2. Configure Application
- **Name:** `Goblin Assistant Ops`
- **Domain:** `ops.goblin.fuaad.ai`
- **Session Duration:** 24 hours
- **Policies:**
  - Policy Name: "Goblin Admins Only"
  - Action: Allow
  - Include: `Goblin Admins` group (ID: `1eac441b-55ad-4be9-9259-573675e2d993`)

### 3. Test Zero Trust
```bash
# Should redirect to Cloudflare login
curl -I https://ops.goblin.fuaad.ai

# Should return 302 redirect
# HTTP/2 302
# location: https://fuaadabdullah.cloudflareaccess.com/...
```

## 📊 Monitoring

### Check Cloudflare Analytics
```bash
# Open Cloudflare dashboard
open https://dash.cloudflare.com/a9c52e892f7361bab3bfd084c6ffaccb

# Check DNS records
open https://dash.cloudflare.com/a9c52e892f7361bab3bfd084c6ffaccb/zones/
```

### Check Worker Analytics
```bash
# View real-time logs
wrangler tail

# View metrics in dashboard
open https://dash.cloudflare.com/a9c52e892f7361bab3bfd084c6ffaccb/workers/services/view/goblin-assistant-edge/production/analytics
```

### Check Turnstile Analytics
```bash
# View bot protection stats
open https://dash.cloudflare.com/a9c52e892f7361bab3bfd084c6ffaccb/turnstile
```

## 🐛 Troubleshooting

### DNS Not Resolving
**Problem:** `dig goblin.fuaad.ai` returns no results

**Solution:**
1. Check DNS records exist in Cloudflare dashboard
2. Wait 5-30 minutes for DNS propagation
3. Clear DNS cache: `sudo dscacheutil -flushcache`
4. Try Cloudflare's DNS: `dig @1.1.1.1 goblin.fuaad.ai`

### SSL Certificate Error
**Problem:** `curl: (60) SSL certificate problem`

**Solution:**
1. SSL certs provision automatically within 15-30 minutes
2. Check Cloudflare SSL mode is "Full" or "Full (strict)"
3. Ensure origin server has valid SSL cert

### CORS Errors in Browser
**Problem:** `Access-Control-Allow-Origin` error in console

**Solution:**
1. Add all subdomains to backend CORS config
2. Ensure credentials allowed: `allow_credentials=True`
3. Check preflight OPTIONS requests work

### Worker Not Accessible via Custom Domain
**Problem:** `brain.goblin.fuaad.ai` returns 404

**Solution:**
1. Add custom domain to Worker in Cloudflare dashboard
2. Or use: `wrangler domains add brain.goblin.fuaad.ai`
3. Wait 5 minutes for binding to propagate

### Ops Panel Not Protected
**Problem:** `ops.goblin.fuaad.ai` accessible without login

**Solution:**
1. Create Access Application in Zero Trust dashboard
2. Add policy requiring "Goblin Admins" group
3. Ensure DNS record is proxied (orange cloud)

## 📚 Reference

### Cloudflare Resources
- **Account Dashboard:** https://dash.cloudflare.com/a9c52e892f7361bab3bfd084c6ffaccb
- **Workers Dashboard:** https://dash.cloudflare.com/a9c52e892f7361bab3bfd084c6ffaccb/workers
- **Zero Trust Dashboard:** https://one.dash.cloudflare.com/
- **Turnstile Dashboard:** https://dash.cloudflare.com/a9c52e892f7361bab3bfd084c6ffaccb/turnstile
- **API Tokens:** https://dash.cloudflare.com/profile/api-tokens

### Documentation Files
- **README.md** - Complete Cloudflare infrastructure overview
- **SUBDOMAIN_SETUP.md** - Detailed manual setup instructions
- **SUBDOMAIN_QUICK_START.md** - Quick automated setup guide
- **TURNSTILE_INTEGRATION.md** - Complete Turnstile bot protection guide
- **MODEL_GATEWAY_SETUP.md** - LLM routing and failover setup

### GoblinOS Integration
Update `.github/copilot-instructions.md` with new URLs:
```markdown
#### Cloudflare Edge (goblin-assistant)

Production URLs:
- Frontend: https://goblin.fuaad.ai
- Backend API: https://api.goblin.fuaad.ai
- Brain (LLM Gateway): https://brain.goblin.fuaad.ai
- Ops (Admin): https://ops.goblin.fuaad.ai (Zero Trust protected)
```

## ✅ Deployment Checklist

- [ ] Run `./setup_subdomains.sh`
- [ ] DNS records created for all 4 subdomains
- [ ] Wait for DNS propagation (5-30 min)
- [ ] Add custom domain to Worker (`brain.goblin.fuaad.ai`)
- [ ] Update frontend `.env.production`
- [ ] Update backend CORS config
- [ ] Update Worker `wrangler.toml`
- [ ] Redeploy Worker with new config
- [ ] Test all endpoints with curl
- [ ] Set up Zero Trust for ops panel
- [ ] Update GoblinOS docs with new URLs
- [ ] Monitor Cloudflare analytics
- [ ] Celebrate! 🎉

---

**Ready to deploy? Run `./setup_subdomains.sh` now!** 🚀
