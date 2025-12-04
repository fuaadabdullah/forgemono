#!/bin/bash
# Deploy GoblinOS Assistant Frontend to Vercel (Infrastructure Repository)
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

# Load production secrets from vault
echo "📦 Loading production secrets from vault..."
export VERCEL_TOKEN=$(bw get password b0729e06-3b13-4ee4-bf66-b3a9006a2b82)
export GOOGLE_CLIENT_ID=$(bw get password goblin-prod-google-client-id)
export SUPABASE_URL=$(bw get password goblin-prod-supabase-url)
export SUPABASE_ANON_KEY=$(bw get password goblin-prod-supabase-anon-key)

echo "✅ Secrets loaded successfully"

# Authenticate with Vercel
echo "🔑 Authenticating with Vercel..."
export VERCEL_TOKEN="$VERCEL_TOKEN"  # Ensure token is available for Vercel CLI

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Build the project
echo "📦 Building frontend..."
npm run build

# Set environment variables in Vercel
echo "🔧 Configuring Vercel environment..."
vercel env rm VITE_API_URL production -y 2>/dev/null || true
vercel env rm VITE_FASTAPI_URL production -y 2>/dev/null || true
vercel env rm VITE_FRONTEND_URL production -y 2>/dev/null || true
vercel env rm VITE_GOOGLE_CLIENT_ID production -y 2>/dev/null || true
vercel env rm VITE_APP_ENV production -y 2>/dev/null || true
vercel env rm SUPABASE_URL production -y 2>/dev/null || true
vercel env rm SUPABASE_ANON_KEY production -y 2>/dev/null || true

vercel env add VITE_API_URL production <<< "https://goblin-assistant.fly.dev"
vercel env add VITE_FASTAPI_URL production <<< "https://goblin-assistant.fly.dev"
vercel env add VITE_FRONTEND_URL production <<< "https://goblin-assistant.vercel.app"
vercel env add VITE_GOOGLE_CLIENT_ID production <<< "$GOOGLE_CLIENT_ID"
vercel env add VITE_APP_ENV production <<< "production"
vercel env add SUPABASE_URL production <<< "$SUPABASE_URL"
vercel env add SUPABASE_ANON_KEY production <<< "$SUPABASE_ANON_KEY"

# Deploy to Vercel
echo "🌐 Deploying to Vercel..."
vercel --prod --cwd "$GOBLIN_APP_DIR"

# Clean up session
unset BW_SESSION
unset VERCEL_TOKEN
unset GOOGLE_CLIENT_ID
unset SUPABASE_URL
unset SUPABASE_ANON_KEY

echo "✅ Frontend deployment complete!"
echo "🔗 URL: https://goblin-assistant.vercel.app"
echo ""
echo "🧹 Secrets cleaned from environment"
echo ""
echo "Next steps:"
echo "1. Deploy backend to Fly.io (see goblin-infra/projects/goblin-assistant/deploy-backend.sh)"
echo "2. Verify environment variables in Vercel dashboard"
echo "3. Test the deployed application"
