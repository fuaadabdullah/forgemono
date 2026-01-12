# 🚀 GoblinOS Assistant - DuckDNS Deployment Guide

**Domain:** https://goblinosassistant.duckdns.org  
**Account:** fuaadabdullah@gmail.com  
**Token:** 59be274c-ca62-4e86-b671-035cee6f5bad  
**Created:** January 12, 2026

---

## ✅ What's Already Done

- [x] DuckDNS domain registered: `goblinosassistant.duckdns.org`
- [x] Token generated and stored
- [x] Deployment scripts created with your credentials
- [x] Environment files configured

---

## 🎯 Quick Deployment (15 minutes)

### Step 1: Connect to Your GCP VM

```bash
# From your local machine
gcloud compute ssh goblin-assistant-vm \
  --project=goblin-assistant-gcp \
  --zone=us-central1-a
```

**Or manually SSH:**
```bash
ssh -i ~/.ssh/gcp-key username@<GCP_VM_IP>
```

### Step 2: Copy Deployment Files to GCP VM

**Option A: Git Clone (Recommended)**
```bash
# On GCP VM
cd /root
git clone https://github.com/fuaadabdullah/ForgeMonorepo.git
cd ForgeMonorepo
git checkout feat/chat-kamatera-integration
cd deployments/gcp
```

**Option B: SCP Copy (if files not in git yet)**
```bash
# From your local machine
gcloud compute scp \
  --recurse \
  ./deployments/gcp \
  goblin-assistant-vm:/root/goblin-deployment \
  --project=goblin-assistant-gcp \
  --zone=us-central1-a
```

### Step 3: Run Deployment Script

```bash
# On GCP VM
cd /root/ForgeMonorepo/deployments/gcp
sudo ./deploy-with-duckdns.sh
```

The script will:
1. ✅ Detect your GCP external IP
2. ✅ Update DuckDNS with your IP
3. ✅ Setup auto-updates (every 5 minutes)
4. ✅ Install nginx + certbot
5. ✅ Configure GCP firewall rules
6. ✅ Request SSL certificate (Let's Encrypt)
7. ✅ Setup SSL auto-renewal
8. ✅ Test HTTPS access

**Total time:** ~15 minutes

---

## 🔥 One-Line Deployment

If you trust the automation:

```bash
# On GCP VM (as root)
curl -fsSL https://raw.githubusercontent.com/fuaadabdullah/ForgeMonorepo/feat/chat-kamatera-integration/deployments/gcp/deploy-with-duckdns.sh | sudo bash
```

---

## 🔧 Manual Steps (if needed)

### Configure GCP Firewall

**From your local machine:**

```bash
# Allow HTTP (port 80)
gcloud compute firewall-rules create allow-http \
  --allow tcp:80 \
  --target-tags=goblin-assistant \
  --project=goblin-assistant-gcp

# Allow HTTPS (port 443)
gcloud compute firewall-rules create allow-https \
  --allow tcp:443 \
  --target-tags=goblin-assistant \
  --project=goblin-assistant-gcp

# Verify rules
gcloud compute firewall-rules list --project=goblin-assistant-gcp
```

**Or via GCP Console:**
1. Go to [VPC Network > Firewall](https://console.cloud.google.com/networking/firewalls)
2. Create rule for TCP:80 (HTTP)
3. Create rule for TCP:443 (HTTPS)

### Manual SSL Installation

```bash
# On GCP VM
sudo certbot --nginx \
  --email fuaadabdullah@gmail.com \
  --domains goblinosassistant.duckdns.org \
  --agree-tos \
  --non-interactive \
  --redirect
```

---

## 📊 Verify Deployment

### Check DuckDNS Update

```bash
# From anywhere
curl "https://www.duckdns.org/update?domains=goblinosassistant&token=59be274c-ca62-4e86-b671-035cee6f5bad&ip="
# Should return: OK
```

### Check DNS Resolution

```bash
# From anywhere
dig +short goblinosassistant.duckdns.org
# Should show your GCP VM IP
```

### Check SSL Certificate

```bash
# On GCP VM
sudo certbot certificates
```

```bash
# From anywhere
curl -I https://goblinosassistant.duckdns.org
# Should return 200 with valid SSL
```

### Check Auto-Update Cron

```bash
# On GCP VM
crontab -l | grep duckdns
# Should show: */5 * * * * curl ...
```

---

## 🔐 Your Credentials

**IMPORTANT:** These credentials are already embedded in the deployment scripts.

```bash
# DuckDNS Configuration
DUCKDNS_DOMAIN=goblinosassistant
DUCKDNS_TOKEN=59be274c-ca62-4e86-b671-035cee6f5bad

# Public URL
PUBLIC_URL=https://goblinosassistant.duckdns.org

# SSL Email
SSL_EMAIL=fuaadabdullah@gmail.com
```

---

## 🎯 Next Steps After Deployment

### 1. Deploy Your GoblinOS Services

```bash
# On GCP VM
cd /root/ForgeMonorepo/apps/goblin-assistant
docker-compose up -d
```

### 2. Update Nginx to Proxy Your Services

Edit `/etc/nginx/sites-available/goblin-assistant`:

```nginx
upstream goblin_backend {
    server localhost:8000;
}

upstream goblin_frontend {
    server localhost:3000;
}

server {
    listen 443 ssl http2;
    server_name goblinosassistant.duckdns.org;
    
    ssl_certificate /etc/letsencrypt/live/goblinosassistant.duckdns.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/goblinosassistant.duckdns.org/privkey.pem;
    
    # Frontend
    location / {
        proxy_pass http://goblin_frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://goblin_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name goblinosassistant.duckdns.org;
    return 301 https://$server_name$request_uri;
}
```

```bash
# Test and reload
sudo nginx -t
sudo systemctl reload nginx
```

### 3. Test Your Application

```bash
# Test frontend
curl https://goblinosassistant.duckdns.org

# Test backend API
curl https://goblinosassistant.duckdns.org/api/health
```

---

## 🐛 Troubleshooting

### DNS Not Resolving

```bash
# Manually update DuckDNS
curl "https://www.duckdns.org/update?domains=goblinosassistant&token=59be274c-ca62-4e86-b671-035cee6f5bad&ip=$(curl -s https://api.ipify.org)"

# Wait 2-5 minutes for propagation
# Test resolution
dig +short goblinosassistant.duckdns.org @8.8.8.8
```

### SSL Certificate Failed

```bash
# Check nginx is running
sudo systemctl status nginx

# Check port 80 is open
sudo netstat -tlnp | grep :80

# Try manual certbot
sudo certbot --nginx -d goblinosassistant.duckdns.org --email fuaadabdullah@gmail.com
```

### Firewall Issues

```bash
# Check GCP firewall rules
gcloud compute firewall-rules list --project=goblin-assistant-gcp

# Test from external
telnet <your-gcp-ip> 80
telnet <your-gcp-ip> 443
```

### Cron Not Updating IP

```bash
# Check cron logs
sudo tail -f /var/log/syslog | grep CRON

# Manually test update
curl "https://www.duckdns.org/update?domains=goblinosassistant&token=59be274c-ca62-4e86-b671-035cee6f5bad&ip="

# Re-add cron job
(crontab -l 2>/dev/null | grep -v "duckdns.org" ; echo "*/5 * * * * curl -s \"https://www.duckdns.org/update?domains=goblinosassistant&token=59be274c-ca62-4e86-b671-035cee6f5bad&ip=\" > /dev/null 2>&1") | crontab -
```

---

## 📋 Useful Commands

```bash
# Check nginx status
sudo systemctl status nginx

# Check SSL certificates
sudo certbot certificates

# Check cron jobs
crontab -l

# View nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Test SSL renewal
sudo certbot renew --dry-run

# Restart nginx
sudo systemctl restart nginx

# View all open ports
sudo netstat -tlnp
```

---

## 💰 Cost Breakdown

| Item | Cost |
|------|------|
| DuckDNS Domain | **$0/year** ✅ |
| SSL Certificate | **$0/year** ✅ |
| GCP VM (e2-micro) | ~$7/month |
| GCP Storage (20GB) | ~$0.80/month |
| GCP Networking | ~$5/month |
| **Total** | **~$13/month** |

**Savings:** $216/year vs paid .com domain + SSL certificate!

---

## 🎉 Success!

Once deployed, your customer-facing GoblinOS Assistant will be live at:

### https://goblinosassistant.duckdns.org

✅ **Free domain**  
✅ **Valid SSL certificate**  
✅ **Auto-updating IP**  
✅ **Production-ready**  
✅ **Customer-facing**  

---

## 📞 Support

- **DuckDNS Dashboard:** https://www.duckdns.org/domains
- **Let's Encrypt Status:** https://letsencrypt.status.io/
- **GCP Console:** https://console.cloud.google.com/

**Account:** fuaadabdullah@gmail.com  
**Domain:** goblinosassistant  
**Registered:** January 12, 2026

---

**Ready to deploy? SSH into your GCP VM and run the script!** 🚀
