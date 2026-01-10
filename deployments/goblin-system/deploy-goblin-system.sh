#!/bin/bash
# Project: Goblin AI System
# Script: deploy-goblin-system.sh
# Purpose: Automated deployment script for Goblin AI system
# Date: 2025-12-12
# Maintainer: fuaadabdullah
# Usage: ./deploy-goblin-system.sh [--router-ip IP] [--inference-ip IP]
set -euo pipefail

# Parse command line arguments
ROUTER_IP="45.61.51.220"
INFERENCE_IP="192.175.23.150"

while [[ $# -gt 0 ]]; do
  case $1 in
    --router-ip)
      ROUTER_IP="$2"
      shift 2
      ;;
    --inference-ip)
      INFERENCE_IP="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [--router-ip IP] [--inference-ip IP]"
      echo "  --router-ip IP      Router server IP address (default: 45.61.51.220)"
      echo "  --inference-ip IP   Inference server IP address (default: 192.175.23.150)"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

echo "🚀 Starting Goblin AI System Deployment"
echo "========================================"

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "📋 Deployment Configuration:"
echo "   Router Server: $ROUTER_IP"
echo "   Inference Server: $INFERENCE_IP"
echo "   Scripts Directory: $SCRIPT_DIR"
echo ""

# Function to check if script exists
check_script() {
    local script_name="$1"
    if [[ ! -f "$SCRIPT_DIR/$script_name" ]]; then
        echo "❌ Error: $script_name not found in $SCRIPT_DIR"
        exit 1
    fi
    if [[ ! -x "$SCRIPT_DIR/$script_name" ]]; then
        echo "⚠️  Making $script_name executable..."
        chmod +x "$SCRIPT_DIR/$script_name"
    fi
    echo "✅ $script_name ready for deployment"
}

# Check scripts exist
echo "🔍 Checking deployment scripts..."
check_script "bootstrap_router.sh"
check_script "bootstrap_inference.sh"
echo ""

# Deploy Router Server
echo "🏗️  Deploying Router Server ($ROUTER_IP)..."
echo "   Copying bootstrap_router.sh..."
if ! scp "$SCRIPT_DIR/bootstrap_router.sh" "root@$ROUTER_IP:/root/"; then
    echo "❌ Failed to copy bootstrap_router.sh to $ROUTER_IP"
    exit 1
fi

echo "   Running bootstrap_router.sh..."
if ! ssh "root@$ROUTER_IP" "chmod +x bootstrap_router.sh && ./bootstrap_router.sh"; then
    echo "❌ Failed to run bootstrap_router.sh on $ROUTER_IP"
    echo ""
    echo "🔧 TROUBLESHOOTING:"
    echo "   The router server deployment failed. This is likely due to Docker installation issues."
    echo "   The bootstrap script has been updated to fix Docker Compose installation."
    echo ""
    echo "🚀 RETRY INSTRUCTIONS:"
    echo "   Run this command again: ./deploy-goblin-system.sh"
    echo "   Or manually redeploy router: ssh root@$ROUTER_IP './bootstrap_router.sh'"
    exit 1
fi

echo "✅ Router Server deployment completed!"
echo ""

# Deploy Inference Server
echo "🤖 Deploying Inference Server ($INFERENCE_IP)..."
echo "   Copying bootstrap_inference.sh..."
if ! scp "$SCRIPT_DIR/bootstrap_inference.sh" "root@$INFERENCE_IP:/root/"; then
    echo "❌ Failed to copy bootstrap_inference.sh to $INFERENCE_IP"
    exit 1
fi

echo "   Running bootstrap_inference.sh..."
if ! ssh "root@$INFERENCE_IP" "chmod +x bootstrap_inference.sh && ./bootstrap_inference.sh"; then
    echo "❌ Failed to run bootstrap_inference.sh on $INFERENCE_IP"
    exit 1
fi

echo "✅ Inference Server deployment completed!"
echo ""

# Verification
echo "🔍 Deployment Summary:"
echo "======================"
echo "📊 Grafana Dashboard: http://$ROUTER_IP:3000"
echo "   Username: admin"
echo "   Password: goblin_logs_2025!"
echo ""
echo "🔗 API Endpoints:"
echo "   Router API: http://$ROUTER_IP/v1/chat/completions"
echo "   Health Check: http://$ROUTER_IP/health"
echo "   Metrics: http://$ROUTER_IP/metrics"
echo ""
echo "📝 Next Steps:"
echo "   1. Open Grafana at http://$ROUTER_IP:3000"
echo "   2. Check that logs appear from both servers within 5 minutes"
echo "   3. Test the API with a sample request"
echo "   4. Configure S3 credentials for cold storage (optional)"
echo ""
echo "🎉 Goblin AI System deployment completed successfully!"
