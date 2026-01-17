# 🚀 GoblinOS Assistant - DuckDNS Domain Setup

**Domain:** goblinosassistant.duckdns.org  
**Backend:** Fly.io (`goblin-backend`)  
**Frontend:** Vercel  

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  👤 Customer                                                │
│                                                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │
          ┌──────────▼──────────┐
          │                     │
          │  goblinosassistant  │  ← DuckDNS Main Domain
          │  .duckdns.org       │
          │                     │
          └──────────┬──────────┘
                     │
                     │ Points to Vercel IP
                     │
          ┌──────────▼──────────┐
          │                     │
          │  Frontend (Vercel)  │  ← Next.js App
          │  goblin-assistant   │
          │                     │
          └──────────┬──────────┘
                     │
                     │ API calls to
                     │
          ┌──────────▼──────────┐
          │                     │
          │  Backend (Fly.io)   │  ← FastAPI
          │  goblin-backend     │
          │  .fly.dev           │
          │                     │
          └─────────────────────┘
```

---

## 📋 Setup Steps

### Step 1: Get Vercel Domain IP

1. Go to your Vercel project: https://vercel.com/[your-username]/[project-name]
2. Navigate to **Settings** → **Domains**
3. Click **Add Domain**
4. Enter: `goblinosassistant.duckdns.org`
5. Vercel will provide an IP address (typically `76.76.21.21` or similar)

### Step 2: Configure DuckDNS

1. Go to https://www.duckdns.org/domains
2. You should see your domain: `goblinosassistant`
3. Update the IP to the **Vercel IP** from Step 1
4. Click **Update IP**

### Step 3: Wait for DNS Propagation

```bash
# Check DNS resolution (wait 2-5 minutes)
dig +short goblinosassistant.duckdns.org

# Should return Vercel's IP
```

### Step 4: Verify Vercel Domain

1. Back in Vercel dashboard
2. Wait for the domain to show **Valid Configuration** ✅
3. Vercel will automatically provision SSL certificate

### Step 5: Update Environment Variables in Vercel

In Vercel dashboard → **Settings** → **Environment Variables**, add/update:

```env
BACKEND_URL=https://goblin-backend.fly.dev
NEXT_PUBLIC_API_URL=https://goblin-backend.fly.dev
NEXT_PUBLIC_DOMAIN=goblinosassistant.duckdns.org
```

### Step 6: Redeploy Frontend

```bash
# From your local machine
cd apps/goblin-assistant
git add vercel.json
git commit -m "feat: Configure Vercel with Fly.io backend and DuckDNS domain"
git push

# Vercel will auto-deploy on push
```

---

## ✅ Verification

### Test Backend (Fly.io)

```bash
# Health check
curl https://goblin-backend.fly.dev/health

# Should return: {"status": "healthy"}
```

### Test Frontend (Vercel + DuckDNS)

```bash
# Check homepage
curl -I https://goblinosassistant.duckdns.org

# Should return: 200 OK with SSL certificate
```

### Test Full Flow

1. Open: https://goblinosassistant.duckdns.org
2. Try the chat interface
3. Check browser console for API calls to `goblin-backend.fly.dev`

---

## 🔧 Alternative: Use Second DuckDNS Domain for Backend

If you want a custom domain for the backend too:

### Option A: Register `goblinapi` on DuckDNS

1. Go to https://www.duckdns.org/domains
2. Register: `goblinapi` (you have 5 domains available)
3. Get Fly.io backend IP:
   ```bash
   flyctl ips list -a goblin-backend
   ```
4. Update `goblinapi` IP on DuckDNS
5. Add custom certificate:
   ```bash
   flyctl certs create goblinapi.duckdns.org -a goblin-backend
   ```
6. Update `vercel.json` to use `goblinapi.duckdns.org`

---

## 🐛 Troubleshooting

### DNS Not Resolving

```bash
# Check current DNS
dig +short goblinosassistant.duckdns.org @8.8.8.8

# Force update DuckDNS
curl "https://www.duckdns.org/update?domains=goblinosassistant&token=59be274c-ca62-4e86-b671-035cee6f5bad&ip="
```

### Vercel Domain Not Validating

1. Make sure DuckDNS IP matches Vercel's IP exactly
2. Wait 5-10 minutes for DNS propagation
3. Try removing and re-adding the domain in Vercel

### Backend Not Accessible

```bash
# Check Fly.io app status
flyctl status -a goblin-backend

# View logs
flyctl logs -a goblin-backend

# Restart app
flyctl apps restart goblin-backend
```

### CORS Errors

Make sure your backend (FastAPI) has CORS enabled for the Vercel domain:

```python
# In backend code
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://goblinosassistant.duckdns.org",
        "http://localhost:3000"  # for local dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 💰 Cost Breakdown

| Service | Domain | SSL | Monthly Cost |
|---------|--------|-----|--------------|
| DuckDNS | goblinosassistant.duckdns.org | Free | $0 |
| Fly.io Backend | goblin-backend.fly.dev | Free | $0-5* |
| Vercel Frontend | (custom domain) | Free | $0-20** |
| **Total** | | | **$0-25/month** |

\* Free tier includes 3 shared CPUs + 256MB RAM  
\*\* Free tier includes 100GB bandwidth

---

## 📞 Quick Commands

```bash
# Check Fly.io backend
flyctl status -a goblin-backend
flyctl logs -a goblin-backend

# Check Vercel deployment
vercel --prod

# Update DuckDNS manually
curl "https://www.duckdns.org/update?domains=goblinosassistant&token=59be274c-ca62-4e86-b671-035cee6f5bad&ip="

# Test endpoints
curl https://goblin-backend.fly.dev/health
curl https://goblinosassistant.duckdns.org
```

---

## 🎉 Success Checklist

- [ ] DuckDNS domain points to Vercel IP
- [ ] Vercel domain shows "Valid Configuration" ✅
- [ ] Vercel environment variables updated
- [ ] Frontend deploys successfully
- [ ] Backend health check returns 200
- [ ] Frontend loads at https://goblinosassistant.duckdns.org
- [ ] Chat interface works end-to-end
- [ ] No CORS errors in browser console

---

## 📚 Resources

- **DuckDNS Dashboard:** https://www.duckdns.org/domains
- **Vercel Dashboard:** https://vercel.com/dashboard
- **Fly.io Dashboard:** https://fly.io/dashboard
- **Your DuckDNS Token:** `59be274c-ca62-4e86-b671-035cee6f5bad`

**Account:** fuaadabdullah@gmail.com  
**Setup Date:** January 12, 2026

---

**Ready to go live!** 🚀
