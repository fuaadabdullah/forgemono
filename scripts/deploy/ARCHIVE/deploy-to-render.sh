#!/bin/bash
# Deprecated: Render deployment is deprecated. Use Fly.io for production deploys.
set -e

echo "❗️ This script is deprecated. Use ./deploy-fly.sh or ./deploy-backend.sh fly instead (Fly.io)."
exit 1

echo "🚀 Deploying Goblin Assistant Backend to Render..."
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if render.yaml exists
if [ ! -f "render.yaml" ]; then
    echo -e "${RED}❌ Error: render.yaml not found${NC}"
    echo "Make sure you're running this from the goblin-assistant directory"
    exit 1
fi

echo -e "${YELLOW}📋 Pre-deployment Checklist:${NC}"
echo ""
echo "Before deploying, ensure you have:"
echo "  ✅ Created a Render account at https://render.com"
echo "  ✅ Set up your API keys (Anthropic, DeepSeek, Gemini, Grok)"
echo "  ✅ Configured a PostgreSQL database (or use Render's managed database)"
echo "  ✅ Updated .env.production with your values"
echo ""

read -p "Have you completed the checklist? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}⚠️  Please complete the checklist first${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}📦 Step 1: Preparing deployment...${NC}"

# Check if we're in a git repository
if [ ! -d "../../.git" ]; then
    echo -e "${RED}❌ Error: Not in a git repository${NC}"
    echo "Render requires your code to be in a Git repository (GitHub, GitLab, or Bitbucket)"
    exit 1
fi

echo -e "${GREEN}✅ Git repository detected${NC}"

echo ""
echo -e "${GREEN}📤 Step 2: Deployment Options${NC}"
echo ""
echo "Choose your deployment method:"
echo "  1. Render Dashboard (Recommended for first-time setup)"
echo "  2. Render CLI (Automatic deployment)"
echo ""
read -p "Select option (1 or 2): " -n 1 -r
echo ""

if [[ $REPLY == "1" ]]; then
    echo ""
    echo -e "${GREEN}🌐 Manual Deployment via Render Dashboard${NC}"
    echo ""
    echo "Follow these steps:"
    echo ""
    echo "1. Go to https://dashboard.render.com"
    echo "2. Click 'New +' → 'Blueprint'"
    echo "3. Connect your Git repository"
    echo "4. Select the repository: forgemono"
    echo "5. Render will auto-detect render.yaml"
    echo "6. Click 'Apply' to create services"
    echo ""
    echo "7. Set required environment variables in Render Dashboard:"
    echo "   - ANTHROPIC_API_KEY"
    echo "   - DEEPSEEK_API_KEY"
    echo "   - GEMINI_API_KEY"
    echo "   - GROK_API_KEY"
    echo "   - DATABASE_URL (if not using Render's database)"
    echo ""
    echo "8. Click 'Deploy' to start the deployment"
    echo ""
    echo -e "${YELLOW}📝 Note: JWT_SECRET_KEY will be auto-generated${NC}"
    echo -e "${YELLOW}📝 Note: PORT will be auto-assigned by Render${NC}"
    echo ""

elif [[ $REPLY == "2" ]]; then
    echo ""
    echo -e "${GREEN}🤖 Automatic Deployment via Render CLI${NC}"
    echo ""

    # Check if Render CLI is installed
    if ! command -v render &> /dev/null; then
        echo -e "${YELLOW}⚠️  Render CLI not found. Installing...${NC}"
        echo ""

        # Detect OS and install
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            brew install render
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            # Linux
            curl -fsSL https://render.com/install.sh | sh
        else
            echo -e "${RED}❌ Unsupported OS for automatic CLI installation${NC}"
            echo "Please install Render CLI manually: https://render.com/docs/cli"
            exit 1
        fi
    fi

    echo -e "${GREEN}✅ Render CLI is installed${NC}"
    echo ""

    # Login to Render
    echo -e "${YELLOW}🔐 Logging in to Render...${NC}"
    render login

    echo ""
    echo -e "${GREEN}🚀 Deploying with render.yaml...${NC}"

    # Deploy using Blueprint
    render deploy

    echo ""
    echo -e "${GREEN}✅ Deployment initiated!${NC}"
    echo ""
    echo "Monitor your deployment at: https://dashboard.render.com"

else
    echo -e "${RED}❌ Invalid option${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 Next Steps:${NC}"
echo ""
echo "1. Wait for deployment to complete (5-10 minutes)"
echo "2. Get your backend URL from Render dashboard"
echo "3. Test the health endpoint:"
echo "   curl https://your-backend-url/health"
echo ""
echo "4. Update frontend environment:"
echo "   VITE_FASTAPI_URL=https://your-backend-url"
echo ""
echo "5. Deploy frontend to Netlify:"
echo "   ./deploy-frontend.sh"
echo ""
echo -e "${GREEN}✨ Happy deploying!${NC}"
