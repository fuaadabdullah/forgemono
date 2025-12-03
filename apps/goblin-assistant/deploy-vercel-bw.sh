#!/bin/bash
# Deploy GoblinOS Assistant to Vercel with Bitwarden Secret Loading

set -e  # Exit on error

echo "🔮 Deploying GoblinOS Assistant Frontend to Vercel (Bitwarden Vault)..."

# Navigate to project directory
cd "$(dirname "$0")"

# Check if Bitwarden CLI is installed
if ! command -v bw &> /dev/null; then
    echo "❌ Bitwarden CLI not found. Installing..."
    npm install -g @bitwarden/cli
fi

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Installing..."
    npm install -g vercel
fi

# Unlock Bitwarden vault
echo "🔐 Unlocking Bitwarden vault..."
export BW_SESSION=$(bw unlock --raw)

# Load production secrets
echo "📦 Loading production secrets from vault..."
export FASTAPI_SECRET=$(bw get password goblin-prod-fastapi-secret)
export CLOUDFLARE_API=$(bw get password goblin-prod-cloudflare-api)
export OPENAI_KEY=$(bw get password goblin-prod-openai-key)
export CLOUDINARY_KEY=$(bw get password goblin-prod-cloudinary-key)

echo "✅ Secrets loaded successfully"

# Build the project
echo "📦 Building frontend..."
npm run build

# Set environment variables in Vercel
echo "🔧 Configuring Vercel environment..."
vercel env add FASTAPI_SECRET production <<< "$FASTAPI_SECRET"
vercel env add CLOUDFLARE_API_TOKEN production <<< "$CLOUDFLARE_API"
vercel env add OPENAI_API_KEY production <<< "$OPENAI_KEY"
vercel env add CLOUDINARY_CLOUD_NAME production <<< "$CLOUDINARY_KEY"

# Deploy to Vercel
echo "🌐 Deploying to Vercel..."
vercel --prod

# Clean up session
unset BW_SESSION
unset FASTAPI_SECRET
unset CLOUDFLARE_API
unset OPENAI_KEY
unset CLOUDINARY_KEY

echo "✅ Frontend deployment complete!"
echo "🔗 URL: https://goblin-assistant.vercel.app"
echo ""
echo "🧹 Secrets cleaned from environment"
echo ""
echo "Next steps:"
echo "1. Deploy backend to Fly.io (see FLY_DEPLOYMENT.md or run ./deploy-fly.sh)"
echo "2. Verify environment variables in Vercel dashboard"
echo "3. Test the deployed application"
