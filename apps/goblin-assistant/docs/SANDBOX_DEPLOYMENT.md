# Sandbox Deployment: Fly.io Backend + Vercel Frontend + DuckDNS

This guide explains how to deploy the Goblin Assistant with the sandbox execution feature fully working:

- **Frontend**: Vercel (Next.js)
- **Backend**: Fly.io (FastAPI)
- **Public Domain**: `goblinosassistant.duckdns.org`

---

## Prerequisites

1. **Fly.io CLI** installed: `brew install flyctl` or see https://fly.io/docs/hands-on/install-flyctl/
2. **Vercel CLI** (optional): `npm i -g vercel`
3. **DuckDNS account**: https://www.duckdns.org (free dynamic DNS)
4. You have the subdomain `goblinosassistant` registered on DuckDNS

---

## 1. Deploy Backend to Fly.io

### 1.1 Authenticate with Fly
```bash
flyctl auth login
```

### 1.2 Deploy from `apps/goblin-assistant`
```bash
cd apps/goblin-assistant
flyctl deploy
```

This uses the `fly.toml` in the directory. Key settings already configured:
- **App name**: `goblin-backend`
- **Region**: `iad` (US East)
- **Port**: `8001`
- **Sandbox enabled**: `SANDBOX_ENABLED=true`
- **CORS origins**: `ALLOWED_ORIGINS` includes `goblinosassistant.duckdns.org` and Vercel domains

### 1.3 Set Production Secrets on Fly
```bash
# Required secrets (replace with your actual values)
flyctl secrets set JWT_SECRET_KEY="your-secure-jwt-secret-here"
flyctl secrets set DATABASE_URL="postgresql://user:pass@host:5432/dbname"

# Optional but recommended
flyctl secrets set REDIS_URL="redis://default:password@host:6379"
flyctl secrets set SENTRY_DSN="https://xxx@sentry.io/xxx"

# If using Docker-based sandbox (optional, simulated mode works without this)
flyctl secrets set SANDBOX_IMAGE="your-sandbox-image:tag"
```

### 1.4 Verify Deployment
```bash
# Check app status
flyctl status

# Check logs
flyctl logs

# Test health endpoint
curl https://goblin-backend.fly.dev/health
```

---

## 2. Configure Custom Domain on Fly.io

To use `goblinosassistant.duckdns.org` as your backend domain:

### 2.1 Add Certificate for Custom Domain
```bash
flyctl certs create goblinosassistant.duckdns.org
```

Fly will output instructions. You may need to add a CNAME or A record.

### 2.2 Check Certificate Status
```bash
flyctl certs show goblinosassistant.duckdns.org
```

Wait until status shows `Ready`.

---

## 3. Configure DuckDNS

### 3.1 Get Your Fly.io App IPs
```bash
flyctl ips list
```

Note the IPv4 and IPv6 addresses.

### 3.2 Update DuckDNS

1. Go to https://www.duckdns.org
2. Find your `goblinosassistant` subdomain
3. Update the IP address to point to your Fly.io IPv4 address

**Or use the API:**
```bash
# Replace YOUR_TOKEN and YOUR_FLY_IP
curl "https://www.duckdns.org/update?domains=goblinosassistant&token=YOUR_TOKEN&ip=YOUR_FLY_IP"
```

### 3.3 Verify DNS Resolution
```bash
# Should return your Fly.io IP
dig goblinosassistant.duckdns.org +short

# Test the endpoint
curl -i https://goblinosassistant.duckdns.org/health
```

---

## 4. Deploy Frontend to Vercel

### 4.1 Connect Repository to Vercel

1. Go to https://vercel.com/new
2. Import your GitHub repository (`fuaadabdullah/forgemono`)
3. Set the **Root Directory** to `apps/goblin-assistant`
4. Vercel will auto-detect Next.js

### 4.2 Environment Variables in Vercel Dashboard

The `vercel.json` already sets these, but you can override in the Vercel dashboard:

| Variable | Value |
|----------|-------|
| `BACKEND_URL` | `https://goblinosassistant.duckdns.org` |
| `NEXT_PUBLIC_API_URL` | `https://goblinosassistant.duckdns.org` |
| `NEXT_PUBLIC_DOMAIN` | `goblinosassistant.duckdns.org` |

### 4.3 Deploy
```bash
# From apps/goblin-assistant
vercel --prod
```

Or push to your branch and let Vercel auto-deploy.

### 4.4 Verify Frontend
Visit your Vercel deployment URL (e.g., `https://goblin-assistant.vercel.app`).

---

## 5. Verify Sandbox Feature

### 5.1 Check Sandbox Health
```bash
curl -s https://goblinosassistant.duckdns.org/health/sandbox/status | jq
```

Expected response:
```json
{
  "status": "healthy",
  "mode": "simulated",
  "isolation": "none",
  "note": "Using in-memory task simulation (no Docker isolation)"
}
```

### 5.2 Check Full Health
```bash
curl -s https://goblinosassistant.duckdns.org/health/all | jq
```

### 5.3 Test from Frontend
1. Open your Vercel frontend URL
2. Navigate to the Sandbox page (if available in UI)
3. Submit a code execution request
4. Verify the job is queued and executed

---

## 6. Troubleshooting

### CORS Errors
- Ensure `ALLOWED_ORIGINS` in `fly.toml` includes your frontend domain
- Check browser console for the exact origin being blocked
- Redeploy Fly after updating `fly.toml`

### Sandbox Returns "degraded"
- Check if `SANDBOX_ENABLED` is set to `true`
- In simulated mode, sandbox is always "healthy" as fallback
- For Docker mode, ensure `SANDBOX_IMAGE` is set and Docker is available

### Certificate Issues
```bash
# Check cert status
flyctl certs show goblinosassistant.duckdns.org

# If stuck, remove and recreate
flyctl certs remove goblinosassistant.duckdns.org
flyctl certs create goblinosassistant.duckdns.org
```

### DNS Not Resolving
- DuckDNS updates can take a few minutes
- Verify at https://www.duckdns.org that your IP is correct
- Try flushing local DNS: `sudo dscacheutil -flushcache` (macOS)

---

## 7. Architecture Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Browser                            │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Vercel (Frontend)                            │
│                 goblin-assistant.vercel.app                     │
│                                                                 │
│  • Next.js app                                                  │
│  • Rewrites /api/* → goblinosassistant.duckdns.org             │
│  • Rewrites /v1/* → goblinosassistant.duckdns.org              │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│               DuckDNS (goblinosassistant.duckdns.org)          │
│                    Points to Fly.io IP                          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Fly.io (Backend)                             │
│                      goblin-backend                             │
│                                                                 │
│  • FastAPI app (api/main.py)                                    │
│  • CORS configured for frontend domains                         │
│  • Sandbox execution (simulated or Docker)                      │
│  • Health endpoints: /health, /health/sandbox/status            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8. Files Changed

| File | Change |
|------|--------|
| `apps/goblin-assistant/vercel.json` | Updated `BACKEND_URL`, `NEXT_PUBLIC_API_URL`, and rewrites to use `goblinosassistant.duckdns.org` |
| `apps/goblin-assistant/fly.toml` | Added `SANDBOX_ENABLED=true` and `ALLOWED_ORIGINS` with frontend domains |

---

## 9. Quick Commands Reference

```bash
# Deploy backend
cd apps/goblin-assistant && flyctl deploy

# Deploy frontend
cd apps/goblin-assistant && vercel --prod

# Check Fly status
flyctl status

# Check Fly logs
flyctl logs -a goblin-backend

# Update DuckDNS IP
curl "https://www.duckdns.org/update?domains=goblinosassistant&token=YOUR_TOKEN&ip=YOUR_FLY_IP"

# Test backend health
curl https://goblinosassistant.duckdns.org/health

# Test sandbox status
curl https://goblinosassistant.duckdns.org/health/sandbox/status
```
