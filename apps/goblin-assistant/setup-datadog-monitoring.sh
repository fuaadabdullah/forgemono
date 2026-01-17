#!/bin/bash

# Datadog Monitoring Setup Script
# This script helps configure Datadog RUM monitoring for the Goblin Assistant

set -e

echo "📊 Setting up Datadog Monitoring for Goblin Assistant"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Previously required Netlify CLI; Netlify deployment support has been removed.
# The script now writes environment variables to .env.production and advises
# the user to set platform-specific environment variables (e.g., Vercel, Fly, or other).

# Get Datadog credentials from user
get_datadog_credentials() {
    print_step "Datadog RUM Setup"

    echo ""
    echo "You need to create a Datadog RUM application first."
    echo "Go to: https://app.datadoghq.com/rum/applications"
    echo ""
    echo "1. Click 'Add Application'"
    echo "2. Application Type: Web"
    echo "3. Name: 'Goblin Assistant Frontend'"
    echo "4. Environment: production"
    echo ""

    read -p "Enter your Datadog Application ID: " DD_APP_ID
    read -p "Enter your Datadog Client Token: " DD_CLIENT_TOKEN

    if [ -z "$DD_APP_ID" ] || [ -z "$DD_CLIENT_TOKEN" ]; then
        print_error "Both Application ID and Client Token are required"
        exit 1
    fi

    print_status "Credentials received ✓"
}

# Update environment variables (written to .env.production)
update_env_file() {
    print_step "Writing environment variables to .env.production..."

    env_file=".env.production"
    echo "VITE_DD_APPLICATION_ID=$DD_APP_ID" > "$env_file"
    echo "VITE_DD_CLIENT_TOKEN=$DD_CLIENT_TOKEN" >> "$env_file"
    echo "VITE_DD_ENV=production" >> "$env_file"
    echo "VITE_DD_VERSION=1.0.0" >> "$env_file"
    echo "VITE_FASTAPI_URL=https://api.goblin-assistant.com" >> "$env_file"
    echo "VITE_GOBLIN_RUNTIME=fastapi" >> "$env_file"
    echo "VITE_MOCK_API=false" >> "$env_file"

    print_status "Env vars written to $env_file"
    print_status "Please set these variables in your hosting provider dashboard (e.g., Vercel) for production deployments."
}

# Test the setup
test_setup() {
    print_step "Testing monitoring setup..."

    # Build and deploy to test
    npm run build

    # Start preview server
    npm run preview &
    PREVIEW_PID=$!

    sleep 3

    # Test if Datadog is loaded
    if curl -s http://localhost:4173 | grep -q "datadog"; then
        print_status "Datadog RUM detected in build ✓"
    else
        print_warning "Datadog RUM not detected. Check your build configuration."
    fi

    # Kill preview server
    kill $PREVIEW_PID 2>/dev/null || true
}

# Redeploy to production
redeploy_production() {
    print_step "Redeploying to production with monitoring..."

    print_status "Triggering production deployment via supported provider..."
    print_status "This script doesn't trigger provider deployments; run your platform command (e.g., 'vercel --prod') or use your CI."

    print_status "Redeploy step complete - ensure your hosting provider picks up the updated env vars."
}

# Main setup function
main() {
    get_datadog_credentials
    update_env_file
    test_setup
    redeploy_production

    echo ""
    print_status "🎉 Datadog monitoring setup completed!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Visit your production URL (e.g., https://goblin.fuaad.ai or Vercel host)"
    echo "2. Check Datadog RUM dashboard for user sessions"
    echo "3. Generate some test errors to verify error tracking"
    echo "4. Set up alerts in Datadog (see PRODUCTION_DATADOG_SETUP.md)"
    echo ""
    echo "🔗 Useful links:"
    echo "   Datadog RUM Dashboard: https://app.datadoghq.com/rum/overview"
    echo "   Error Explorer: https://app.datadoghq.com/rum/explorer"
}

# Run main function
main "$@"
