# 🚀 Fly.io Deployment Checklist

## ✅ Pre-Deployment (Complete)

- [x] Database migration from in-memory to SQLite/PostgreSQL
- [x] Fixed `models_base.py` to use unified Base object
- [x] Updated `start_server.py` for production (PORT env var)
- [x] Created `fly.toml` configuration
- [x] Created deployment script `deploy-fly.sh`
- [x] Created documentation `FLY_DEPLOYMENT.md`

## 📋 Deployment Steps

### Step 1: Commit Changes

```bash
cd /Users/fuaadabdullah/ForgeMonorepo
git status  # Review changes
git add apps/goblin-assistant/
git commit -m "feat: add Fly.io deployment config and database persistence"
git push origin main
```

### Step 2: Deploy to Fly.io

#### Option A: Dashboard (Recommended)

1. [ ] Go to <https://fly.io/dashboard>
2. [ ] Click "New +" → "Blueprint"
3. [ ] Connect GitHub: `fuaadabdullah/forgemono`
4. [ ] Fly uses `fly.toml` and the `flyctl` CLI; you can also use the Fly dashboard
5. [ ] Click "Apply"

#### Option B: Script

```bash
cd apps/goblin-assistant
./deploy-backend.sh fly
```

### Step 3: Configure Environment Variables

In Fly dashboard or using `flyctl`, add:

#### Required API Keys

- [ ] `ANTHROPIC_API_KEY` - Get from <https://console.anthropic.com>
- [ ] `DEEPSEEK_API_KEY` - Get from <https://platform.deepseek.com>
- [ ] `GEMINI_API_KEY` - Get from <https://makersuite.google.com/app/apikey>
- [ ] `GROK_API_KEY` - Get from <https://console.x.ai>

#### Auto-Generated (No action needed)

- [ ] `PORT` - Auto-set by Fly (or defined in fly.toml)
- [ ] `DATABASE_URL` - Auto-set if using a managed DB or via your DB provider config
- [ ] `JWT_SECRET_KEY` - Configure in Fly secrets (`fly secrets set JWT_SECRET_KEY=...`)

#### Optional

- [ ] `GOOGLE_CLIENT_ID` - For Google OAuth
- [ ] `GOOGLE_CLIENT_SECRET` - For Google OAuth
- [ ] `SENTRY_DSN` - For error tracking
- [ ] `POSTHOG_API_KEY` - For analytics

### Step 4: Monitor Deployment

1. [ ] Watch build logs in Fly dashboard (`fly logs`) or use `flyctl logs`
2. [ ] Wait for "Deploy succeeded" message (5-10 minutes)
3. [ ] Note your backend URL: `https://goblin-assistant.fly.dev`

### Step 5: Test Deployment

```bash
# Replace with your actual URL
BACKEND_URL="https://goblin-assistant.fly.dev"

# Test health endpoint
curl $BACKEND_URL/health

# Expected response:
# {"status":"healthy","timestamp":...}

# Test API endpoint
curl $BACKEND_URL/api/goblins

# Should return list of goblins
```

### Step 6: Update Frontend

If deploying frontend separately:

1. [ ] Update frontend environment variable:

   ```bash
   VITE_FASTAPI_URL=https://goblin-assistant.fly.dev
   ```

2. [ ] Redeploy frontend (Vercel)

## 🔍 Verification Checklist

After deployment:

- [ ] Health check endpoint works: `/health`
- [ ] Database tables created automatically
- [ ] API endpoints respond correctly
- [ ] CORS configured for frontend domain
- [ ] SSL certificate active (https://)
- [ ] Environment variables loaded correctly

## � Security & Production Hardening

Before deploying to production, make sure to complete the following steps (where applicable):

- [ ] Do not use `backend/api_keys.json` in production. Use a secrets manager or encrypt keys in the database and use `ROUTING_ENCRYPTION_KEY` to decrypt them.
- [ ] Set `ROUTING_ENCRYPTION_KEY` and store it in a secure secrets manager; do NOT commit it to git or store as plain `.env` in source control.
- [ ] Switch from the in-memory rate limiter to a Redis-backed rate limiter (or similar distributed rate limiting) to support multiple instances.
- [ ] Confirm RQ/Redis is configured and production-ready (authentication, TLS, backups) before enabling background workers.
- [ ] Validate `LOCAL_LLM_PROXY` is behind internal network access or secured with API keys and that `LOCAL_LLM_API_KEY` is rotated and not embedded in code.
- [ ] Set and rotate `JWT_SECRET_KEY` and any other token secrets used for authentication.
- [ ] Enable HTTPS with TLS termination at the edge and implement secure headers (HSTS, CSP, CORS) for the frontend.
- [ ] Set up monitoring alerts for `provider` health and routing errors, and configure budget-based alerts for cost monitoring if cloud providers are used.

### Frontend Production Checklist

Before building and deploying the frontend, verify these items:

- [ ] No secrets (API keys, private tokens) are included in any `VITE_*` env vars — set them only server-side.
- [ ] Authentication uses HttpOnly & Secure cookies for session tokens or a secure refresh token flow; avoid persisting long-lived tokens in `localStorage`.
- [ ] Streaming endpoints are authenticated with secure session cookies or a short-lived single-use stream token; do not pass secrets in query string.
- [ ] Configure a strong Content Security Policy (CSP) header and input sanitization to reduce XSS risk.
- [ ] Configure Cloudflare Turnstile correctly: keys are public in the frontend, but verification happens server-side.
- [ ] CORS allowed origin is set to the frontend production domain(s), don't set `'*'` in production.
- [ ] Add Sentry / error reporting for the frontend and map `X-Correlation-ID` to backend logs.
- [ ] Add E2E tests for sign-in, chat flow, streaming, and provider fallback scenarios.

## �🐛 Troubleshooting

### Build Failed

- [ ] Check `requirements.txt` includes all dependencies
 - [ ] Verify `fly.toml` syntax and configuration
- [ ] Check build logs for specific error

### Runtime Errors

- [ ] Verify all required API keys are set
- [ ] Check `DATABASE_URL` is correct
- [ ] Review application logs in dashboard

### Database Issues

- [ ] Ensure PostgreSQL service is running
- [ ] Verify `DATABASE_URL` connection string
- [ ] Check database tables were created (auto-migration)

## 📊 Post-Deployment

### Monitoring

- [ ] Set up uptime monitoring (Fly provides this or use an external provider)
- [ ] Configure alerts for service down
- [ ] Review metrics: CPU, Memory, Requests

### Security

- [ ] Verify SSL certificate is active
- [ ] Check CORS settings
- [ ] Review firewall rules (if using external DB)
- [ ] Enable DDoS protection

### Optimization

- [ ] Monitor response times
- [ ] Check database query performance
- [ ] Review log levels for production
- [ ] Consider upgrading from free tier if needed

## 💰 Cost Estimate

### Free Tier (First Month)

- Web Service: 750 hours free
- PostgreSQL: Free tier available
- **Total: $0/month**

### Paid (After Free Tier)

- Web Service (Starter): $7/month
- PostgreSQL (Starter): $7/month
- **Total: ~$14/month**

## 📞 Support Resources

 - **Fly Docs**: <https://fly.io/docs>
 - **Fly Status**: <https://status.fly.io/>
- **Community**: https://fly.io/community/
- **GitHub Issues**: Report bugs in your repo

## ✨ Success Criteria

Deployment is successful when:

- [x] All files created
- [ ] Code pushed to GitHub
- [ ] Fly service deployed
- [ ] Health check passes
- [ ] Database connected
- [ ] API endpoints working
- [ ] Frontend can connect to backend

---

**Created**: December 1, 2025
**Status**: Ready for deployment
**Platform**: Fly.io
**Database**: PostgreSQL (with SQLite fallback)
