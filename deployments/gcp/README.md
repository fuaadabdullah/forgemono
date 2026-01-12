# GCP Deployment Directory

This directory contains deployment configurations and scripts for running **Goblin Assistant** on **Google Cloud Platform (GCP)**.

## 📋 Overview

The customer-facing Goblin Assistant is currently deployed on GCP with:

- **Platform**: Google Cloud Platform (GCP)
- **LLM Infrastructure**:
  - Ollama Server: `http://34.60.255.199:11434`
  - llama.cpp Server: `http://34.132.226.143:8000`
- **Public Domain**: DuckDNS (free subdomain)
- **SSL**: Let's Encrypt (free HTTPS)

## 🚀 Quick Start

### 1. Setup DuckDNS (Public Domain)

Give your customer-facing Goblin Assistant a professional domain:

```bash
# SSH to GCP VM
gcloud compute ssh your-instance-name --zone=your-zone

# Navigate to deployment directory
cd /root/ForgeMonorepo/deployments/gcp

# Run DuckDNS setup
chmod +x setup-duckdns-gcp.sh
sudo ./setup-duckdns-gcp.sh
```

**Result**: Your service will be accessible at `https://goblinossistant.duckdns.org`

### 2. Configure GCP Firewall

```bash
# Allow HTTPS traffic
gcloud compute firewall-rules create allow-https \
  --allow tcp:443 \
  --source-ranges 0.0.0.0/0 \
  --target-tags https-server

# Allow HTTP (for SSL verification)
gcloud compute firewall-rules create allow-http \
  --allow tcp:80 \
  --source-ranges 0.0.0.0/0 \
  --target-tags http-server
```

### 3. Deploy Services

```bash
cd /root/ForgeMonorepo/apps/goblin-assistant
./deploy-gcp-chat.sh production
```

## 📁 Files

### Configuration Scripts

- **setup-duckdns-gcp.sh** - DuckDNS dynamic DNS setup for GCP
  - Detects GCP public IP automatically
  - Configures auto-updates every 5 minutes
  - Creates environment variables

### Documentation

- **DUCKDNS_SETUP_GCP.md** - Complete DuckDNS setup guide
  - Customer-facing deployment instructions
  - GCP firewall configuration
  - SSL certificate setup
  - Troubleshooting guide

## 🌐 Public Access

After setup, your Goblin Assistant will be available at:

**https://goblinossistant.duckdns.org**

(or your chosen subdomain)

## 🏗️ Architecture

```
Internet Users
      ↓
DuckDNS (goblinossistant.duckdns.org)
      ↓
GCP VM (Public IP)
      ↓
Nginx (SSL/HTTPS)
      ├── Frontend (Next.js)
      ├── Backend (FastAPI)
      └── LLM Services
          ├── Ollama (34.60.255.199:11434)
          └── llama.cpp (34.132.226.143:8000)
```

## 📊 Cost Breakdown

| Service | Monthly Cost |
|---------|--------------|
| DuckDNS Domain | $0 (free) |
| SSL Certificate | $0 (Let's Encrypt) |
| GCP VM (e2-medium) | ~$25-40 |
| GCP Egress | ~$0.12/GB |
| **Total** | **~$25-50/month** |

Much cheaper than:
- Custom .org domain: +$1-2/month
- Managed DNS (Route53): +$0.50/month
- Managed SSL: +$5-10/month

## 🔧 Maintenance

### Monitor DuckDNS Updates

```bash
# View update log
tail -f /var/log/duckdns.log

# Manually trigger update
sudo /usr/local/bin/duckdns-update.sh
```

### Check SSL Certificate

```bash
# View certificate info
sudo certbot certificates

# Test auto-renewal
sudo certbot renew --dry-run
```

### Monitor GCP Resources

```bash
# Check VM status
gcloud compute instances list

# View firewall rules
gcloud compute firewall-rules list

# Check logs
gcloud logging read "resource.type=gce_instance"
```

## 🚨 Troubleshooting

### DuckDNS Not Updating

```bash
# Check cron job
crontab -l | grep duckdns

# Test IP detection
curl -H "Metadata-Flavor: Google" \
  http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip
```

### SSL Issues

```bash
# Test nginx config
sudo nginx -t

# Check certificate expiry
sudo certbot certificates

# View nginx logs
sudo tail -f /var/log/nginx/error.log
```

### Firewall Issues

```bash
# List rules
gcloud compute firewall-rules list

# Test connectivity
curl -v https://goblinossistant.duckdns.org/health
```

## 📝 Migration Notes

### From Kamatera to GCP

The Goblin Assistant was **temporarily migrated from Kamatera to GCP**. Key changes:

- **LLM Endpoints**: Now using GCP VMs for Ollama and llama.cpp
- **Networking**: GCP firewall rules instead of UFW
- **IP Detection**: Uses GCP metadata service
- **Monitoring**: GCP Cloud Monitoring instead of custom scripts

**Kamatera deployment files** are still available in `/deployments/kamatera/` for future reference.

## 🔄 Future Plans

### Option 1: Stay on GCP

- Scale with GCP managed services
- Use Cloud Load Balancer
- Implement Cloud CDN
- Enable Cloud Armor (DDoS protection)

### Option 2: Return to Kamatera

- Lower costs (~$15/month vs $25-50)
- More control over infrastructure
- Use existing Kamatera deployment scripts

### Option 3: Upgrade Domain

- Purchase `goblinossistant.org` (~$12/year)
- Use Google Domains or Namecheap
- Keep DuckDNS as backup/staging

## 📚 Additional Resources

- [GCP Compute Documentation](https://cloud.google.com/compute/docs)
- [DuckDNS FAQ](https://www.duckdns.org/faqs.jsp)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs)
- [Nginx Configuration Guide](https://nginx.org/en/docs/)

## 🎯 Production Checklist

Before customer launch:

- [ ] DuckDNS configured and updating
- [ ] SSL certificate installed and auto-renewing
- [ ] GCP firewall rules configured
- [ ] Health checks passing
- [ ] Monitoring and alerts set up
- [ ] Rate limiting configured
- [ ] CORS properly configured
- [ ] API keys secured
- [ ] Backup strategy implemented
- [ ] Load testing completed
- [ ] Customer documentation prepared

## 🆘 Support

For deployment issues:

1. Check logs: `/var/log/duckdns.log`, `/var/log/nginx/error.log`
2. Verify GCP firewall rules
3. Test DNS resolution: `dig goblinossistant.duckdns.org`
4. Check SSL certificate: `sudo certbot certificates`

---

**Customer-Facing Domain**: https://goblinossistant.duckdns.org

**Platform**: Google Cloud Platform (GCP)

**Status**: Production-Ready 🚀
