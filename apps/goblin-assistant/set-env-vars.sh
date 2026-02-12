#!/bin/bash

# Vercel Environment Variables Setup - Simple Bash Script
# This script uses vercel CLI with proper input handling

set -e

echo "🔧 Setting Vercel Environment Variables"
echo "========================================"

cd "/Volumes/GOBLINOS 1/ForgeMonorepo/apps/goblin-assistant"

# Check if vercel CLI is available
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Install with: npm i -g vercel"
    exit 1
fi

echo "✅ Vercel CLI found: $(vercel --version)"

# Check if project is linked
if [ ! -f ".vercel/project.json" ]; then
    echo "❌ Project not linked. Run: vercel link"
    exit 1
fi

echo "✅ Project linked"

# Function to set environment variable
set_env_var() {
    local key="$1"
    local value="$2"
    
    echo ""
    echo "📝 Setting $key..."
    
    # Use printf to avoid issues with special characters
    printf "%s\n" "$value" | vercel env add "$key" production --force 2>&1 || {
        echo "⚠️  Note: Variable may already exist or require manual setup"
        return 0
    }
    
    echo "✅ $key configured"
}

# Set each environment variable
echo ""
echo "Setting environment variables..."

set_env_var "NEXT_PUBLIC_API_URL" "https://goblin-backend.fly.dev"
set_env_var "NEXT_PUBLIC_FASTAPI_URL" "https://goblin-backend.fly.dev"
set_env_var "NEXT_PUBLIC_DD_APPLICATION_ID" "goblin-assistant"
set_env_var "NEXT_PUBLIC_DD_ENV" "production"
set_env_var "NEXT_PUBLIC_DD_VERSION" "1.0.0"

echo ""
echo "========================================"
echo "✅ Environment variable setup complete!"
echo ""
echo "Next steps:"
echo "  1. Verify variables: vercel env ls"
echo "  2. Deploy: vercel deploy --prod"
echo ""
