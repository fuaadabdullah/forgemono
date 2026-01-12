#!/bin/bash
#
# Quick Deployment Helper for GoblinOS Assistant
# Frontend: Vercel | Backend: Fly.io | Domain: DuckDNS
#

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║   🚀 GoblinOS Assistant - Quick Deploy                        ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}📋 Pre-Deployment Checklist${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check 1: Vercel domain
echo -e "${YELLOW}1. Have you added the domain to Vercel?${NC}"
echo "   → Go to: https://vercel.com/dashboard"
echo "   → Settings → Domains"
echo "   → Add: goblinosassistant.duckdns.org"
echo ""
read -p "   Domain added? (y/N): " domain_added
if [[ ! $domain_added =~ ^[Yy]$ ]]; then
    echo "   ⚠️  Add the domain first, then run this script again"
    exit 1
fi

# Check 2: Get Vercel IP
echo ""
echo -e "${YELLOW}2. What IP did Vercel give you?${NC}"
echo "   (e.g., 76.76.21.21)"
read -p "   Vercel IP: " vercel_ip

if [[ -z "$vercel_ip" ]]; then
    echo "   ⚠️  IP required"
    exit 1
fi

# Check 3: Update DuckDNS
echo ""
echo -e "${YELLOW}3. Updating DuckDNS...${NC}"
RESPONSE=$(curl -s "https://www.duckdns.org/update?domains=goblinosassistant&token=59be274c-ca62-4e86-b671-035cee6f5bad&ip=${vercel_ip}")

if [[ "$RESPONSE" == "OK" ]]; then
    echo -e "   ${GREEN}✅ DuckDNS updated successfully${NC}"
else
    echo -e "   ❌ DuckDNS update failed: $RESPONSE"
    exit 1
fi

# Check 4: Environment variables
echo ""
echo -e "${YELLOW}4. Have you added environment variables to Vercel?${NC}"
echo "   Required variables:"
echo "   - BACKEND_URL=https://goblin-backend.fly.dev"
echo "   - NEXT_PUBLIC_API_URL=https://goblin-backend.fly.dev"
echo "   - NEXT_PUBLIC_DOMAIN=goblinosassistant.duckdns.org"
echo ""
read -p "   Variables added? (y/N): " env_added
if [[ ! $env_added =~ ^[Yy]$ ]]; then
    echo "   ⚠️  Add the variables first"
    echo "   → https://vercel.com/dashboard → Settings → Environment Variables"
    exit 1
fi

# Check 5: Ready to deploy
echo ""
echo -e "${YELLOW}5. Ready to deploy?${NC}"
echo "   This will:"
echo "   → Push changes to GitHub"
echo "   → Trigger Vercel auto-deployment"
echo "   → Deploy with your custom domain"
echo ""
read -p "   Deploy now? (y/N): " deploy_now

if [[ $deploy_now =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${BLUE}🚀 Deploying...${NC}"
    echo ""
    
    # Push to GitHub
    cd /Users/fuaadabdullah/ForgeMonorepo
    git push origin feat/chat-kamatera-integration
    
    echo ""
    echo -e "${GREEN}✅ Pushed to GitHub!${NC}"
    echo ""
    echo "   Vercel is now building and deploying..."
    echo "   Watch progress: https://vercel.com/dashboard"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo -e "${GREEN}🎉 Deployment initiated!${NC}"
    echo ""
    echo "   Wait 2-3 minutes for deployment to complete, then:"
    echo ""
    echo "   Test backend:"
    echo "   curl https://goblin-backend.fly.dev/health"
    echo ""
    echo "   Test frontend:"
    echo "   curl -I https://goblinosassistant.duckdns.org"
    echo ""
    echo "   Open in browser:"
    echo "   https://goblinosassistant.duckdns.org"
    echo ""
else
    echo ""
    echo "   Deployment cancelled"
    echo "   Run this script again when ready"
    echo ""
fi
