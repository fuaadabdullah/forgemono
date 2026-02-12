# Complete Vercel CLI Deployment Commands
# Run these commands in your terminal to deploy Goblin Assistant

echo "🚀 Starting Vercel Deployment for Goblin Assistant"
echo "=================================================="

# Navigate to project root
cd "/Volumes/GOBLINOS 1/ForgeMonorepo"

# Check Vercel CLI
echo "✓ Checking Vercel CLI..."
vercel --version

# Check git status and commit changes
echo "✓ Checking git status..."
git status --short
if [ -n "$(git status --porcelain)" ]; then
    echo "📝 Committing changes..."
    git add .
    git commit -m "fix(vercel): configure pnpm monorepo deployment" || echo "No changes to commit"
fi

# Link project to Vercel
echo "🔗 Linking project to Vercel..."
vercel link --yes

# Set environment variables
echo "🔧 Setting environment variables..."
echo "https://goblin-backend.fly.dev" | vercel env add NEXT_PUBLIC_API_URL production
echo "https://goblin-backend.fly.dev" | vercel env add NEXT_PUBLIC_FASTAPI_URL production
echo "goblin-assistant" | vercel env add NEXT_PUBLIC_DD_APPLICATION_ID production
echo "production" | vercel env add NEXT_PUBLIC_DD_ENV production
echo "1.0.0" | vercel env add NEXT_PUBLIC_DD_VERSION production

# Deploy to production
echo "🚀 Deploying to production..."
vercel deploy --prod

# Get deployment URL
echo "📍 Getting deployment URL..."
vercel ls --prod

echo ""
echo "✅ Deployment Complete!"
echo "Check the URL above and verify the application is working."
echo "If you encounter issues, check the Vercel dashboard for build logs."
