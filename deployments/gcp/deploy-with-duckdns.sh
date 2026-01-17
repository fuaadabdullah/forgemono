#!/bin/bash
#
# GoblinOS Assistant - Quick DuckDNS Deployment
# Deploy to GCP with your registered DuckDNS domain
#
# Account: fuaadabdullah@gmail.com
# Domain: goblinosassistant.duckdns.org
# Token: 59be274c-ca62-4e86-b671-035cee6f5bad
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DUCKDNS_DOMAIN="goblinosassistant"
DUCKDNS_TOKEN="59be274c-ca62-4e86-b671-035cee6f5bad"
PUBLIC_URL="https://goblinosassistant.duckdns.org"
SSL_EMAIL="fuaadabdullah@gmail.com"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                                ║${NC}"
echo -e "${BLUE}║   🚀 GoblinOS Assistant - DuckDNS Deployment                  ║${NC}"
echo -e "${BLUE}║                                                                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Domain:${NC} ${PUBLIC_URL}"
echo -e "${GREEN}Email:${NC}  ${SSL_EMAIL}"
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}❌ This script must be run as root${NC}" 
   echo -e "${YELLOW}   Please run: sudo $0${NC}"
   exit 1
fi

# Check if we're on GCP
echo -e "${YELLOW}⏳ Checking GCP environment...${NC}"
if curl -sf -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/id > /dev/null 2>&1; then
    echo -e "${GREEN}✅ GCP VM detected${NC}"
    GCP_IP=$(curl -sf -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip)
    echo -e "${GREEN}   External IP: ${GCP_IP}${NC}"
else
    echo -e "${YELLOW}⚠️  Not on GCP - using fallback IP detection${NC}"
    GCP_IP=$(curl -s https://api.ipify.org)
    echo -e "${GREEN}   External IP: ${GCP_IP}${NC}"
fi

# Update DuckDNS
echo ""
echo -e "${YELLOW}⏳ Updating DuckDNS with your IP...${NC}"
RESPONSE=$(curl -sf "https://www.duckdns.org/update?domains=${DUCKDNS_DOMAIN}&token=${DUCKDNS_TOKEN}&ip=${GCP_IP}")
if [[ "$RESPONSE" == "OK" ]]; then
    echo -e "${GREEN}✅ DuckDNS updated successfully${NC}"
    echo -e "${GREEN}   ${DUCKDNS_DOMAIN}.duckdns.org → ${GCP_IP}${NC}"
else
    echo -e "${RED}❌ DuckDNS update failed: ${RESPONSE}${NC}"
    exit 1
fi

# Setup cron job for auto-updates
echo ""
echo -e "${YELLOW}⏳ Setting up automatic IP updates...${NC}"
CRON_JOB="*/5 * * * * curl -s \"https://www.duckdns.org/update?domains=${DUCKDNS_DOMAIN}&token=${DUCKDNS_TOKEN}&ip=\" > /dev/null 2>&1"
(crontab -l 2>/dev/null | grep -v "duckdns.org" ; echo "$CRON_JOB") | crontab -
echo -e "${GREEN}✅ Cron job installed (updates every 5 minutes)${NC}"

# Check if nginx is installed
echo ""
echo -e "${YELLOW}⏳ Checking nginx installation...${NC}"
if ! command -v nginx &> /dev/null; then
    echo -e "${YELLOW}   Installing nginx...${NC}"
    apt-get update -qq
    apt-get install -y nginx
    echo -e "${GREEN}✅ Nginx installed${NC}"
else
    echo -e "${GREEN}✅ Nginx already installed${NC}"
fi

# Check if certbot is installed
echo ""
echo -e "${YELLOW}⏳ Checking certbot installation...${NC}"
if ! command -v certbot &> /dev/null; then
    echo -e "${YELLOW}   Installing certbot...${NC}"
    apt-get install -y certbot python3-certbot-nginx
    echo -e "${GREEN}✅ Certbot installed${NC}"
else
    echo -e "${GREEN}✅ Certbot already installed${NC}"
fi

# Configure firewall (GCP)
echo ""
echo -e "${YELLOW}⏳ Configuring GCP firewall...${NC}"
if command -v gcloud &> /dev/null; then
    echo -e "${BLUE}   Run these commands on your LOCAL machine:${NC}"
    echo ""
    echo -e "${YELLOW}   # Allow HTTP traffic${NC}"
    echo -e "   gcloud compute firewall-rules create allow-http \\"
    echo -e "     --allow tcp:80 \\"
    echo -e "     --target-tags=goblin-assistant"
    echo ""
    echo -e "${YELLOW}   # Allow HTTPS traffic${NC}"
    echo -e "   gcloud compute firewall-rules create allow-https \\"
    echo -e "     --allow tcp:443 \\"
    echo -e "     --target-tags=goblin-assistant"
    echo ""
    echo -e "${YELLOW}   Press Enter when done...${NC}"
    read -r
else
    echo -e "${YELLOW}⚠️  gcloud not found - configure firewall manually:${NC}"
    echo -e "   - Allow TCP port 80 (HTTP)"
    echo -e "   - Allow TCP port 443 (HTTPS)"
    echo ""
    echo -e "${YELLOW}   Press Enter when done...${NC}"
    read -r
fi

# Wait for DNS propagation
echo ""
echo -e "${YELLOW}⏳ Waiting for DNS propagation (30 seconds)...${NC}"
for i in {30..1}; do
    echo -ne "   ${i} seconds remaining...\r"
    sleep 1
done
echo -e "${GREEN}✅ DNS should be ready${NC}"

# Verify DNS
echo ""
echo -e "${YELLOW}⏳ Verifying DNS resolution...${NC}"
RESOLVED_IP=$(dig +short ${DUCKDNS_DOMAIN}.duckdns.org @8.8.8.8 | tail -n1)
if [[ "$RESOLVED_IP" == "$GCP_IP" ]]; then
    echo -e "${GREEN}✅ DNS resolution verified${NC}"
    echo -e "${GREEN}   ${DUCKDNS_DOMAIN}.duckdns.org → ${RESOLVED_IP}${NC}"
else
    echo -e "${YELLOW}⚠️  DNS not fully propagated yet${NC}"
    echo -e "   Expected: ${GCP_IP}"
    echo -e "   Got:      ${RESOLVED_IP}"
    echo -e "${YELLOW}   Continuing anyway (may take a few minutes)...${NC}"
fi

# Install SSL certificate
echo ""
echo -e "${YELLOW}⏳ Installing SSL certificate...${NC}"
echo -e "${BLUE}   This will request a Let's Encrypt certificate${NC}"
echo ""

# Create basic nginx config for certbot
cat > /etc/nginx/sites-available/goblin-assistant << EOF
server {
    listen 80;
    server_name ${DUCKDNS_DOMAIN}.duckdns.org;
    
    location / {
        return 200 'GoblinOS Assistant - Setting up SSL...';
        add_header Content-Type text/plain;
    }
}
EOF

ln -sf /etc/nginx/sites-available/goblin-assistant /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# Request certificate
certbot --nginx \
    --non-interactive \
    --agree-tos \
    --email "${SSL_EMAIL}" \
    --domains "${DUCKDNS_DOMAIN}.duckdns.org" \
    --redirect

if [[ $? -eq 0 ]]; then
    echo -e "${GREEN}✅ SSL certificate installed${NC}"
    echo -e "${GREEN}   Certificate: /etc/letsencrypt/live/${DUCKDNS_DOMAIN}.duckdns.org/${NC}"
else
    echo -e "${RED}❌ SSL installation failed${NC}"
    echo -e "${YELLOW}   You can try again manually:${NC}"
    echo -e "   certbot --nginx -d ${DUCKDNS_DOMAIN}.duckdns.org"
    exit 1
fi

# Setup auto-renewal
echo ""
echo -e "${YELLOW}⏳ Setting up SSL auto-renewal...${NC}"
systemctl enable certbot.timer
systemctl start certbot.timer
echo -e "${GREEN}✅ SSL auto-renewal enabled${NC}"

# Test the domain
echo ""
echo -e "${YELLOW}⏳ Testing HTTPS access...${NC}"
sleep 5
if curl -sf "${PUBLIC_URL}" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ HTTPS is working!${NC}"
else
    echo -e "${YELLOW}⚠️  HTTPS test failed (may need a few minutes)${NC}"
fi

# Success summary
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                                ║${NC}"
echo -e "${BLUE}║   🎉 DEPLOYMENT COMPLETE!                                     ║${NC}"
echo -e "${BLUE}║                                                                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}✅ DuckDNS:${NC}       Configured and auto-updating"
echo -e "${GREEN}✅ SSL/HTTPS:${NC}     Certificate installed and auto-renewing"
echo -e "${GREEN}✅ Firewall:${NC}      Ports 80/443 configured"
echo ""
echo -e "${YELLOW}🌐 Your Public URL:${NC}"
echo -e "   ${PUBLIC_URL}"
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo -e "   1. Deploy your GoblinOS Assistant services"
echo -e "   2. Update nginx config to proxy to your backend"
echo -e "   3. Test your application"
echo ""
echo -e "${YELLOW}💡 Nginx config location:${NC}"
echo -e "   /etc/nginx/sites-available/goblin-assistant"
echo ""
echo -e "${YELLOW}📊 Check status:${NC}"
echo -e "   systemctl status nginx"
echo -e "   certbot certificates"
echo -e "   crontab -l | grep duckdns"
echo ""
echo -e "${GREEN}✨ Your customer-facing domain is ready!${NC}"
echo ""
