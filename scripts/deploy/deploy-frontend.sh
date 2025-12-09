#!/bin/bash

# NOTE: Netlify frontend deployment support removed across the repo.
# Use the frontend's `deploy-vercel.sh` script or CI for Vercel deployments.

echo "⚠️  Netlify support removed. Use deploy-vercel.sh or Vercel dashboard for frontend deployment."
exit 0

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

# Check if Netlify CLI is installed
check_netlify_cli() {
    print_step "Checking Netlify CLI..."

    if ! command -v netlify &> /dev/null; then
        print_status "Installing Netlify CLI..."
        npm install -g netlify-cli
    fi

    print_status "Netlify CLI ready ✓"
}

# Check if logged in to Netlify
check_netlify_auth() {
    print_step "Checking Netlify authentication..."

    # Try to get user info - if this fails, user is not logged in
    if ! netlify api getCurrentUser &> /dev/null; then
        print_error "Not logged in to Netlify"
        print_status "Please run: netlify login"
        exit 1
    fi

    print_status "Netlify authentication confirmed ✓"
}

# Setup Netlify site
setup_netlify_site() {
    print_step "Setting up Netlify site..."

    # Check if site already exists
    if [ -f ".netlify/state.json" ]; then
        print_status "Netlify site already configured"
        return
    fi

    print_status "Creating new Netlify site..."
    # Create a new site without linking to git
    SITE_NAME="goblin-assistant-$(date +%s)"
    netlify sites:create --name "$SITE_NAME" --with-ci

    print_status "Netlify site created ✓"
}

# Set environment variables
set_environment_variables() {
    print_step "Setting environment variables..."

    if [ ! -f ".env.production" ]; then
        print_error ".env.production file not found!"
        print_status "Please create .env.production with your production environment variables"
        exit 1
    fi

    print_status "Setting production environment variables..."
    # Set environment variables from .env.production
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ $key =~ ^#.*$ ]] && continue
        [[ -z $key ]] && continue

        # Only set VITE_ variables for frontend
        if [[ $key == VITE_* ]]; then
            print_status "Setting $key..."
            netlify env:set "$key" "$value"
        fi
    done < ".env.production"

    print_status "Environment variables set ✓"
}

# Build and deploy
build_and_deploy() {
    print_step "Building and deploying..."

    print_status "Building application..."
    npm run build

    print_status "Deploying to Netlify..."
    netlify deploy --prod --dir=dist

    print_status "Deployment completed ✓"
}

# Get deployment URL
get_deployment_url() {
    print_step "Getting deployment URL..."

    # Get the deployment URL from Netlify
    DEPLOYMENT_URL=$(netlify status | grep "Site URL:" | awk '{print $3}')

    if [ -n "$DEPLOYMENT_URL" ]; then
        print_status "Frontend deployed at: $DEPLOYMENT_URL"
    else
        print_warning "Could not retrieve deployment URL automatically"
        print_status "Check Netlify dashboard for the deployment URL"
    fi
}

# Main deployment function
main() {
    echo "Goblin Assistant Frontend Production Deployment"
    echo "==============================================="

    check_netlify_cli
    check_netlify_auth
    setup_netlify_site
    set_environment_variables
    build_and_deploy
    get_deployment_url

    echo ""
    print_status "🎉 Frontend deployment completed successfully!"
    echo ""
    print_status "Next steps:"
    echo "1. Test the complete application"
    echo "2. Set up monitoring and analytics"
    echo "3. Configure custom domain (optional)"
}

# Run main function
main "$@"
