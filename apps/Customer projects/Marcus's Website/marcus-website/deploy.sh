#!/bin/bash

# Deployment script for Elbey Projects website
# Usage: ./deploy.sh [platform]
# Platforms: vercel, netlify, build

PLATFORM=${1:-"build"}

echo "🚀 Deploying Elbey Projects website to $PLATFORM"

case $PLATFORM in
  "vercel")
    echo "📦 Deploying to Vercel..."
    if ! command -v vercel &> /dev/null; then
      echo "❌ Vercel CLI not found. Install with: npm i -g vercel"
      exit 1
    fi
    vercel --prod
    ;;
  "netlify")
    echo "📦 Deploying to Netlify..."
    if ! command -v netlify &> /dev/null; then
      echo "❌ Netlify CLI not found. Install with: npm i -g netlify-cli"
      exit 1
    fi
    netlify deploy --prod --dir=.next
    ;;
  "build")
    echo "🔨 Building for production..."
    npm run build
    echo "✅ Build complete. Ready for manual deployment."
    echo "📁 Output directory: .next"
    ;;
  *)
    echo "❌ Unknown platform: $PLATFORM"
    echo "📖 Usage: $0 [vercel|netlify|build]"
    exit 1
    ;;
esac

echo "🎉 Deployment complete!"
