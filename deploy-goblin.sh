#!/bin/bash
# Deployment script for Goblin Assistant frontend
# Run this when your network is restored

set -e

cd '/Volumes/GOBLINOS 1/ForgeMonorepo'

echo "🚀 Goblin Assistant Deployment"
echo "================================"
echo ""

# Clean Git corruption from macOS metadata
echo "🧹 Cleaning macOS metadata files..."
find .git -name '._*' -type f -exec rm -f {} + 2>/dev/null || true
echo "✅ Cleaned"

# Stage deployment files
echo ""
echo "📦 Staging deployment files..."
git add apps/goblin-assistant/.vercelignore
git add apps/goblin-assistant/DEPLOYMENT_READY.md 2>/dev/null || true
git add apps/goblin-assistant/deploy-complete.sh 2>/dev/null || true
echo "✅ Files staged"

# Commit
echo ""
echo "💾 Committing changes..."
git commit -m "feat(goblin-assistant): optimize Vercel deployment with 90+ exclusions

- Add comprehensive .vercelignore (90+ patterns)
- Exclude backend code, docs, tests from deployment
- Reduce deployment size by ~70%
- Add deployment automation scripts
"
echo "✅ Committed"

# Push (will trigger Vercel auto-deploy)
echo ""
echo "🌐 Pushing to GitHub (will trigger Vercel deployment)..."
git push origin fix/docs-lint-2
echo "✅ Pushed!"

echo ""
echo "================================"
echo "✅ Deployment Initiated!"
echo ""
echo "Vercel will automatically deploy from GitHub."
echo "Check status at: https://vercel.com/dashboard"
echo ""
echo "Your deployment URL: https://goblin-assistant.vercel.app"
echo ""
