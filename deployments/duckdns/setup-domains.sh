#!/bin/bash
#
# GoblinOS Assistant - DuckDNS Domain Setup for Fly.io + Vercel
# 
# Architecture:
# - Backend (Fly.io): api.goblinosassistant.duckdns.org
# - Frontend (Vercel): goblinosassistant.duckdns.org
#

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
DUCKDNS_DOMAIN="goblinosassistant"
DUCKDNS_TOKEN="59be274c-ca62-4e86-b671-035cee6f5bad"
FLY_APP_NAME="goblin-backend"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                                ║${NC}"
echo -e "${BLUE}║   🚀 GoblinOS Assistant - DuckDNS + Fly.io + Vercel          ║${NC}"
echo -e "${BLUE}║                                                                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Backend:${NC}  api.goblinosassistant.duckdns.org → Fly.io"
echo -e "${GREEN}Frontend:${NC} goblinosassistant.duckdns.org → Vercel"
echo ""

# Check flyctl
if ! command -v flyctl &> /dev/null; then
    echo -e "${RED}❌ flyctl not found${NC}"
    echo -e "${YELLOW}   Install: curl -L https://fly.io/install.sh | sh${NC}"
    exit 1
fi

echo -e "${GREEN}✅ flyctl found${NC}"

# Get Fly.io backend IP
echo ""
echo -e "${YELLOW}⏳ Getting Fly.io backend IP...${NC}"
FLY_IP=$(flyctl ips list -a ${FLY_APP_NAME} -j | jq -r '.[0].address // empty')

if [[ -z "$FLY_IP" ]]; then
    echo -e "${RED}❌ Could not get Fly.io IP for app: ${FLY_APP_NAME}${NC}"
    echo -e "${YELLOW}   Run: flyctl ips allocate-v4 -a ${FLY_APP_NAME}${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Fly.io backend IP: ${FLY_IP}${NC}"

# Update DuckDNS for root domain (points to Vercel)
echo ""
echo -e "${YELLOW}⏳ Configuring DuckDNS domains...${NC}"
echo -e "${BLUE}   Note: goblinosassistant.duckdns.org will be configured in Vercel${NC}"
echo -e "${BLUE}         api.goblinosassistant.duckdns.org will point to Fly.io${NC}"

# DuckDNS doesn't support subdomains directly
# We need to use Fly.io's custom domain feature instead
echo ""
echo -e "${YELLOW}⏳ Adding custom domain to Fly.io...${NC}"

# Add custom certificate for the subdomain
flyctl certs create api.goblinosassistant.duckdns.org -a ${FLY_APP_NAME} || {
    echo -e "${YELLOW}   Certificate may already exist${NC}"
}

# Get certificate info
echo ""
echo -e "${YELLOW}📋 Certificate configuration:${NC}"
flyctl certs show api.goblinosassistant.duckdns.org -a ${FLY_APP_NAME}

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                                ║${NC}"
echo -e "${BLUE}║   ⚠️  MANUAL STEPS REQUIRED                                   ║${NC}"
echo -e "${BLUE}║                                                                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${YELLOW}1. Configure DuckDNS Subdomains:${NC}"
echo ""
echo -e "   Unfortunately, DuckDNS doesn't support subdomains directly."
echo -e "   You have two options:"
echo ""
echo -e "   ${GREEN}Option A: Register a second DuckDNS domain (Recommended)${NC}"
echo -e "   - Go to: https://www.duckdns.org/domains"
echo -e "   - Register: ${BLUE}goblinapi${NC} (this will be goblinapi.duckdns.org)"
echo -e "   - Update IP to: ${FLY_IP}"
echo -e "   - Then run: flyctl certs create goblinapi.duckdns.org -a ${FLY_APP_NAME}"
echo ""
echo -e "   ${YELLOW}Option B: Use Fly.io subdomain${NC}"
echo -e "   - Backend: https://${FLY_APP_NAME}.fly.dev"
echo -e "   - Frontend: https://goblinosassistant.duckdns.org"
echo ""

echo -e "${YELLOW}2. Configure Vercel:${NC}"
echo ""
echo -e "   a) Add custom domain:"
echo -e "      - Go to: https://vercel.com/[your-project]/settings/domains"
echo -e "      - Add domain: ${BLUE}goblinosassistant.duckdns.org${NC}"
echo -e "      - Vercel will give you an IP address (e.g., 76.76.21.21)"
echo ""
echo -e "   b) Update DuckDNS:"
echo -e "      - Go to: https://www.duckdns.org/domains"
echo -e "      - Update goblinosassistant IP to Vercel's IP"
echo ""
echo -e "   c) Update environment variables in Vercel:"
echo -e "      - NEXT_PUBLIC_API_URL=${BLUE}https://goblinapi.duckdns.org${NC} (or Fly.io URL)"
echo -e "      - BACKEND_URL=${BLUE}https://goblinapi.duckdns.org${NC} (or Fly.io URL)"
echo ""

echo -e "${YELLOW}3. Verify Setup:${NC}"
echo ""
echo -e "   # Test backend"
echo -e "   curl https://goblinapi.duckdns.org/health"
echo -e "   # OR"
echo -e "   curl https://${FLY_APP_NAME}.fly.dev/health"
echo ""
echo -e "   # Test frontend"
echo -e "   curl https://goblinosassistant.duckdns.org"
echo ""

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   📋 Summary                                                   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Fly.io App:${NC}       ${FLY_APP_NAME}"
echo -e "${GREEN}Fly.io IP:${NC}        ${FLY_IP}"
echo -e "${GREEN}Fly.io URL:${NC}       https://${FLY_APP_NAME}.fly.dev"
echo ""
echo -e "${YELLOW}Recommended Setup:${NC}"
echo -e "  Backend:  https://goblinapi.duckdns.org → Fly.io (${FLY_IP})"
echo -e "  Frontend: https://goblinosassistant.duckdns.org → Vercel"
echo ""
echo -e "${BLUE}Or use Fly.io subdomain:${NC}"
echo -e "  Backend:  https://${FLY_APP_NAME}.fly.dev"
echo -e "  Frontend: https://goblinosassistant.duckdns.org → Vercel"
echo ""
