# DuckDNS Setup Checklist for Goblin Assistant

## 📋 Pre-Setup (Do This First)

- [ ] Visit https://www.duckdns.org
- [ ] Sign in with Google, GitHub, Reddit, or Twitter account
- [ ] Click "add domain" and register your subdomain
  - Suggested: `goblinossistant` (closest to GoblinOSAssistant)
  - Alternatives: `goblinai`, `goblinos-assistant`, `goblin-chat`
- [ ] Copy your DuckDNS token (shown at top of page)
- [ ] Save token securely (you'll need it for setup)

## 🚀 Setup on Kamatera Server

### Phase 1: DuckDNS Configuration (5 minutes)

- [ ] SSH into Kamatera server: `ssh root@YOUR_SERVER_IP`
- [ ] Navigate to deployment directory:
  ```bash
  cd /root/ForgeMonorepo/deployments/kamatera
  ```
- [ ] Run DuckDNS setup script:
  ```bash
  export DUCKDNS_DOMAIN="goblinossistant"  # your subdomain
  export DUCKDNS_TOKEN="your-token-here"
  sudo -E ./setup-duckdns.sh
  ```
- [ ] Verify DuckDNS is updating:
  ```bash
  tail -f /var/log/duckdns.log
  ```
- [ ] Verify DNS resolution:
  ```bash
  dig goblinossistant.duckdns.org
  nslookup goblinossistant.duckdns.org
  ```

### Phase 2: SSL Certificate (3 minutes)

- [ ] Install Certbot:
  ```bash
  sudo apt-get update
  sudo apt-get install -y certbot python3-certbot-nginx
  ```
- [ ] Get SSL certificate:
  ```bash
  sudo certbot --nginx -d goblinossistant.duckdns.org
  ```
- [ ] During Certbot prompts:
  - [ ] Enter your email address
  - [ ] Agree to Terms of Service (Y)
  - [ ] Choose whether to share email (Y/N, your choice)
  - [ ] Redirect HTTP to HTTPS? Select 2 (redirect)
- [ ] Verify certificate:
  ```bash
  sudo certbot certificates
  ```
- [ ] Test auto-renewal:
  ```bash
  sudo certbot renew --dry-run
  ```

### Phase 3: Nginx Configuration (2 minutes)

- [ ] Copy nginx.conf to system:
  ```bash
  sudo cp nginx.conf /etc/nginx/nginx.conf
  ```
- [ ] Update domain in nginx.conf:
  ```bash
  sudo nano /etc/nginx/nginx.conf
  # Find: server_name goblinossistant.duckdns.org;
  # Replace with your domain if different
  ```
- [ ] Test nginx configuration:
  ```bash
  sudo nginx -t
  ```
- [ ] Reload nginx:
  ```bash
  sudo systemctl reload nginx
  ```

### Phase 4: Update Environment (1 minute)

- [ ] Edit .env file:
  ```bash
  nano /root/ForgeMonorepo/deployments/kamatera/.env
  ```
- [ ] Update these values:
  - [ ] `DUCKDNS_DOMAIN=goblinossistant` (your subdomain)
  - [ ] `DUCKDNS_TOKEN=your-actual-token`
  - [ ] `BACKEND_URL=https://goblinossistant.duckdns.org`
  - [ ] `FRONTEND_URL=https://goblinossistant.duckdns.org`
  - [ ] `API_BASE_URL=https://goblinossistant.duckdns.org/api`

### Phase 5: Deploy Services (2 minutes)

- [ ] Start all services with nginx:
  ```bash
  cd /root/ForgeMonorepo/deployments/kamatera
  docker-compose -f docker-compose.kamatera.yml up -d
  ```
- [ ] Check all containers are running:
  ```bash
  docker-compose -f docker-compose.kamatera.yml ps
  ```
- [ ] Expected containers:
  - [ ] goblin-nginx (healthy)
  - [ ] goblin-router (healthy)
  - [ ] goblin-redis (healthy)
  - [ ] goblin-postgres (healthy)
  - [ ] celery workers (running)

### Phase 6: Verification (2 minutes)

- [ ] Test HTTPS from server:
  ```bash
  curl -I https://goblinossistant.duckdns.org
  ```
  Expected: `HTTP/2 200` or similar
  
- [ ] Test health endpoint:
  ```bash
  curl https://goblinossistant.duckdns.org/health
  ```
  Expected: `{"status": "healthy"}` or similar
  
- [ ] Test API endpoint:
  ```bash
  curl https://goblinossistant.duckdns.org/api/health
  ```
  
- [ ] Test from browser:
  - [ ] Open https://goblinossistant.duckdns.org
  - [ ] Verify green padlock (SSL valid)
  - [ ] Test chat functionality
  - [ ] Check browser console (should be no errors)

### Phase 7: Firewall Configuration (1 minute)

- [ ] Ensure firewall allows HTTPS:
  ```bash
  sudo ufw status
  sudo ufw allow 80/tcp
  sudo ufw allow 443/tcp
  ```
- [ ] Block direct access to internal ports:
  ```bash
  sudo ufw deny 8000/tcp
  sudo ufw deny 3000/tcp
  sudo ufw deny 6379/tcp
  sudo ufw deny 5432/tcp
  ```

## 🔍 Post-Setup Monitoring

### Daily Checks

- [ ] Monitor DuckDNS updates:
  ```bash
  tail -f /var/log/duckdns.log
  ```
- [ ] Check nginx logs:
  ```bash
  tail -f /var/log/nginx/access.log
  tail -f /var/log/nginx/error.log
  ```
- [ ] Verify services are healthy:
  ```bash
  docker-compose -f docker-compose.kamatera.yml ps
  ```

### Weekly Checks

- [ ] Check SSL certificate expiry:
  ```bash
  sudo certbot certificates
  ```
- [ ] Test SSL renewal:
  ```bash
  sudo certbot renew --dry-run
  ```
- [ ] Review security logs
- [ ] Check disk usage

## ⚠️ Troubleshooting

### DuckDNS Not Updating

- [ ] Check cron job:
  ```bash
  crontab -l | grep duckdns
  ```
- [ ] Manually trigger update:
  ```bash
  sudo /usr/local/bin/duckdns-update.sh
  ```
- [ ] Verify token is correct on duckdns.org

### SSL Certificate Errors

- [ ] Test nginx config:
  ```bash
  sudo nginx -t
  ```
- [ ] Check certificate paths:
  ```bash
  ls -la /etc/letsencrypt/live/goblinossistant.duckdns.org/
  ```
- [ ] Force certificate renewal:
  ```bash
  sudo certbot renew --force-renewal
  ```

### Can't Access Website

- [ ] Check nginx is running:
  ```bash
  sudo systemctl status nginx
  ```
- [ ] Check docker containers:
  ```bash
  docker-compose ps
  ```
- [ ] Check firewall:
  ```bash
  sudo ufw status
  ```
- [ ] Test DNS:
  ```bash
  dig goblinossistant.duckdns.org
  ```

### Docker Containers Not Starting

- [ ] Check logs:
  ```bash
  docker-compose -f docker-compose.kamatera.yml logs
  ```
- [ ] Restart services:
  ```bash
  docker-compose -f docker-compose.kamatera.yml restart
  ```
- [ ] Check disk space:
  ```bash
  df -h
  ```

## ✅ Success Criteria

You're done when:

- [x] DuckDNS updates automatically every 5 minutes
- [x] SSL certificate is valid and auto-renews
- [x] Website accessible at https://your-domain.duckdns.org
- [x] Green padlock in browser (valid SSL)
- [x] API endpoints responding correctly
- [x] Chat functionality working
- [x] No errors in browser console
- [x] All docker containers healthy
- [x] Nginx logs show no errors
- [x] Firewall configured properly

## 🎉 Final Result

Your Goblin Assistant is now publicly accessible at:

**https://goblinossistant.duckdns.org**

With:
- ✅ Free domain (DuckDNS)
- ✅ Free SSL certificate (Let's Encrypt)
- ✅ Auto-renewal (Certbot)
- ✅ Auto IP updates (DuckDNS cron)
- ✅ Rate limiting (nginx)
- ✅ Security headers (nginx)
- ✅ Production-ready configuration

## 📚 Documentation

For detailed information, see:
- [DUCKDNS_SETUP.md](./DUCKDNS_SETUP.md) - Complete setup guide
- [DUCKDNS_SUMMARY.md](./DUCKDNS_SUMMARY.md) - Quick summary
- [README.md](./README.md) - Kamatera deployment overview

## 💡 Tips

1. **Bookmark your domain** - Save https://goblinossistant.duckdns.org
2. **Monitor logs** - Set up log rotation for /var/log/duckdns.log
3. **Test regularly** - Weekly health checks recommended
4. **Keep token secret** - Never commit DuckDNS token to git
5. **Consider upgrade** - If traffic grows, consider custom .org domain

---

**Estimated Total Time:** 15-20 minutes
**Cost:** $0 (completely free!)
**Difficulty:** Easy (copy-paste commands)
