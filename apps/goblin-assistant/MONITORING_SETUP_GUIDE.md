# Goblin Assistant Monitoring Setup Guide

## 🎯 Monitoring Overview

Your Goblin Assistant application now has comprehensive monitoring set up with:

- ✅ **Frontend Monitoring**: Datadog RUM (Real User Monitoring)
- ✅ **Backend Health Checks**: Automated uptime monitoring
- ✅ **Deployment Analytics**: Vercel Analytics ready for activation
- ✅ **Error Tracking**: Configured for production error monitoring

## 📊 Current Monitoring Status

### Frontend (Netlify)

- **URL**: <https://goblin-assistant.netlify.app>
- **Datadog RUM**: Environment variables configured (needs your credentials)
- **Status**: Ready for Datadog setup

### Backend (Vercel)

- **URL**: <https://goblinos-assistant-backend-v2-gsjbxtrro-fuaadabdullahs-projects.vercel.app>
- **Health Endpoint**: `/health` (protected by Vercel authentication)
- **Analytics**: Ready for activation
- **Status**: Deployed and functional

## 🚀 Quick Setup Instructions

### 1. Set Up Datadog Monitoring

Run the automated setup script:

```bash
cd /Users/fuaadabdullah/ForgeMonorepo/goblin-assistant
./setup-datadog-monitoring.sh
```

This script will:
- Guide you through creating a Datadog RUM application
- Configure environment variables in Netlify
- Redeploy with monitoring enabled

### 2. Enable Vercel Analytics

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select your `goblinos-assistant-backend-v2` project
3. Navigate to **Settings** → **Analytics**
4. Click **Enable Analytics**
5. Choose your plan (free tier available)

### 3. Set Up Backend Health Monitoring

```bash

cd /Users/fuaadabdullah/ForgeMonorepo/goblin-assistant
./setup-backend-monitoring.sh
```

This creates:

- `uptime-monitor.sh` - Automated health check script
- `backend-uptime.log` - Health check logs

## 📈 What You'll Monitor

### Frontend Metrics (Datadog RUM)

- **User Sessions**: Track user behavior and session duration
- **Page Performance**: Core Web Vitals (LCP, FID, CLS)
- **Error Tracking**: JavaScript errors and failed API calls
- **User Journeys**: Click paths and user flows

### Backend Metrics (Vercel Analytics)

- **Request Volume**: API call frequency and patterns
- **Response Times**: Function execution performance
- **Error Rates**: Failed requests and exceptions
- **Geographic Data**: User location distribution

### Health Monitoring

- **Uptime Checks**: Automated health endpoint monitoring
- **Response Times**: Track API performance
- **Error Alerts**: Immediate notification of failures

## 🔧 Manual Configuration

### Datadog Dashboard Access

After setup, access your monitoring data at:

- **RUM Overview**: <https://app.datadoghq.com/rum/overview>
- **Error Explorer**: <https://app.datadoghq.com/rum/explorer>
- **Logs**: <https://app.datadoghq.com/logs>

### Vercel Analytics Dashboard

- **Analytics**: <https://vercel.com/dashboard> → Your Project → Analytics tab
- **Function Logs**: <https://vercel.com/dashboard> → Your Project → Functions
- **Deployment Logs**: <https://vercel.com/dashboard> → Your Project → Deployments

## ⚠️ Important Notes

### Vercel Deployment Protection

Your backend is protected by Vercel authentication. For testing:

1. **Temporary Disable**: Go to Vercel Dashboard → Settings → Deployment Protection → Disable
2. **Test Health Endpoint**: `curl <https://your-backend-url/health`>
3. **Re-enable Protection**: Turn protection back on after testing

### Datadog Credentials

Keep your Datadog Application ID and Client Token secure:

- Never commit to version control
- Rotate tokens periodically
- Use different tokens for staging/production

## 🧪 Testing Your Monitoring

### Test Frontend Monitoring

1. Visit <https://goblin-assistant.netlify.app>
2. Open browser DevTools (F12)
3. Go to Console tab
4. Run: `throw new Error('Test error for Datadog')`
5. Check Datadog RUM dashboard for the error

### Test Backend Monitoring

1. Temporarily disable Vercel protection
2. Run: `./uptime-monitor.sh`
3. Check Vercel Analytics for request metrics
4. Re-enable protection

## 📋 Maintenance Tasks

### Weekly

- [ ] Review error trends in Datadog
- [ ] Check Vercel Analytics for performance issues
- [ ] Verify uptime monitoring logs

### Monthly

- [ ] Update Datadog RUM version if needed
- [ ] Review monitoring costs
- [ ] Optimize alerts based on data patterns

## 🔗 Useful Links

- **Datadog RUM Documentation**: <https://docs.datadoghq.com/real_user_monitoring/>
- **Vercel Analytics**: <https://vercel.com/docs/analytics>
- **Monitoring Best Practices**: See `PRODUCTION_DATADOG_SETUP.md`

## 🎉 Next Steps

1. **Run Datadog Setup**: `./setup-datadog-monitoring.sh`
2. **Enable Vercel Analytics**: Via Vercel dashboard
3. **Test Monitoring**: Generate test errors and verify data appears
4. **Set Up Alerts**: Configure notifications for critical issues

Your application monitoring is now ready for production! 🚀
