#!/bin/bash

# Vercel Environment Variable Setup Script
# This script sets up all required environment variables for production deployment

set -e

echo "🔧 Setting Vercel Environment Variables for Goblin Assistant"
echo "=============================================================="

# API URLs
echo "📍 Setting API URLs..."
echo "https://goblin-backend.fly.dev" | vercel env add NEXT_PUBLIC_API_URL production
echo "https://goblin-backend.fly.dev" | vercel env add NEXT_PUBLIC_FASTAPI_URL production

# Datadog Configuration 
echo "📊 Setting Datadog variables..."
echo "goblin-assistant" | vercel env add NEXT_PUBLIC_DD_APPLICATION_ID production
echo "production" | vercel env add NEXT_PUBLIC_DD_ENV production

echo ""
echo "✅ Environment variables setup complete!"
echo ""
echo "To verify the variables, run:"
echo "  vercel env ls"
echo ""
echo "To deploy with these variables:"
echo "  vercel deploy --prod"
