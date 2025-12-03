# Deployment Architecture

## Overview

The GoblinOS Assistant uses a three-tier deployment architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    DEPLOYMENT ARCHITECTURE                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐      ┌──────────────┐      ┌────────────┐ │
│  │   VERCEL    │─────▶│    RENDER    │─────▶│  KAMATERA  │ │
│  │  (Frontend) │      │  (Backend)   │      │ (LLM Models)│ │
│  └─────────────┘      └──────────────┘      └────────────┘ │
│                                                               │
│  UI/React App          FastAPI Server       Ollama Server   │
│  Static Assets         PostgreSQL DB        Local Models    │
│  CDN Distribution      Redis Cache                          │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. Frontend - Vercel
**Service**: Static Site Hosting
**URL**: `https://goblin-assistant.vercel.app`

**Why Vercel?**
- ✅ Zero-config deployment for Vite/React apps
- ✅ Global CDN with edge caching
- ✅ Automatic HTTPS and SSL
- ✅ Preview deployments for PRs
- ✅ Excellent performance and uptime
- ✅ Free tier sufficient for development

**Configuration**: `vercel.json`
- Framework: Vite
- Build Command: `npm run build`
- Output Directory: `dist`
- API Proxy: Forwards `/api/*` to Render backend

### 2. Backend - Render
**Service**: Web Service (Python)
**URL**: `https://goblin-assistant-backend.onrender.com`

**Why Render?**
- ✅ Native Python support with pip
- ✅ Managed PostgreSQL database
- ✅ Environment variable management
- ✅ Auto-deploy from Git
- ✅ Health check monitoring
- ✅ Built-in SSL certificates
- ✅ Better for long-running backend processes than serverless

**Configuration**: `render.yaml`
- Runtime: Python 3.11
- Start Command: `python start_server.py`
- Health Check: `/health` endpoint
- Database: Managed PostgreSQL (starter plan)
- Redis: Optional, for production caching

**Environment Variables** (Set in Render Dashboard):
```bash
# Required
DATABASE_URL=<from Render PostgreSQL>
LOCAL_LLM_PROXY_URL=http://45.61.60.3:8002
LOCAL_LLM_API_KEY=<your-kamatera-api-key>
JWT_SECRET_KEY=<generated>
FRONTEND_URL=https://goblin-assistant.vercel.app

# AI Providers
OPENAI_API_KEY=<your-key>
ANTHROPIC_API_KEY=<your-key>
DEEPSEEK_API_KEY=<your-key>
GEMINI_API_KEY=<your-key>
GROK_API_KEY=<your-key>

# OAuth
GOOGLE_CLIENT_ID=<your-id>
GOOGLE_CLIENT_SECRET=<your-secret>
GOOGLE_REDIRECT_URI=https://goblin-assistant.vercel.app/auth/google/callback

# Supabase
SUPABASE_URL=<your-url>
SUPABASE_ANON_KEY=<your-key>
SUPABASE_SERVICE_ROLE_KEY=<your-key>
```

### 3. LLM Models - Kamatera VPS
**Service**: Self-hosted Ollama Server
**URL**: `http://45.61.60.3:8002`

**Why Kamatera?**
- ✅ Cost-effective for running local LLM models
- ✅ Full control over model deployment
- ✅ No per-token pricing (fixed monthly cost)
- ✅ GPU support for faster inference
- ✅ Can run multiple models simultaneously
- ✅ Private network for sensitive data

**Configuration**:
- Server: Ubuntu VPS with GPU
- Software: Ollama + Custom API Proxy
- Models: gemma:2b, phi3:3.8b, qwen2.5:3b, mistral:7b
- API: Custom FastAPI proxy with authentication
- Port: 8002 (with firewall rules)

**Models Available**:
```
gemma:2b        - Safety verification (1.7GB)
phi3:3.8b       - Confidence scoring (2.2GB)
qwen2.5:3b      - Advanced reasoning (1.9GB)
mistral:7b      - Top-tier responses (4.1GB)
deepseek-coder  - Code generation (776MB)
```

## Data Flow

### 1. User Request Flow
```
User Browser
    ↓
Vercel (Static UI)
    ↓
Render Backend (/api/chat/completions)
    ↓
Kamatera LLM Server (http://45.61.60.3:8002)
    ↓
Ollama Model Inference
    ↓
← Response flows back up the chain
```

### 2. Authentication Flow
```
User → Vercel UI → Google OAuth
                      ↓
                   Render Backend (validates token)
                      ↓
                   PostgreSQL (stores session)
                      ↓
                   ← JWT returned to client
```

## Deployment Instructions

### Deploy Frontend to Vercel

1. **Install Vercel CLI** (if not already installed):
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**:
   ```bash
   vercel login
   ```

3. **Deploy from project root**:
   ```bash
   cd apps/goblin-assistant
   vercel --prod
   ```

4. **Configure Environment Variables** in Vercel Dashboard:
   - Go to Project Settings → Environment Variables
   - Add variables from `.env.production`
   - Or import from `.env.production` file

5. **Set Custom Domain** (optional):
   - Go to Project Settings → Domains
   - Add `goblin-assistant.vercel.app` or custom domain

### Deploy Backend to Render

1. **Create Render Account**:
   - Sign up at https://render.com
   - Connect your GitHub repository

2. **Create New Web Service**:
   - Click "New +" → "Web Service"
   - Select repository: `forgemono`
   - Name: `goblin-assistant-backend`
   - Root Directory: `apps/goblin-assistant/backend`
   - Runtime: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python start_server.py`

3. **Create PostgreSQL Database**:
   - Click "New +" → "PostgreSQL"
   - Name: `goblin-assistant-db`
   - Plan: Starter (free tier)
   - Region: Oregon (or closest to your users)

4. **Link Database to Web Service**:
   - In Web Service settings → Environment
   - Add `DATABASE_URL` → Connect to Internal Database
   - Select `goblin-assistant-db`

5. **Add Environment Variables**:
   - Copy all variables from `render.yaml` envVars section
   - Or use Render CLI to sync from file:
     ```bash
     render deploy --config render.yaml
     ```

6. **Configure Health Check**:
   - Path: `/health`
   - Interval: 30 seconds

7. **Deploy**:
   - Click "Manual Deploy" → "Deploy latest commit"
   - Or enable auto-deploy on push to main

### Configure Kamatera LLM Server

1. **SSH into VPS**:
   ```bash
   ssh root@45.61.60.3
   ```

2. **Install Ollama**:
   ```bash
   curl https://ollama.ai/install.sh | sh
   ```

3. **Pull Required Models**:
   ```bash
   ollama pull gemma:2b
   ollama pull phi3:3.8b
   ollama pull qwen2.5:3b
   ollama pull mistral:7b
   ```

4. **Start Ollama Service**:
   ```bash
   systemctl start ollama
   systemctl enable ollama
   ```

5. **Configure API Proxy** (if using custom proxy):
   ```bash
   cd /opt/llm-proxy
   python3 local_llm_proxy.py
   ```

6. **Configure Firewall**:
   ```bash
   ufw allow 8002/tcp
   ufw enable
   ```

7. **Test Connection**:
   ```bash
   curl http://45.61.60.3:8002/health
   ```

## Monitoring & Maintenance

### Vercel
- Monitor deployments: https://vercel.com/dashboard
- View build logs for errors
- Check analytics for traffic patterns
- Set up uptime monitoring (optional)

### Render
- Monitor service health: https://dashboard.render.com
- Check logs for backend errors
- Monitor PostgreSQL database metrics
- Set up alerts for downtime
- Review billing and resource usage

### Kamatera
- Monitor VPS resources (CPU, RAM, disk)
- Check Ollama logs: `journalctl -u ollama -f`
- Monitor API proxy logs
- Set up backup for model configurations
- Update models periodically

## Cost Breakdown

### Monthly Costs (Estimated)

| Service | Plan | Cost |
|---------|------|------|
| Vercel (Frontend) | Hobby | $0 (free tier) |
| Render (Backend) | Starter | $7/month |
| Render (PostgreSQL) | Starter | $7/month |
| Kamatera (VPS) | Custom | $20-50/month |
| **Total** | | **$34-64/month** |

### Cost Optimization Tips
- Use Vercel free tier for hobby projects
- Upgrade Render only when needed (500 build hours/month on free tier)
- Kamatera: Use spot instances or reserved pricing
- Redis: Start with in-memory, add Redis only in production

## Security Considerations

### Frontend (Vercel)
- ✅ HTTPS enabled by default
- ✅ Environment variables hidden from client
- ✅ CORS configured for backend API
- ⚠️ Never expose API keys in frontend code

### Backend (Render)
- ✅ Environment variables encrypted at rest
- ✅ SSL/TLS for all connections
- ✅ Database connection encrypted
- ⚠️ Use firewall rules to restrict access
- ⚠️ Rotate JWT secrets regularly

### Kamatera (LLM Server)
- ✅ API key authentication required
- ✅ Firewall configured (UFW)
- ⚠️ Use VPN or private network if possible
- ⚠️ Keep Ollama and system packages updated
- ⚠️ Monitor access logs for suspicious activity

## Troubleshooting

### Frontend Issues
**Problem**: Build fails on Vercel
- Check `package.json` dependencies
- Ensure `vite.config.ts` is correct
- Review build logs in Vercel dashboard

**Problem**: API calls failing
- Verify `VITE_API_URL` in environment variables
- Check CORS configuration in backend
- Inspect network tab in browser DevTools

### Backend Issues
**Problem**: Service won't start on Render
- Check `requirements.txt` for missing dependencies
- Review start command syntax
- Check environment variables are set
- Review build logs for errors

**Problem**: Database connection fails
- Verify `DATABASE_URL` is set correctly
- Check PostgreSQL service is running
- Review Render database logs

### LLM Server Issues
**Problem**: Models not responding
- Check Ollama service: `systemctl status ollama`
- Verify models are loaded: `ollama list`
- Check disk space: `df -h`
- Review API proxy logs

**Problem**: Connection timeout from Render
- Verify firewall allows connections from Render IPs
- Check Kamatera server is running
- Test locally: `curl http://45.61.60.3:8002/health`

## Rollback Procedures

### Frontend (Vercel)
```bash
# Revert to previous deployment
vercel rollback <deployment-url>

# Or via dashboard:
# Deployments → Select working deployment → Promote to Production
```

### Backend (Render)
```bash
# Via Render Dashboard:
# Services → goblin-assistant-backend → Deploys → Select previous → Redeploy
```

### Database Migrations
```bash
# Rollback Alembic migration
alembic downgrade -1
```

## Next Steps

1. **Set up CI/CD**:
   - Configure GitHub Actions for automated testing
   - Add deployment workflows

2. **Add Monitoring**:
   - Set up Sentry for error tracking
   - Add PostHog for analytics
   - Configure Datadog for infrastructure monitoring

3. **Implement Caching**:
   - Add Redis for session management
   - Cache LLM responses for common queries
   - Use CDN caching for static assets

4. **Scale as Needed**:
   - Upgrade Render plan for more resources
   - Add load balancer for backend
   - Scale Kamatera VPS or add multiple servers

## Support

For deployment issues:
- Vercel: https://vercel.com/support
- Render: https://render.com/docs/support
- Kamatera: support@kamatera.com

For code issues:
- GitHub Issues: https://github.com/fuaadabdullah/forgemono/issues
- GoblinOS Docs: `/GoblinOS/docs/`
