#!/bin/bash
# Vercel Deployment Checklist for Goblin Assistant
# Run this script to verify Vercel deployment is ready

set -e

echo "🔍 Vercel Deployment Readiness Check"
echo "===================================="
echo ""

# Check 1: Vercel configuration files exist
echo "✓ Checking Vercel configuration files..."
if [ -f "vercel.json" ]; then
    echo "  ✅ Root vercel.json found"
else
    echo "  ❌ Root vercel.json missing"
    exit 1
fi

if [ -f "apps/goblin-assistant/vercel.json" ]; then
    echo "  ✅ App vercel.json found"
else
    echo "  ❌ App vercel.json missing"
    exit 1
fi

# Check 2: pnpm configuration
echo ""
echo "✓ Checking pnpm configuration..."
if [ -f "pnpm-workspace.yaml" ]; then
    echo "  ✅ pnpm-workspace.yaml found"
else
    echo "  ❌ pnpm-workspace.yaml missing"
    exit 1
fi

if [ -f "pnpm-lock.yaml" ]; then
    echo "  ✅ pnpm-lock.yaml found"
else
    echo "  ❌ pnpm-lock.yaml missing - run 'pnpm install'"
    exit 1
fi

# Check 3: Next.js configuration
echo ""
echo "✓ Checking Next.js configuration..."
if [ -f "apps/goblin-assistant/next.config.mjs" ]; then
    echo "  ✅ next.config.mjs found"
else
    echo "  ❌ next.config.mjs missing"
    exit 1
fi

if [ -f "apps/goblin-assistant/package.json" ]; then
    if grep -q '"next":' "apps/goblin-assistant/package.json"; then
        echo "  ✅ Next.js dependency found in package.json"
    else
        echo "  ❌ Next.js dependency missing from package.json"
        exit 1
    fi
fi

# Check 4: Build scripts
echo ""
echo "✓ Checking build scripts..."
if grep -q '"build": "next build"' "apps/goblin-assistant/package.json"; then
    echo "  ✅ Build script configured"
else
    echo "  ❌ Build script missing or incorrect"
    exit 1
fi

# Check 5: Environment variables documentation
echo ""
echo "✓ Checking environment variable documentation..."
if [ -f "apps/goblin-assistant/.env.example" ]; then
    echo "  ✅ .env.example found"
    if grep -q "NEXT_PUBLIC_" "apps/goblin-assistant/.env.example"; then
        echo "  ✅ Public environment variables documented"
    fi
else
    echo "  ⚠️  .env.example not found (optional)"
fi

# Check 6: Vercel ignores
echo ""
echo "✓ Checking Vercel ignore patterns..."
if [ -f "apps/goblin-assistant/.vercelignore" ]; then
    echo "  ✅ .vercelignore found"
    if grep -q "backend/" "apps/goblin-assistant/.vercelignore"; then
        echo "  ✅ Backend properly excluded from Vercel build"
    fi
fi

# Summary
echo ""
echo "===================================="
echo "✅ All checks passed!"
echo ""
echo "Next steps:"
echo "1. Push changes to git: git push"
echo "2. Verify Vercel deployment in dashboard"
echo "3. Check build logs for pnpm usage"
echo "4. Verify environment variables are set"
echo "5. Test API proxy routes"
echo ""
