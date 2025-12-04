# GoblinOS Assistant - Frontend Deployment (Vercel)

This directory contains the infrastructure configuration for deploying the GoblinOS Assistant frontend to Vercel.

## Files

- `vercel.json` - Vercel deployment configuration
- `deploy-vercel.sh` - Full deployment script with Bitwarden secrets integration
- `deploy-vercel-simple.sh` - Simple deployment script (manual secrets management)

## Deployment Configuration

### Vercel Configuration (`vercel.json`)

- **Framework**: Vite (React/TypeScript)
- **Build Command**: `npm run build`
- **Output Directory**: `dist`
- **API Proxy**: Routes `/api/*` requests to Fly.io backend
- **CORS Headers**: Configured for API access

## Deployment Scripts

### Full Deployment (`deploy-vercel.sh`)

This script provides complete automation with secrets management:

1. **Bitwarden Integration**: Loads secrets from Bitwarden vault
2. **Vercel Authentication**: Uses stored Vercel token
3. **Environment Setup**: Configures production environment variables
4. **Build & Deploy**: Builds and deploys the application

**Required Bitwarden Secrets:**
- `goblin-prod-vercel-token` - Vercel authentication token
- `goblin-prod-google-client-id` - Google OAuth client ID
- `goblin-prod-supabase-url` - Supabase project URL
- `goblin-prod-supabase-anon-key` - Supabase anonymous key

### Simple Deployment (`deploy-vercel-simple.sh`)

Basic deployment script that assumes:
- Vercel CLI is already authenticated
- Environment variables are set manually in Vercel dashboard

## Usage

### Full Automated Deployment

```bash
cd goblin-infra/projects/goblin-assistant/frontend
./deploy-vercel.sh
```

### Simple Deployment

```bash
cd goblin-infra/projects/goblin-assistant/frontend
./deploy-vercel-simple.sh
```

## Environment Variables

The following environment variables are configured for production:

| Variable | Description | Source |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | Hardcoded (Fly.io) |
| `VITE_FASTAPI_URL` | FastAPI backend URL | Hardcoded (Fly.io) |
| `VITE_FRONTEND_URL` | Frontend application URL | Hardcoded (Vercel) |
| `VITE_GOOGLE_CLIENT_ID` | Google OAuth client ID | Bitwarden |
| `VITE_APP_ENV` | Application environment | Hardcoded (production) |
| `SUPABASE_URL` | Supabase project URL | Bitwarden |
| `SUPABASE_ANON_KEY` | Supabase anonymous key | Bitwarden |

## Post-Deployment Verification

1. **Check Deployment Status**: Visit Vercel dashboard
2. **Test Application**: Access https://goblin-assistant.vercel.app
3. **Verify API Integration**: Test chat functionality
4. **Check Environment Variables**: Ensure all secrets are loaded

## Rollback

If deployment fails or issues arise:

```bash
# From the goblin-assistant directory
vercel rollback <deployment-url>
```

Or use the Vercel dashboard to rollback to a previous deployment.

## Integration with goblin-infra

This configuration is part of the centralized infrastructure management approach:

- **Secrets Management**: Integrated with Bitwarden (same as backend)
- **Deployment Scripts**: Located in infra repo for version control
- **Configuration**: Centralized Vercel config management
- **CI/CD Ready**: Scripts can be called from CI pipelines

## Dependencies

- **Vercel CLI**: `npm install -g vercel`
- **Bitwarden CLI**: `npm install -g @bitwarden/cli` (for full deployment)
- **Node.js/npm**: For building the frontend

## Troubleshooting

### Common Issues

1. **Bitwarden Authentication Failed**
   - Ensure `bw login` has been run recently
   - Check vault access permissions

2. **Vercel Deployment Failed**
   - Verify Vercel CLI authentication: `vercel login`
   - Check build logs for TypeScript/ESLint errors

3. **Environment Variables Not Set**
   - For automated deployment: Check Bitwarden secret names
   - For manual setup: Configure in Vercel dashboard

4. **API Connection Issues**
   - Verify backend is deployed and accessible
   - Check CORS configuration in `vercel.json`

### Logs and Debugging

```bash
# View recent deployments
vercel ls

# View deployment logs
vercel logs <deployment-url>

# Check environment variables
vercel env ls
```
