#!/bin/bash
# Goblin Assistant - Production Deployment Script
# Deploys to Fly.io using Bitwarden secrets (manual version of CI/CD)
# Usage: ./deploy-fly.sh

set -e  # Exit on any error

echo "🚀 Goblin Assistant - Production Deployment to Fly.io"
echo "====================================================="

# Check if Bitwarden CLI is available
if ! command -v bw &> /dev/null; then
    echo "❌ Bitwarden CLI not found. Install with: npm install -g @bitwarden/cli"
    exit 1
fi

# Unlock Bitwarden vault
echo "🔐 Unlocking Bitwarden vault..."
export BW_SESSION=$(bw unlock --raw)

# Load production secrets
echo "📦 Loading production secrets..."
export FASTAPI_SECRET=$(bw get password goblin-prod-fastapi-secret)
export DB_URL=$(bw get password goblin-prod-db-url)
export CF_TOKEN=$(bw get password goblin-prod-cloudflare)
export OPENAI_KEY=$(bw get password goblin-prod-openai)
export JWT_SECRET=$(bw get password goblin-prod-jwt)
export FLY_TOKEN=$(bw get password goblin-prod-fly-token)

echo "✅ Secrets loaded successfully"

# Check if Fly.io CLI is available
if ! command -v flyctl &> /dev/null; then
    echo "❌ Fly.io CLI not found. Install from: https://fly.io/docs/getting-started/installing-flyctl/"
    exit 1
fi

# Authenticate with Fly.io
echo "🔑 Authenticating with Fly.io..."
echo "$FLY_TOKEN" | flyctl auth login --stdin

# Deploy to Fly.io
echo "🌐 Deploying to Fly.io..."
flyctl deploy --remote-only --yes

# Clean up secrets from environment
unset BW_SESSION
unset FASTAPI_SECRET
unset DB_URL
unset CF_TOKEN
unset OPENAI_KEY
unset JWT_SECRET
unset FLY_TOKEN

echo "✅ Deployment complete!"
echo "🧹 Secrets cleaned from environment"
echo ""
echo "🔗 Check your deployment at: https://goblin-assistant.fly.dev"
echo ""
echo "🧙‍♂️ Goblin deployment ritual complete!"
