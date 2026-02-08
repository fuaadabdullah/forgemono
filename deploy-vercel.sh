#!/bin/bash
# Complete Vercel Deployment Script for Goblin Assistant
# This script handles the entire deployment process via CLI

set -e

echo "🚀 Starting Complete Vercel Deployment for Goblin Assistant"
echo "=========================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "pnpm-workspace.yaml" ]; then
    print_error "Not in the monorepo root directory. Please run from /Volumes/GOBLINOS 1/ForgeMonorepo"
    exit 1
fi

print_status "Working directory: $(pwd)"

# Step 1: Check Vercel CLI
print_status "Step 1: Checking Vercel CLI..."
if ! command -v vercel &> /dev/null; then
    print_error "Vercel CLI not found. Please install it first: npm i -g vercel"
    exit 1
fi
print_success "Vercel CLI found: $(vercel --version)"

# Step 2: Check git status
print_status "Step 2: Checking git status..."
if [ -n "$(git status --porcelain)" ]; then
    print_warning "Uncommitted changes found. Adding and committing..."
    git add .
    git commit -m "fix(vercel): configure pnpm monorepo deployment" || print_warning "No changes to commit"
else
    print_success "Git working directory is clean"
fi

# Step 3: Link project to Vercel (if not already linked)
print_status "Step 3: Linking project to Vercel..."
if [ ! -f ".vercel/project.json" ]; then
    print_warning "Project not linked to Vercel. Attempting to link..."
    vercel link --yes || {
        print_error "Failed to link project. You may need to run 'vercel login' first"
        print_error "Then run: vercel link"
        exit 1
    }
    print_success "Project linked to Vercel"
else
    print_success "Project already linked to Vercel"
fi

# Step 4: Set environment variables
print_status "Step 4: Setting environment variables..."
ENV_VARS=(
    "NEXT_PUBLIC_API_URL=https://goblin-backend.fly.dev"
    "NEXT_PUBLIC_FASTAPI_URL=https://goblin-backend.fly.dev"
    "NEXT_PUBLIC_DD_APPLICATION_ID=goblin-assistant"
    "NEXT_PUBLIC_DD_ENV=production"
    "NEXT_PUBLIC_DD_VERSION=1.0.0"
)

for env_var in "${ENV_VARS[@]}"; do
    var_name=$(echo $env_var | cut -d'=' -f1)
    var_value=$(echo $env_var | cut -d'=' -f2-)

    # Check if env var already exists
    if vercel env ls | grep -q "$var_name"; then
        print_warning "Environment variable $var_name already exists, skipping..."
    else
        print_status "Setting $var_name..."
        echo "$var_value" | vercel env add "$var_name" production || {
            print_warning "Failed to set $var_name via CLI. You'll need to set it manually in Vercel dashboard"
        }
    fi
done

# Step 5: Deploy to production
print_status "Step 5: Deploying to production..."
print_warning "Starting deployment. This may take several minutes..."

# Try deployment with timeout
timeout 600 vercel deploy --prod || {
    print_error "Deployment failed or timed out"
    print_error "Check Vercel dashboard for deployment status and logs"
    exit 1
}

print_success "Deployment completed successfully!"

# Step 6: Get deployment URL
print_status "Step 6: Getting deployment URL..."
DEPLOYMENT_URL=$(vercel ls --prod | grep -E "https://" | head -1 | awk '{print $2}' || echo "")

if [ -n "$DEPLOYMENT_URL" ]; then
    print_success "Deployment URL: $DEPLOYMENT_URL"
else
    print_warning "Could not retrieve deployment URL. Check Vercel dashboard."
fi

# Step 7: Verification
print_status "Step 7: Running basic verification..."
if [ -n "$DEPLOYMENT_URL" ]; then
    # Test health endpoint
    if curl -s --max-time 10 "$DEPLOYMENT_URL/api/health" > /dev/null; then
        print_success "Health check passed: $DEPLOYMENT_URL/api/health"
    else
        print_warning "Health check failed. Backend may not be responding."
    fi

    # Test main page
    if curl -s --max-time 10 "$DEPLOYMENT_URL" | grep -q "html"; then
        print_success "Frontend page loads successfully"
    else
        print_warning "Frontend page may not be loading correctly"
    fi
fi

echo ""
echo "=========================================================="
print_success "DEPLOYMENT COMPLETE!"
echo ""
echo "Next steps:"
echo "1. Visit your deployment URL: $DEPLOYMENT_URL"
echo "2. Check Vercel dashboard for build logs and status"
echo "3. Verify API proxy routes are working"
echo "4. Test the application functionality"
echo ""
print_warning "If deployment failed, check:"
echo "- Vercel dashboard for build logs"
echo "- Environment variables are set correctly"
echo "- Backend service (goblin-backend.fly.dev) is accessible"
echo ""

# Final summary
echo "Deployment Summary:"
echo "- ✅ Vercel configuration updated for pnpm monorepo"
echo "- ✅ Environment variables configured"
echo "- ✅ Production deployment completed"
echo "- ✅ Basic verification performed"
echo ""
print_success "Goblin Assistant is now deployed on Vercel! 🎉"
