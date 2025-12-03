# Goblin Assistant Subdomain Setup 🌐

**Status**: Configuration Guide
**Date**: December 2, 2025
**Purpose**: Set up clean subdomain structure for Goblin Assistant services

---

## 🎯 Subdomain Architecture

```
goblin.fuaad.ai
├── goblin.fuaad.ai          → Frontend (React app)
├── api.goblin.fuaad.ai      → Backend API (FastAPI)
├── brain.goblin.fuaad.ai    → LLM Inference Gateway (Cloudflare Worker)
└── ops.goblin.fuaad.ai      → Zero Trust Admin Panel
```

### Benefits

- ✅ **Clean separation** of concerns (frontend/backend/inference/admin)
- ✅ **Easy CORS** configuration (same parent domain)
- ✅ **Better security** (separate auth for each service)
- ✅ **Cloudflare optimization** (edge caching, DDoS protection per subdomain)
- ✅ **Professional appearance** for your Goblin Assistant brand

---

## 📋 Prerequisites

1. **Domain**: You own `fuaad.ai` (or will use a different domain)
2. **Cloudflare Account**: Domain is managed by Cloudflare DNS
3. **Cloudflare API Token**: With Zone.DNS permissions
4. **Services Running**:
   - Frontend: React app (port 5173 or deployed)
   - Backend: FastAPI (port 8000 or deployed)
   - Worker: Already deployed at `goblin-assistant-edge.fuaadabdullah.workers.dev`

---

## 🚀 Quick Setup

### Option 1: Automated Setup (Recommended)

```bash
cd apps/goblin-assistant/infra/cloudflare

# Make script executable
chmod +x setup_subdomains.sh

# Run setup wizard
./setup_subdomains.sh
```

The script will:
1. Check your Cloudflare credentials
2. List available zones (domains)
3. Create DNS records for all subdomains
4. Configure SSL/TLS settings
5. Set up page rules for optimization
6. Test DNS propagation

### Option 2: Manual Setup via Cloudflare Dashboard

See section "Manual DNS Configuration" below.

---

## 🔧 Configuration

### 1. Environment Variables

Create or update `/apps/goblin-assistant/infra/cloudflare/.env`:

```bash
# Cloudflare Configuration
CF_API_TOKEN=your_cloudflare_api_token_here
CF_ACCOUNT_ID=a9c52e892f7361bab3bfd084c6ffaccb
CF_ZONE_ID=your_zone_id_here  # Get from Cloudflare dashboard

# Domain Configuration
ROOT_DOMAIN=fuaad.ai
GOBLIN_SUBDOMAIN=goblin.fuaad.ai

# Frontend Configuration
FRONTEND_SUBDOMAIN=goblin.fuaad.ai
FRONTEND_TARGET=your-frontend-deployment.vercel.app  # Or Netlify, etc.
# OR if self-hosted:
FRONTEND_IP=your.server.ip.address

# Backend Configuration
BACKEND_SUBDOMAIN=api.goblin.fuaad.ai
BACKEND_TARGET=your-backend-deployment.railway.app  # Or your server
# OR if self-hosted:
BACKEND_IP=your.server.ip.address

# Inference Gateway Configuration
BRAIN_SUBDOMAIN=brain.goblin.fuaad.ai
BRAIN_TARGET=goblin-assistant-edge.fuaadabdullah.workers.dev

# Admin Panel Configuration
OPS_SUBDOMAIN=ops.goblin.fuaad.ai
OPS_TARGET=your-admin-panel.vercel.app
# OR use Cloudflare Zero Trust tunnel
OPS_TUNNEL_ID=9c780bd1-ac63-4d6c-afb1-787a2867e5dd
```

### 2. Get Your Zone ID

**Via Dashboard**:
1. Go to https://dash.cloudflare.com
2. Select your domain (`fuaad.ai`)
3. Scroll down on Overview page
4. Copy **Zone ID** from the right sidebar

**Via API**:
```bash
curl -X GET "https://api.cloudflare.com/client/v4/zones" \
  -H "Authorization: Bearer YOUR_CF_API_TOKEN" \
  -H "Content-Type: application/json" | jq '.result[] | {name, id}'
```

### 3. DNS Record Types

**For Cloudflare Workers** (brain.goblin.fuaad.ai):
- Type: `CNAME`
- Name: `brain.goblin.fuaad.ai`
- Target: `goblin-assistant-edge.fuaadabdullah.workers.dev`
- Proxied: ✅ Yes (orange cloud)

**For External Services** (Vercel, Netlify, Railway):
- Type: `CNAME`
- Name: `goblin.fuaad.ai` (frontend)
- Target: `cname.vercel-dns.com` (or your platform's CNAME)
- Proxied: ✅ Yes

**For Self-Hosted Services**:
- Type: `A`
- Name: `api.goblin.fuaad.ai`
- Target: Your server IP (e.g., `203.0.113.42`)
- Proxied: ✅ Yes

**For Zero Trust Admin** (ops.goblin.fuaad.ai):
- Type: `CNAME`
- Name: `ops.goblin.fuaad.ai`
- Target: `your-tunnel-id.cfargotunnel.com`
- Proxied: ✅ Yes

---

## 📝 Manual DNS Configuration

### Step 1: Access Cloudflare Dashboard

```bash
open https://dash.cloudflare.com/a9c52e892f7361bab3bfd084c6ffaccb/fuaad.ai/dns/records
```

### Step 2: Create DNS Records

#### Record 1: Frontend (goblin.fuaad.ai)

```
Type: CNAME
Name: goblin
Content: your-frontend.vercel.app  # Or your deployment target
Proxy status: Proxied (orange cloud)
TTL: Auto
```

**If using Vercel**:
1. In Vercel project settings, add domain: `goblin.fuaad.ai`
2. Vercel will provide CNAME target
3. Use that as Content in Cloudflare DNS

**If self-hosted**:
```
Type: A
Name: goblin
Content: YOUR_SERVER_IP
Proxy status: Proxied
TTL: Auto
```

#### Record 2: Backend API (api.goblin.fuaad.ai)

```
Type: CNAME
Name: api.goblin
Content: your-backend.railway.app  # Or your deployment target
Proxy status: Proxied
TTL: Auto
```

**If self-hosted FastAPI**:
```
Type: A
Name: api.goblin
Content: YOUR_SERVER_IP
Proxy status: Proxied
TTL: Auto
```

#### Record 3: Brain/Inference (brain.goblin.fuaad.ai)

```
Type: CNAME
Name: brain.goblin
Content: goblin-assistant-edge.fuaadabdullah.workers.dev
Proxy status: Proxied
TTL: Auto
```

#### Record 4: Ops/Admin (ops.goblin.fuaad.ai)

**Option A: Using Cloudflare Tunnel**
```
Type: CNAME
Name: ops.goblin
Content: 9c780bd1-ac63-4d6c-afb1-787a2867e5dd.cfargotunnel.com
Proxy status: Proxied
TTL: Auto
```

**Option B: Using Zero Trust Access Application**
1. Create Access Application at https://one.dash.cloudflare.com
2. Set subdomain: `ops.goblin.fuaad.ai`
3. Add Goblin Admins group (fuaadabdullah@gmail.com)
4. Point to your admin panel origin

---

## 🔒 SSL/TLS Configuration

### Enable Full (Strict) SSL

1. Go to SSL/TLS → Overview
2. Set encryption mode to **Full (strict)**
3. Enable **Always Use HTTPS**
4. Enable **Automatic HTTPS Rewrites**

### Order SSL Certificates

Cloudflare will automatically provision SSL certificates for:
- `goblin.fuaad.ai`
- `*.goblin.fuaad.ai` (wildcard for all subdomains)

**Check certificate status**:
```bash
curl -I https://goblin.fuaad.ai
curl -I https://api.goblin.fuaad.ai
curl -I https://brain.goblin.fuaad.ai
curl -I https://ops.goblin.fuaad.ai
```

---

## ⚡ Page Rules & Optimization

### Create Page Rules

**Rule 1: Cache Brain Responses**
```
URL: brain.goblin.fuaad.ai/*
Settings:
  - Cache Level: Standard
  - Edge Cache TTL: 5 minutes (for identical prompts)
  - Browser Cache TTL: 1 minute
```

**Rule 2: Always HTTPS**
```
URL: *.goblin.fuaad.ai/*
Settings:
  - Always Use HTTPS: On
```

**Rule 3: Security Headers**
```
URL: goblin.fuaad.ai/*
Settings:
  - Security Level: Medium
  - Browser Integrity Check: On
```

### Enable Cloudflare Features

1. **Speed → Optimization**:
   - ✅ Auto Minify (HTML, CSS, JS)
   - ✅ Brotli compression
   - ✅ Early Hints
   - ✅ Rocket Loader

2. **Caching → Configuration**:
   - ✅ Always Online (keep cached version if origin is down)
   - Cache Level: Standard

3. **Security → Settings**:
   - ✅ Email Address Obfuscation
   - ✅ Hotlink Protection
   - Security Level: Medium

---

## 🔄 Update Application Configuration

### Frontend (.env.production)

```bash
# /apps/goblin-assistant/.env.production

VITE_API_URL=https://api.goblin.fuaad.ai
VITE_BRAIN_URL=https://brain.goblin.fuaad.ai
VITE_APP_URL=https://goblin.fuaad.ai

# Keep existing Turnstile keys
VITE_TURNSTILE_SITE_KEY_MANAGED=0x4AAAAAACEUKA3R8flZ2Ig0
VITE_TURNSTILE_SITE_KEY_INVISIBLE=0x4AAAAAACEUKak3TnCntrFv
```

### Backend (environment variables)

```bash
# Backend deployment platform (Railway/Fly.io/etc.)

FRONTEND_URL=https://goblin.fuaad.ai
CORS_ORIGINS=https://goblin.fuaad.ai,https://api.goblin.fuaad.ai
BRAIN_URL=https://brain.goblin.fuaad.ai

# Database URLs, API keys, etc. (keep existing)
```

### Cloudflare Worker (wrangler.toml)

```toml
# /apps/goblin-assistant/infra/cloudflare/wrangler.toml

[vars]
# Update URLs to use new subdomains
API_URL = "https://api.goblin.fuaad.ai"
FRONTEND_URL = "https://goblin.fuaad.ai"
OPS_URL = "https://ops.goblin.fuaad.ai"

# ... rest of existing config
```

### Update CORS Configuration

**In your FastAPI backend**:

```python
# backend/main.py

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://goblin.fuaad.ai",          # Frontend
        "https://brain.goblin.fuaad.ai",    # Inference gateway
        "https://ops.goblin.fuaad.ai",      # Admin panel
        "http://localhost:5173",            # Local dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 🧪 Testing & Verification

### Test DNS Propagation

```bash
# Check DNS records
dig goblin.fuaad.ai
dig api.goblin.fuaad.ai
dig brain.goblin.fuaad.ai
dig ops.goblin.fuaad.ai

# Or use online tools
open https://www.whatsmydns.net/#CNAME/goblin.fuaad.ai
```

### Test SSL Certificates

```bash
# Check SSL cert is valid
curl -vI https://goblin.fuaad.ai 2>&1 | grep -i "subject:\|issuer:"
curl -vI https://api.goblin.fuaad.ai 2>&1 | grep -i "subject:\|issuer:"
curl -vI https://brain.goblin.fuaad.ai 2>&1 | grep -i "subject:\|issuer:"
```

### Test Endpoints

```bash
# Frontend
curl -I https://goblin.fuaad.ai
# Should return: 200 OK with HTML

# Backend API
curl https://api.goblin.fuaad.ai/health | jq
# Should return: {"status": "healthy"}

# Brain (Inference Gateway)
curl https://brain.goblin.fuaad.ai/health | jq
# Should return: {"status": "healthy", "features": {"model_gateway": true}}

# Ops (should redirect to login if Zero Trust is enabled)
curl -I https://ops.goblin.fuaad.ai
# Should return: 302 Found (redirect to Cloudflare Access login)
```

### Test Full Flow

```bash
# 1. Load frontend
open https://goblin.fuaad.ai

# 2. Check Network tab in DevTools
# - All API calls should go to https://api.goblin.fuaad.ai
# - LLM inference calls should go to https://brain.goblin.fuaad.ai
# - No mixed content warnings

# 3. Try chat functionality
# - Send a message
# - Check it routes through brain.goblin.fuaad.ai
# - Verify Turnstile protection still works

# 4. Access admin panel
open https://ops.goblin.fuaad.ai
# - Should prompt for Cloudflare Access login
# - Login with fuaadabdullah@gmail.com
# - Should grant access (part of Goblin Admins group)
```

---

## 🔐 Zero Trust Setup for Ops Panel

### Step 1: Create Access Group

```bash
open https://one.dash.cloudflare.com/a9c52e892f7361bab3bfd084c6ffaccb/access/groups
```

Create group "Goblin Admins":
- Name: `Goblin Admins`
- Criteria: `Emails` → `fuaadabdullah@gmail.com`
- (Add more admins as needed)

### Step 2: Create Access Application

```bash
open https://one.dash.cloudflare.com/a9c52e892f7361bab3bfd084c6ffaccb/access/apps
```

**Application Settings**:
- Name: `Goblin Ops Panel`
- Session Duration: `24 hours`
- Application Domain: `ops.goblin.fuaad.ai`

**Policy**:
- Name: `Goblin Admins Only`
- Action: `Allow`
- Include: `Goblin Admins` group

**Identity Providers**:
- ✅ One-time PIN (email)
- ✅ Google (optional)
- ✅ GitHub (optional)

### Step 3: Connect to Origin

**Option A: Cloudflare Tunnel**
```bash
# If ops panel is self-hosted
cloudflared tunnel route dns 9c780bd1-ac63-4d6c-afb1-787a2867e5dd ops.goblin.fuaad.ai
```

**Option B: Public Origin**
```
Origin: https://your-admin-panel.vercel.app
```

---

## 📊 Monitoring & Analytics

### Cloudflare Analytics

View traffic for each subdomain:

```bash
# Frontend traffic
open https://dash.cloudflare.com/a9c52e892f7361bab3bfd084c6ffaccb/fuaad.ai/analytics?domain=goblin.fuaad.ai

# API traffic
open https://dash.cloudflare.com/a9c52e892f7361bab3bfd084c6ffaccb/fuaad.ai/analytics?domain=api.goblin.fuaad.ai

# Brain traffic
open https://dash.cloudflare.com/a9c52e892f7361bab3bfd084c6ffaccb/fuaad.ai/analytics?domain=brain.goblin.fuaad.ai
```

### Worker Analytics

```bash
# View brain.goblin.fuaad.ai (Worker) metrics
open https://dash.cloudflare.com/a9c52e892f7361bab3bfd084c6ffaccb/workers/services/view/goblin-assistant-edge/production/analytics
```

### D1 Database Queries

```bash
# Cost per subdomain (if logging includes subdomain)
wrangler d1 execute goblin-assistant-db --remote --command "
  SELECT
    provider,
    COUNT(*) as requests,
    SUM(cost_usd) as total_cost
  FROM inference_logs
  WHERE timestamp > datetime('now', '-7 days')
  GROUP BY provider
"
```

---

## 🚨 Troubleshooting

### DNS Not Resolving

**Problem**: `dig goblin.fuaad.ai` returns NXDOMAIN

**Solutions**:
1. Wait for DNS propagation (can take up to 24 hours, usually <5 minutes)
2. Check Cloudflare DNS records are created correctly
3. Verify domain nameservers point to Cloudflare:
   ```bash
   dig NS fuaad.ai
   # Should return: *.ns.cloudflare.com
   ```
4. Check Cloudflare Zone status (not paused/suspended)

### SSL Certificate Errors

**Problem**: Browser shows "Not Secure" or certificate mismatch

**Solutions**:
1. Wait for SSL provisioning (can take 15-30 minutes)
2. Check SSL/TLS mode is "Full (strict)"
3. Verify origin server has valid SSL certificate
4. Check certificate covers wildcard (`*.goblin.fuaad.ai`)

### CORS Errors in Frontend

**Problem**: Browser console shows CORS errors

**Solutions**:
1. Update backend CORS configuration with new subdomain
2. Verify `Access-Control-Allow-Origin` header in response
3. Check Cloudflare isn't stripping CORS headers (shouldn't happen)
4. Test API directly: `curl -H "Origin: https://goblin.fuaad.ai" https://api.goblin.fuaad.ai/health -v`

### Worker Not Accessible

**Problem**: `brain.goblin.fuaad.ai` returns 522 error

**Solutions**:
1. Verify Worker is deployed: `wrangler deployments list`
2. Check Worker custom domain is configured:
   ```bash
   wrangler domains list
   ```
3. Add custom domain if missing:
   ```bash
   wrangler domains add brain.goblin.fuaad.ai
   ```
4. Verify DNS CNAME points to Worker (check Dashboard)

### Zero Trust Login Loop

**Problem**: ops.goblin.fuaad.ai redirects infinitely

**Solutions**:
1. Check Access Application subdomain matches exactly
2. Verify you're in the Goblin Admins group
3. Clear Cloudflare Access cookies:
   ```bash
   # In browser DevTools Console
   document.cookie.split(";").forEach(c => document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/"));
   ```
4. Try incognito/private window

---

## 📚 Additional Resources

### Cloudflare Documentation

- [DNS Records](https://developers.cloudflare.com/dns/manage-dns-records/how-to/create-dns-records/)
- [Workers Custom Domains](https://developers.cloudflare.com/workers/configuration/routing/custom-domains/)
- [Zero Trust Access](https://developers.cloudflare.com/cloudflare-one/applications/)
- [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)

### API References

- [Cloudflare API - DNS Records](https://developers.cloudflare.com/api/operations/dns-records-for-a-zone-create-dns-record)
- [Cloudflare API - Workers](https://developers.cloudflare.com/api/operations/worker-routes-list-routes)

---

## ✅ Checklist

- [ ] Get Cloudflare API token with Zone.DNS permissions
- [ ] Get Zone ID for fuaad.ai domain
- [ ] Create DNS records for all subdomains
- [ ] Configure SSL/TLS to Full (strict)
- [ ] Update frontend environment variables (API URLs)
- [ ] Update backend environment variables (CORS origins)
- [ ] Update Cloudflare Worker wrangler.toml (URLs)
- [ ] Deploy updated frontend to production
- [ ] Deploy updated backend to production
- [ ] Deploy updated Worker with `wrangler deploy`
- [ ] Set up Zero Trust for ops.goblin.fuaad.ai
- [ ] Test all subdomains (DNS, SSL, functionality)
- [ ] Configure page rules for optimization
- [ ] Set up monitoring/analytics
- [ ] Update documentation with new URLs

---

**Last Updated**: December 2, 2025
**Status**: Configuration Guide Complete
**Next Steps**: Run `./setup_subdomains.sh` to automate DNS setup
