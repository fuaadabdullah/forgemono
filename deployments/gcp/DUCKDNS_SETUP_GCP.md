# DuckDNS Setup for Customer-Facing Goblin Assistant (GCP)

## Overview

This guide configures a **free public domain** for the customer-facing Goblin Assistant deployment on **Google Cloud Platform (GCP)**. Since the infrastructure was temporarily moved from Kamatera to GCP, this setup ensures your users can access the service at a memorable, professional domain.

## Why DuckDNS for Customer-Facing Service?

- ✅ **100% Free** - No costs for domain
- ✅ **Quick Setup** - 10 minutes to go live
- ✅ **Professional** - `goblinossistant.duckdns.org` instead of IP
- ✅ **SSL Ready** - Works with Let's Encrypt for HTTPS
- ✅ **Auto-Updates** - Handles GCP IP changes automatically
- ✅ **Production-Ready** - Used by thousands of services

## Current GCP Infrastructure

Your Goblin Assistant is currently deployed on:

- **Platform**: Google Cloud Platform (GCP)
- **Ollama Server**: `http://34.60.255.199:11434`
- **llama.cpp Server**: `http://34.132.226.143:8000`
- **Deployment**: Customer-facing production service

## Recommended Domain Options

For a customer-facing service, choose a professional, memorable domain:

### Top Recommendations:

1. **goblinossistant.duckdns.org** (closest to GoblinOSAssistant)
2. **goblinai.duckdns.org** (short and tech-focused)
3. **goblin-chat.duckdns.org** (descriptive)
4. **goblinhelp.duckdns.org** (friendly, support-focused)

**Note:** While `.org` domains like `GoblinOSAssistant.org` are more professional, they cost $10-15/year. DuckDNS gives you a free subdomain instantly, perfect for MVP/beta launches!

## Setup Instructions

### Step 1: Register DuckDNS Account (2 minutes)

1. Visit [https://www.duckdns.org](https://www.duckdns.org)
2. Sign in with Google, GitHub, Reddit, or Twitter
3. Click "add domain" and register: `goblinossistant` (or your choice)
4. Copy your **token** from the top of the page (save it securely)

### Step 2: Run Setup on GCP VM (5 minutes)

SSH into your GCP VM instance:

```bash
# SSH to GCP VM
gcloud compute ssh your-instance-name --zone=your-zone

# Or use SSH key
ssh -i ~/.ssh/gcp-key user@YOUR_GCP_VM_IP

# Navigate to deployment directory
cd /root/ForgeMonorepo/deployments/gcp

# Make script executable
chmod +x setup-duckdns-gcp.sh

# Run setup (will prompt for token and domain)
sudo ./setup-duckdns-gcp.sh
```

Or set environment variables first:

```bash
export DUCKDNS_DOMAIN="goblinossistant"
export DUCKDNS_TOKEN="your-token-from-duckdns-org"
sudo -E ./setup-duckdns-gcp.sh
```

### Step 3: Configure GCP Firewall (2 minutes)

Allow HTTPS traffic to your VM:

```bash
# Allow HTTPS (port 443)
gcloud compute firewall-rules create allow-https \
  --allow tcp:443 \
  --source-ranges 0.0.0.0/0 \
  --target-tags https-server

# Allow HTTP (port 80 for Let's Encrypt verification)
gcloud compute firewall-rules create allow-http \
  --allow tcp:80 \
  --source-ranges 0.0.0.0/0 \
  --target-tags http-server

# Verify firewall rules
gcloud compute firewall-rules list | grep allow-http
```

Or use GCP Console:
1. Go to [VPC Network > Firewall](https://console.cloud.google.com/networking/firewalls)
2. Click "Create Firewall Rule"
3. Name: `allow-https`
4. Targets: All instances in the network (or specific tags)
5. Source IP ranges: `0.0.0.0/0`
6. Protocols and ports: `tcp:443`
7. Click "Create"

### Step 4: Install SSL Certificate (3 minutes)

```bash
# Install Certbot
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d goblinossistant.duckdns.org

# Follow prompts:
# - Enter email address (for renewal notifications)
# - Agree to Terms of Service (Y)
# - Share email with EFF? (Y/N, your choice)
# - Redirect HTTP to HTTPS? Select 2 (recommended)
```

### Step 5: Update Environment Variables (1 minute)

```bash
# Edit your .env file
nano /root/ForgeMonorepo/apps/goblin-assistant/.env

# Update these values:
BACKEND_URL=https://goblinossistant.duckdns.org
FRONTEND_URL=https://goblinossistant.duckdns.org
API_BASE_URL=https://goblinossistant.duckdns.org/api

# Keep existing GCP endpoints
OLLAMA_GCP_URL=http://34.60.255.199:11434
LLAMACPP_GCP_URL=http://34.132.226.143:8000
```

### Step 6: Deploy Services (2 minutes)

```bash
cd /root/ForgeMonorepo/apps/goblin-assistant

# Start all services
docker-compose up -d

# Or use the deployment script
./deploy-gcp-chat.sh production
```

### Step 7: Verify Deployment (2 minutes)

```bash
# Test HTTPS from server
curl -I https://goblinossistant.duckdns.org

# Test health endpoint
curl https://goblinossistant.duckdns.org/health

# Test API endpoint
curl https://goblinossistant.duckdns.org/api/health

# Check DuckDNS updates
tail -f /var/log/duckdns.log

# Verify DNS resolution
dig goblinossistant.duckdns.org
```

Test from browser:
1. Visit `https://goblinossistant.duckdns.org`
2. Verify green padlock (SSL valid)
3. Test chat functionality
4. Check browser console (should be no errors)

## Architecture

```
┌─────────────────────────────────────────────────┐
│              Customer Users                      │
│         (Access via Web/Mobile)                  │
└────────────────────┬────────────────────────────┘
                     │
                     ↓
        ┌────────────────────────┐
        │   DuckDNS Service      │
        │  (Free DNS Provider)   │
        │                        │
        │  goblinossistant       │
        │    .duckdns.org        │
        └────────┬───────────────┘
                 │
                 ↓
    ┌────────────────────────────┐
    │   Google Cloud Platform    │
    │   GCP VM Instance          │
    │   Public IP (Dynamic)      │
    └────────┬───────────────────┘
             │
             ↓
    ┌────────────────────────────┐
    │   Nginx (Ports 80/443)     │
    │   - SSL Termination        │
    │   - Rate Limiting          │
    │   - Reverse Proxy          │
    └────────┬───────────────────┘
             │
      ┌──────┴──────┬─────────────┐
      │             │             │
      ↓             ↓             ↓
┌──────────┐  ┌─────────┐  ┌────────────┐
│ Frontend │  │ Backend │  │  LLM       │
│  :3000   │  │  :8000  │  │  Services  │
│  Next.js │  │ FastAPI │  │  (GCP)     │
└──────────┘  └─────────┘  └────────────┘
                                │
                         ┌──────┴──────┐
                         │             │
                         ↓             ↓
                   ┌──────────┐  ┌───────────┐
                   │  Ollama  │  │ llama.cpp │
                   │  :11434  │  │   :8000   │
                   │ GCP VM 1 │  │ GCP VM 2  │
                   └──────────┘  └───────────┘
```

## GCP-Specific Considerations

### IP Address Changes

GCP VMs can have their IPs changed during:
- VM restarts
- Region migrations
- Maintenance windows

**DuckDNS handles this automatically** with the cron job updating every 5 minutes.

### Firewall Configuration

Ensure these ports are open:
- **80** (HTTP) - For Let's Encrypt verification
- **443** (HTTPS) - For customer traffic
- **8000** (Internal) - Backend API (internal only)
- **11434** (Internal) - Ollama (internal only)

### Health Monitoring

Set up GCP monitoring:

```bash
# Enable Cloud Monitoring
gcloud services enable monitoring.googleapis.com

# Create uptime check
gcloud monitoring uptime create goblin-assistant \
  --resource-type=uptime-url \
  --host=goblinossistant.duckdns.org \
  --path=/health
```

### Cost Optimization

- **DuckDNS**: $0/month (free)
- **SSL**: $0/month (Let's Encrypt)
- **GCP VM**: ~$20-50/month (e2-medium)
- **GCP Egress**: ~$0.12/GB

**Total**: Much cheaper than purchasing custom domain + managed DNS!

## Troubleshooting

### DuckDNS Not Updating

```bash
# Check cron job
crontab -l | grep duckdns

# Check log
tail -f /var/log/duckdns.log

# Manually trigger update
sudo /usr/local/bin/duckdns-update.sh

# Verify IP on DuckDNS
nslookup goblinossistant.duckdns.org
```

### GCP Firewall Issues

```bash
# List firewall rules
gcloud compute firewall-rules list

# Check VM tags
gcloud compute instances describe your-instance-name \
  --zone=your-zone \
  --format="get(tags.items)"

# Test connectivity
curl -v https://goblinossistant.duckdns.org
```

### SSL Certificate Errors

```bash
# Test nginx config
sudo nginx -t

# Check certificate
sudo certbot certificates

# Force renewal
sudo certbot renew --force-renewal

# Check logs
sudo tail -f /var/log/letsencrypt/letsencrypt.log
```

### GCP Metadata Service

If IP detection fails:

```bash
# Test metadata service
curl -H "Metadata-Flavor: Google" \
  http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip

# Check if metadata service is enabled
gcloud compute instances describe your-instance-name \
  --zone=your-zone \
  --format="get(metadata)"
```

## Production Checklist

Before going live with customers:

- [ ] DuckDNS configured and updating
- [ ] SSL certificate valid and auto-renewing
- [ ] GCP firewall rules configured
- [ ] Health endpoints responding
- [ ] Rate limiting configured
- [ ] Monitoring and alerts set up
- [ ] Backup strategy in place
- [ ] Error tracking (Sentry/Datadog) configured
- [ ] API keys rotated and secured
- [ ] CORS configured for frontend domain
- [ ] Load testing completed
- [ ] Documentation updated with new domain

## Upgrading to Custom Domain

When you're ready for a custom `.org` domain:

1. **Purchase domain** (~$10-15/year) from Namecheap, GoDaddy, or Google Domains
2. **Update DNS**:
   ```bash
   # Point A record to your GCP VM IP
   @ A 34.60.255.199 (your GCP IP)
   www CNAME goblinossistant.org
   ```
3. **Update SSL certificate**:
   ```bash
   sudo certbot --nginx -d goblinossistant.org -d www.goblinossistant.org
   ```
4. **Keep DuckDNS** as backup/staging domain

## Support Resources

- **DuckDNS**: https://www.duckdns.org/faqs.jsp
- **GCP Docs**: https://cloud.google.com/compute/docs
- **Let's Encrypt**: https://letsencrypt.org/docs
- **Certbot**: https://certbot.eff.org/instructions

## Files Created

- `/deployments/gcp/setup-duckdns-gcp.sh` - Automated setup script
- `/usr/local/bin/duckdns-update.sh` - Auto-update script (on GCP VM)
- `/var/log/duckdns.log` - Update log (on GCP VM)
- `/root/goblin-assistant/.env.duckdns` - Environment variables (on GCP VM)

## Next Steps

1. ✅ Run setup script on GCP VM
2. ✅ Configure GCP firewall
3. ✅ Install SSL certificate
4. ✅ Update environment variables
5. ✅ Deploy services
6. ✅ Test customer access
7. 📱 Update mobile apps with new domain
8. 📝 Announce new domain to users
9. 🔐 Set up monitoring and alerts

---

**Your customer-facing Goblin Assistant will be live at:**

## 🌐 https://goblinossistant.duckdns.org

**Cost**: $0/year | **Setup Time**: 15 minutes | **Professional**: ✅
