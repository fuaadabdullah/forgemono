# Subdomain Quick Start

**Get your Goblin Assistant production subdomains running in 5 minutes.**

## What You'll Get

- `goblin.fuaad.ai` → Frontend application
- `api.goblin.fuaad.ai` → Backend API
- `brain.goblin.fuaad.ai` → LLM inference gateway (Cloudflare Worker)
- `ops.goblin.fuaad.ai` → Admin panel (Zero Trust protected)

## Prerequisites

- Cloudflare account with `fuaad.ai` domain configured
- Cloudflare API token with **Zone.DNS (Edit)** permissions
- `curl` and `jq` installed (`brew install curl jq`)

## Quick Setup

### 1. Run Automated Script

```bash
cd apps/goblin-assistant/infra/cloudflare
./setup_subdomains.sh
```

**The script will:**
- ✅ Verify your Cloudflare API token
- ✅ List your domains and select `fuaad.ai`
- ✅ Ask for target IPs/CNAMEs for each subdomain
- ✅ Create all 4 DNS records (CNAME or A records)
- ✅ Enable SSL/TLS Full (strict) mode
- ✅ Enable Always Use HTTPS
- ✅ Test DNS propagation
- ✅ Save configuration to `.env` for future runs

### 2. Provide Target Information

When prompted, enter:

**Frontend** (`goblin.fuaad.ai`):
- If using Vercel/Netlify: Enter their CNAME (e.g., `cname.vercel-dns.com`)
- If using custom server: Enter IP address

**Backend API** (`api.goblin.fuaad.ai`):
- If using Railway/Render: Enter their CNAME
- If using VPS: Enter IP address

**Brain** (`brain.goblin.fuaad.ai`):
- Press Enter to use default: `goblin-assistant-edge.fuaadabdullah.workers.dev`
- Or provide custom Worker URL

**Ops** (`ops.goblin.fuaad.ai`):
- If using Cloudflare Tunnel: Enter tunnel CNAME
- If using VPS: Enter IP address

### 3. Wait for DNS Propagation

DNS records can take 5-30 minutes to propagate globally.

Test propagation:
```bash
dig goblin.fuaad.ai
dig api.goblin.fuaad.ai
dig brain.goblin.fuaad.ai
dig ops.goblin.fuaad.ai
```

### 4. Update Application Config

**Frontend** (`.env.production`):
```env
VITE_API_URL=https://api.goblin.fuaad.ai
VITE_BRAIN_URL=https://brain.goblin.fuaad.ai
VITE_TURNSTILE_SITE_KEY=0x4AAAAAACEUKA3R8flZ2Ig0
VITE_TURNSTILE_INVISIBLE_KEY=0x4AAAAAACEUKak3TnCntrFv
```

**Backend** (environment variables):
```env
FRONTEND_URL=https://goblin.fuaad.ai
CORS_ORIGINS=https://goblin.fuaad.ai,https://api.goblin.fuaad.ai,https://ops.goblin.fuaad.ai
```

**Worker** (`wrangler.toml`):
```toml
[vars]
API_URL = "https://api.goblin.fuaad.ai"
FRONTEND_URL = "https://goblin.fuaad.ai"
OPS_URL = "https://ops.goblin.fuaad.ai"
```

**FastAPI CORS** (`main.py`):
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

### 5. Test Your Subdomains

```bash
# Frontend
curl -I https://goblin.fuaad.ai

# Backend API
curl https://api.goblin.fuaad.ai/health | jq

# Brain (Inference Gateway)
curl https://brain.goblin.fuaad.ai/health | jq

# Ops (should require Zero Trust auth)
curl -I https://ops.goblin.fuaad.ai
```

### 6. Set Up Zero Trust (Optional)

Protect your admin panel:

1. Go to Cloudflare Zero Trust Dashboard:
   https://one.dash.cloudflare.com/

2. Create Access Application:
   - Name: `Goblin Assistant Ops`
   - Domain: `ops.goblin.fuaad.ai`
   - Policy: Allow `Goblin Admins` group (ID: `1eac441b-55ad-4be9-9259-573675e2d993`)

3. Test:
   ```bash
   curl -I https://ops.goblin.fuaad.ai
   # Should return 302 redirect to Cloudflare login
   ```

## What the Script Created

### DNS Records

| Subdomain | Type | Target | Proxied | SSL |
|-----------|------|--------|---------|-----|
| `goblin.fuaad.ai` | CNAME/A | Your frontend host | ✅ Yes | ✅ Full |
| `api.goblin.fuaad.ai` | CNAME/A | Your backend host | ✅ Yes | ✅ Full |
| `brain.goblin.fuaad.ai` | CNAME | Worker URL | ✅ Yes | ✅ Full |
| `ops.goblin.fuaad.ai` | CNAME/A | Your admin host | ✅ Yes | ✅ Full |

### SSL/TLS Settings

- Mode: **Full (strict)** - Requires valid cert on origin server
- Always Use HTTPS: **Enabled**
- Automatic HTTPS Rewrites: **Enabled**

## Troubleshooting

### DNS Not Resolving

```bash
# Check if record exists in Cloudflare
dig @1.1.1.1 goblin.fuaad.ai

# Check global propagation
dig @8.8.8.8 goblin.fuaad.ai
```

**Solution:** Wait 5-30 minutes for DNS propagation.

### SSL Certificate Error

```bash
# Check SSL cert
curl -vI https://goblin.fuaad.ai
```

**Solution:** SSL certs provision in 15-30 minutes after DNS is active.

### CORS Errors

**Solution:** Ensure all subdomains are in CORS config:
- Frontend at `goblin.fuaad.ai`
- API at `api.goblin.fuaad.ai`
- Brain at `brain.goblin.fuaad.ai`
- Ops at `ops.goblin.fuaad.ai`

### Worker Not Routing

```bash
# Check if Worker is accessible
curl https://goblin-assistant-edge.fuaadabdullah.workers.dev/health

# Check if custom domain is working
curl https://brain.goblin.fuaad.ai/health
```

**Solution:** Add custom domain in Cloudflare Dashboard:
1. Workers & Pages → goblin-assistant-edge → Settings → Triggers
2. Add Custom Domain: `brain.goblin.fuaad.ai`

## Re-running the Script

The script is **idempotent** - safe to run multiple times.

It will:
- Update existing DNS records instead of creating duplicates
- Use saved configuration from `.env`
- Only prompt for missing values

To change targets:
```bash
# Delete saved config
rm .env

# Re-run script
./setup_subdomains.sh
```

## Manual Configuration

If you prefer manual setup, see [SUBDOMAIN_SETUP.md](./SUBDOMAIN_SETUP.md) for step-by-step instructions using the Cloudflare Dashboard.

## Next Steps

1. ✅ DNS records created
2. ⏳ Wait for propagation (5-30 min)
3. ⏳ Update app configs with new URLs
4. ⏳ Deploy updated apps
5. ⏳ Test all endpoints
6. ⏳ Set up Zero Trust for ops panel
7. ⏳ Monitor logs and analytics

## Support

- Full documentation: [SUBDOMAIN_SETUP.md](./SUBDOMAIN_SETUP.md)
- Cloudflare Dashboard: https://dash.cloudflare.com/
- Zero Trust Dashboard: https://one.dash.cloudflare.com/

---

**Ready to deploy? Run `./setup_subdomains.sh` now!** 🚀
