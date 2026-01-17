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

## 7. Docker-Based Sandbox (Full Isolation)

The sandbox supports two modes:

1. **Simulated mode**: Subprocess-based execution (always available, minimal isolation)
2. **Docker mode**: Full container isolation (requires Docker + sandbox image)

### 7.1 Build the Sandbox Image

```bash
# From the api/sandbox directory
cd apps/goblin-assistant/api/sandbox
./build.sh

# Or manually:
docker build -t goblin/sandbox:latest .
```

### 7.2 Test the Sandbox Image Locally

```bash
# Basic test
docker run --rm goblin/sandbox:latest python3 -c "print('Hello from sandbox!')"

# Test with full security restrictions (as used in production)
docker run --rm \
  --network none \
  --read-only \
  --security-opt=no-new-privileges:true \
  --cap-drop=ALL \
  --memory=128m \
  --cpu-period=100000 \
  --cpu-quota=50000 \
  goblin/sandbox:latest \
  python3 -c "import sympy; x = sympy.Symbol('x'); print(sympy.simplify(sympy.sin(x)**2 + sympy.cos(x)**2))"
```

### 7.3 Push to Container Registry

```bash
# Tag for your registry
docker tag goblin/sandbox:latest registry.fly.io/goblin-sandbox:latest

# Push to Fly.io registry (if using Fly Machines)
flyctl auth docker
docker push registry.fly.io/goblin-sandbox:latest

# Or push to Docker Hub / GHCR
docker tag goblin/sandbox:latest your-registry/goblin-sandbox:latest
docker push your-registry/goblin-sandbox:latest
```

### 7.4 Configure Fly.io for Docker Sandbox

**Note**: Fly.io standard VMs don't support Docker-in-Docker. For full Docker isolation, you have two options:

**Option A: Fly Machines (recommended)**
Use Fly Machines API to spawn isolated containers per execution.

**Option B: Separate Docker Host**
Run a dedicated Docker host (e.g., on GCP, AWS, or self-hosted) and configure:
```bash
flyctl secrets set SANDBOX_IMAGE="your-registry/goblin-sandbox:latest"
flyctl secrets set DOCKER_HOST="tcp://your-docker-host:2376"
```

**Option C: Simulated Mode (default)**
Keep using simulated mode - it provides process-level isolation with:
- Subprocess execution
- Timeout enforcement
- Output limits
- Dangerous pattern blocking

### 7.5 Verify Docker Mode

If Docker is properly configured:
```bash
curl -s https://goblinosassistant.duckdns.org/v2/execute/status | jq
```

Expected response for Docker mode:
```json
{
  "mode": "docker",
  "available": true,
  "docker_available": true,
  "docker_image_found": true,
  "isolation_level": "full",
  "image": "goblin/sandbox:latest"
}
```

---

## 8. API Versions

| Endpoint | Description | Isolation |
|----------|-------------|-----------|
| `/execute/code` | Legacy endpoint | Simulated |
| `/v1/execute/code` | V1 with capabilities | Simulated |
| `/v2/execute/code` | V2 with Docker support | Docker or Simulated |

The v2 API automatically selects the best available mode:
- Uses Docker isolation when `SANDBOX_IMAGE` is configured and Docker is available
- Falls back to simulated mode otherwise

---

## 9. Architecture Summary

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
│  • Sandbox execution:                                           │
│    - V1: Simulated (subprocess)                                 │
│    - V2: Docker-based or simulated (auto-select)                │
│  • Health endpoints: /health, /health/sandbox/status            │
│  • Execution endpoints: /v1/execute/code, /v2/execute/code      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 10. Files Changed

| File | Change |
|------|--------|
| `apps/goblin-assistant/vercel.json` | Updated `BACKEND_URL`, `NEXT_PUBLIC_API_URL`, and rewrites to use `goblinosassistant.duckdns.org` |
| `apps/goblin-assistant/fly.toml` | Added `SANDBOX_ENABLED=true` and `ALLOWED_ORIGINS` with frontend domains |
| `apps/goblin-assistant/api/sandbox/` | New Docker sandbox module with Dockerfile, executor, and build script |
| `apps/goblin-assistant/api/execute_router_v2.py` | New V2 execute router with Docker support |
| `apps/goblin-assistant/api/main.py` | Added V2 execute router import and include |
| `apps/goblin-assistant/api/requirements.txt` | Added `docker>=7.0.0` for Docker SDK |

---

## 11. Quick Commands Reference

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

# Test sandbox status (v1)
curl https://goblinosassistant.duckdns.org/health/sandbox/status

# Test sandbox status (v2)
curl https://goblinosassistant.duckdns.org/v2/execute/status

# Test code execution (v2)
curl -X POST https://goblinosassistant.duckdns.org/v2/execute/code \
  -H "Content-Type: application/json" \
  -d '{"code": "print(\"Hello from Goblin Sandbox!\")"}'

# Build sandbox image locally
cd apps/goblin-assistant/api/sandbox && ./build.sh
```
