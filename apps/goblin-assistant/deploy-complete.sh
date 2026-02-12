#!/bin/bash

# Complete Vercel Deployment Script for Goblin Assistant
# Handles all steps: configuration check, env vars, and deployment

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}🚀 Goblin Assistant Vercel Deployment${NC}"
echo -e "${BLUE}======================================${NC}"

cd "/Volumes/GOBLINOS 1/ForgeMonorepo/apps/goblin-assistant"

# Step 1: Check Vercel CLI
echo -e "\n${BLUE}[1/6] Checking Vercel CLI...${NC}"
if ! command -v vercel &> /dev/null; then
    echo -e "${RED}❌ Vercel CLI not found${NC}"
    echo "Install with: npm i -g vercel"
    exit 1
fi
VERCEL_VERSION=$(vercel --version)
echo -e "${GREEN}✅ Vercel CLI: $VERCEL_VERSION${NC}"

# Step 2: Check project linking
echo -e "\n${BLUE}[2/6] Checking project configuration...${NC}"
if [ ! -f ".vercel/project.json" ]; then
    echo -e "${RED}❌ Project not linked to Vercel${NC}"
    echo "Run: vercel link"
    exit 1
fi
PROJECT_ID=$(cat .vercel/project.json | grep -o '"projectId":"[^"]*"' | cut -d'"' -f4)
echo -e "${GREEN}✅ Project linked: $PROJECT_ID${NC}"

# Step 3: Check configuration files
echo -e "\n${BLUE}[3/6] Verifying configuration files...${NC}"

if [ -f "vercel.json" ]; then
    echo -e "${GREEN}✅ vercel.json found${NC}"
else
    echo -e "${YELLOW}⚠️  vercel.json not found${NC}"
fi

if [ -f "next.config.mjs" ]; then
    echo -e "${GREEN}✅ next.config.mjs found${NC}"
elif [ -f "next.config.js" ]; then
    echo -e "${GREEN}✅ next.config.js found${NC}"
else
    echo -e "${RED}❌ No Next.js config found${NC}"
    exit 1
fi

if [ -f ".vercelignore" ]; then
    IGNORE_COUNT=$(grep -v '^#' .vercelignore | grep -v '^$' | wc -l | tr -d ' ')
    echo -e "${GREEN}✅ .vercelignore found ($IGNORE_COUNT exclusions)${NC}"
else
    echo -e "${YELLOW}⚠️  .vercelignore not found${NC}"
fi

# Step 4: Check dependencies
echo -e "\n${BLUE}[4/6] Checking dependencies...${NC}"
if [ -d "node_modules" ]; then
    echo -e "${GREEN}✅ Dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠️  node_modules not found${NC}"
    echo "Run: pnpm install"
fi

# Step 5: Set environment variables
echo -e "\n${BLUE}[5/6] Setting environment variables...${NC}"

declare -A ENV_VARS
ENV_VARS=(
    ["NEXT_PUBLIC_API_URL"]="https://goblin-backend.fly.dev"
    ["NEXT_PUBLIC_FASTAPI_URL"]="https://goblin-backend.fly.dev"
    ["NEXT_PUBLIC_DD_APPLICATION_ID"]="goblin-assistant"
    ["NEXT_PUBLIC_DD_ENV"]="production"
    ["NEXT_PUBLIC_DD_VERSION"]="1.0.0"
)

SUCCESS_COUNT=0
TOTAL_VARS=${#ENV_VARS[@]}

for KEY in "${!ENV_VARS[@]}"; do
    VALUE="${ENV_VARS[$KEY]}"
    echo -n "   Setting $KEY... "
    
    # Try to set the variable (suppress verbose output)
    if echo "$VALUE" | vercel env add "$KEY" production --force >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        ((SUCCESS_COUNT++))
    else
        # Check if it already exists
        if vercel env ls 2>/dev/null | grep -q "$KEY"; then
            echo -e "${YELLOW}exists${NC}"
            ((SUCCESS_COUNT++))
        else
            echo -e "${RED}failed${NC}"
        fi
    fi
done

echo -e "\n${GREEN}✅ Environment variables: $SUCCESS_COUNT/$TOTAL_VARS configured${NC}"

# Step 6: Deploy
echo -e "\n${BLUE}[6/6] Deploying to production...${NC}"

read -p "Deploy to production now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Starting deployment..."
    
    if vercel deploy --prod; then
        echo -e "\n${GREEN}======================================${NC}"
        echo -e "${GREEN}✅ Deployment successful!${NC}"
        echo -e "${GREEN}======================================${NC}"
        
        echo -e "\nYour application is now live!"
        echo -e "\n${BLUE}Next steps:${NC}"
        echo "  1. Check deployment: vercel ls --prod"
        echo "  2. View logs: vercel logs"
        echo "  3. Test your application thoroughly"
    else
        echo -e "\n${RED}======================================${NC}"
        echo -e "${RED}❌ Deployment failed${NC}"
        echo -e "${RED}======================================${NC}"
        echo -e "\nCheck the errors above and:"
        echo "  1. Review Vercel dashboard for logs"
        echo "  2. Fix any build errors"
        echo "  3. Try deploying again"
        exit 1
    fi
else
    echo -e "\n${YELLOW}Deployment skipped${NC}"
    echo -e "\nTo deploy manually:"
    echo "  vercel deploy --prod"
fi

echo ""
