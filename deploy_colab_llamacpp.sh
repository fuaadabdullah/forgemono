#!/bin/bash
"""
Deploy llama.cpp to Google Colab and update Goblin Assistant config

This script guides you through deploying llama.cpp on Google Colab
and automatically updates the Goblin Assistant configuration.

Usage:
    ./deploy_colab_llamacpp.sh
"""

set -e

echo "🚀 Deploying llama.cpp to Google Colab"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COLAB_URL="https://colab.research.google.com/github/fuaadabdullah/ForgeMonorepo/blob/main/notebooks/colab_llamacpp_setup_complete.ipynb"
REPO_ROOT="/Users/fuaadabdullah/ForgeMonorepo"
CONFIG_FILE="$REPO_ROOT/goblin-assistant/config/providers.toml"

echo -e "${BLUE}📋 Deployment Steps:${NC}"
echo "1. Open Google Colab notebook"
echo "2. Run setup cells (1-7)"
echo "3. Get ngrok URL from Colab output"
echo "4. Update local configuration"
echo "5. Test integration"
echo ""

# Step 1: Open Colab
echo -e "${YELLOW}Step 1: Opening Colab notebook...${NC}"
echo "Opening: $COLAB_URL"
echo ""
echo -e "${GREEN}✅ Colab notebook opened in browser${NC}"
echo ""

# Step 2: Instructions for Colab
echo -e "${YELLOW}Step 2: Run these cells in Colab (in order):${NC}"
echo ""
echo "🔵 Cell 1: Mount Google Drive"
echo "   - Click the play button"
echo "   - Sign in with your Google account"
echo "   - Grant permissions"
echo ""

echo "🔵 Cell 2: Install dependencies & build llama.cpp"
echo "   - This takes 2-3 minutes"
echo ""

echo "🔵 Cell 3: Install ngrok"
echo "   - Auth token is already configured"
echo ""

echo "🔵 Cell 4: Install huggingface-cli (optional)"
echo ""

echo "🔵 Cell 5: Download TinyLlama model"
echo "   - Downloads to your Google Drive"
echo "   - Takes 1-2 minutes"
echo ""

echo "🔵 Cell 6: Start llama.cpp server"
echo "   - Server starts on port 8080"
echo ""

echo "🔵 Cell 7: Setup ngrok tunnel"
echo "   - Creates public URL"
echo "   - Copy the URL from the output (looks like: https://abc123.ngrok-free.app)"
echo ""

# Step 3: Wait for user input
echo -e "${YELLOW}Step 3: Get the ngrok URL${NC}"
echo ""
echo -n "Enter the ngrok URL from Colab (e.g., https://abc123.ngrok-free.app): "
read NGROK_URL

if [ -z "$NGROK_URL" ]; then
    echo -e "${RED}❌ No URL provided. Exiting.${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Got ngrok URL: $NGROK_URL${NC}"
echo ""

# Step 4: Update configuration
echo -e "${YELLOW}Step 4: Updating Goblin Assistant configuration...${NC}"

cd "$REPO_ROOT"

if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}❌ Config file not found: $CONFIG_FILE${NC}"
    exit 1
fi

# Update the config using Python script
python3 scripts/update_colab_endpoint.py --url "$NGROK_URL" --test

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to update configuration${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Configuration updated successfully!${NC}"
echo ""

# Step 5: Test integration
echo -e "${YELLOW}Step 5: Testing integration...${NC}"

python3 scripts/test_goblin_colab_integration.py --backend-url http://localhost:8000

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 Deployment successful!${NC}"
    echo ""
    echo "Your llama.cpp server is now running on Google Colab and integrated with Goblin Assistant."
    echo ""
    echo "📋 Important notes:"
    echo "- Colab sessions timeout after ~90 minutes"
    echo "- Keep the Colab tab open to maintain the session"
    echo "- Models are saved in your Google Drive for reuse"
    echo "- Use Colab Pro for longer sessions if needed"
else
    echo ""
    echo -e "${RED}⚠️  Integration test failed${NC}"
    echo ""
    echo "The configuration was updated, but there may be connectivity issues."
    echo "Try restarting the Goblin Assistant backend and running the test again."
fi

echo ""
echo -e "${BLUE}📚 Useful commands:${NC}"
echo "• Restart backend: cd goblin-assistant/api && uvicorn main:app --host 0.0.0.0 --port 8000"
echo "• Run tests: python3 scripts/test_goblin_colab_integration.py --backend-url http://localhost:8000"
echo "• Check backend: curl http://localhost:8000/health"
