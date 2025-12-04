#!/bin/bash
# Deploy GoblinOS Assistant Frontend to Vercel (Simple Version)
# This script is managed in goblin-infra for centralized deployment control

set -e  # Exit on error

echo "🚀 Deploying GoblinOS Assistant Frontend to Vercel (via goblin-infra)..."

# Get the absolute path to the goblin-assistant app
GOBLIN_APP_DIR="/Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant"

# Check if we're in the right directory or navigate to goblin-assistant
if [[ ! -f "package.json" ]] || [[ ! -d "src" ]]; then
    echo "📁 Navigating to goblin-assistant app directory..."
    cd "$GOBLIN_APP_DIR"
fi

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Installing..."
    npm install -g vercel
fi

# Build the project
echo "📦 Building frontend..."
npm run build

# Deploy to Vercel
echo "🌐 Deploying to Vercel..."
vercel --prod

echo "✅ Frontend deployment complete!"
echo "🔗 URL: https://goblin-assistant.vercel.app"
echo ""
echo "Next steps:"
echo "1. Deploy backend to Fly.io (see goblin-infra/projects/goblin-assistant/deploy-backend.sh)"
echo "2. Configure environment variables in Vercel dashboard"
echo "3. Test the deployed application"
