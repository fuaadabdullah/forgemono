#!/bin/bash

# Goblin Assistant Backend Production Deployment Script
# Supports multiple deployment platforms: Render, Fly.io, Railway

set -e

echo "🚀 Deploying Goblin Assistant Backend to Production"

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

# Render.com deployment
deploy_to_render() {
    print_step "Setting up Render.com deployment..."

    # Check if Render CLI is available
    if ! command -v render &> /dev/null; then
        print_warning "Render CLI not found. Please install it:"
        print_status "brew install render"
        print_status "Or deploy manually via Render dashboard"
        manual_render_instructions
        return
    fi

    print_warning "Render CLI v2.5.0 doesn't support service creation"
    print_status "Services must be created manually via Render dashboard"
    print_status "Once created, you can use CLI for deployments and logs"
    manual_render_instructions
}

# Fly.io deployment
deploy_to_fly() {
    print_step "Setting up Fly.io deployment..."

    # Check if Fly CLI is available
    if ! command -v fly &> /dev/null; then
        print_warning "Fly CLI not found. Please install it:"
        print_status "curl -L https://fly.io/install.sh | sh"
        manual_fly_instructions
        return
    fi

    print_status "Creating fly.toml..."
    cat > fly.toml << EOF
app = "goblin-assistant-backend"
primary_region = "iad"

[build]
  dockerfile = "Dockerfile"

[http_service]
  internal_port = 8001
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 1

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 1024

[env]
  ENV = "production"
EOF

    print_status "Deploying to Fly.io..."
    fly deploy

    print_status "Fly.io deployment completed ✓"
}

# Manual instructions for Render
manual_render_instructions() {
    echo ""
    print_status "Manual Render.com Deployment Instructions:"
    echo "1. Go to https://render.com and create a new account if needed"
    echo "2. Click 'New +' → 'Web Service'"
    echo "2. Connect your GitHub repository: fuaadabdullah/GoblinOS-Assistant-Backend"
    echo "4. Create a new Web Service with these settings:"
    echo "   - Name: goblin-assistant-backend"
    echo "   - Environment: Python 3"
    echo "   - Root Directory: (leave empty - root of repo)"
    echo "   - Build Command: pip install -r requirements.txt"
    echo "   - Start Command: python start_server.py"
    echo "5. Add environment variables from .env.production:"
    echo "   - SUPABASE_URL"
    echo "   - SUPABASE_ANON_KEY"
    echo "   - DATABASE_URL (update with your Neon password)"
    echo "   - All AI API keys (ANTHROPIC_API_KEY, DEEPSEEK_API_KEY, etc.)"
    echo "6. Click 'Create Web Service' to deploy"
    echo ""
}

# Manual instructions for Fly.io
manual_fly_instructions() {
    echo ""
    print_status "Manual Fly.io Deployment Instructions:"
    echo "1. Go to https://fly.io"
    echo "2. Install Fly CLI: curl -L https://fly.io/install.sh | sh"
    echo "3. Login: fly auth login"
    echo "4. Create app: fly launch"
    echo "5. Set secrets: fly secrets set <KEY>=<VALUE> for each env var"
    echo "6. Deploy: fly deploy"
    echo ""
}

# Get deployment URL
get_deployment_url() {
    print_step "Getting deployment URL..."

    case $PLATFORM in
        "render")
            print_status "Check Render dashboard for deployment URL"
            ;;
        "fly")
            FLY_URL=$(fly status --json | jq -r '.Hostname')
            if [ -n "$FLY_URL" ]; then
                print_status "Backend deployed at: https://$FLY_URL"
            fi
            ;;
    esac
}

# Platform selection
PLATFORM=${1:-"render"}

case $PLATFORM in
    "render")
        print_status "Deploying to Render.com"
        deploy_to_render
        ;;
    "fly")
        print_status "Deploying to Fly.io"
        deploy_to_fly
        ;;
    "railway")
        print_warning "Railway deployment (user requested to avoid)"
        print_status "Use: ./deploy-backend.sh render"
        exit 1
        ;;
    *)
        print_error "Invalid platform. Use: render, fly, or railway"
        exit 1
        ;;
esac

# Main deployment function
main() {
    echo "Goblin Assistant Backend Production Deployment"
    echo "=============================================="
    echo "Platform: $PLATFORM"
    echo ""

    # Validate environment
    if [ ! -f ".env.production" ]; then
        print_error ".env.production file not found!"
        print_status "Please create .env.production with your production environment variables"
        exit 1
    fi

    # Deploy based on platform
    case $PLATFORM in
        "render")
            deploy_to_render
            ;;
        "fly")
            deploy_to_fly
            ;;
    esac

    get_deployment_url

    echo ""
    print_status "🎉 Backend deployment initiated!"
    echo ""
    print_status "Next steps:"
    echo "1. Wait for deployment to complete"
    echo "2. Note the backend URL for frontend configuration"
    echo "3. Deploy frontend: ./deploy-frontend.sh"
    echo "4. Test the complete application"
}

# Show usage if no arguments
if [ $# -eq 0 ]; then
    echo "Usage: $0 <platform>"
    echo "Platforms: render, fly"
    echo ""
    echo "Examples:"
    echo "  $0 render    # Deploy to Render.com"
    echo "  $0 fly       # Deploy to Fly.io"
    echo ""
    exit 1
fi

# Run main function
main "$@"
