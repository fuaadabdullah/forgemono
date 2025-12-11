#!/bin/bash
# Goblin Assistant Production Deployment with OpenTelemetry
# This script deploys the complete observability stack to production

set -e

echo "🚀 Starting Goblin Assistant Production Deployment with OpenTelemetry"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="/Users/fuaadabdullah/ForgeMonorepo"
GOBLIN_INFRA_DIR="$PROJECT_ROOT/goblin-infra/projects/goblin-assistant"
BACKEND_DIR="$PROJECT_ROOT/apps/goblin-assistant/backend"

# Function to print status
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    echo "🔍 Checking prerequisites..."

    # Check if required tools are installed
    command -v docker >/dev/null 2>&1 || { print_error "Docker is required but not installed."; exit 1; }
    command -v terraform >/dev/null 2>&1 || { print_error "Terraform is required but not installed."; exit 1; }
    command -v wrangler >/dev/null 2>&1 || { print_error "Wrangler is required but not installed."; exit 1; }

    # Check if required files exist
    [[ -f "$GOBLIN_INFRA_DIR/infra/cloudflare/worker.js" ]] || { print_error "Cloudflare Worker file not found."; exit 1; }
    [[ -f "$GOBLIN_INFRA_DIR/infra/otel-collector-config.yaml" ]] || { print_error "OTLP Collector config not found."; exit 1; }
    [[ -f "$GOBLIN_INFRA_DIR/infra/alert_rules.yml" ]] || { print_error "Alert rules file not found."; exit 1; }

    print_status "Prerequisites check passed"
}

# Deploy OTLP Collector
deploy_otel_collector() {
    echo "📊 Deploying OTLP Collector..."

    cd "$GOBLIN_INFRA_DIR/infra"

    # Start OTLP Collector with Docker Compose
    docker-compose up -d otel-collector

    # Wait for collector to be ready
    echo "Waiting for OTLP Collector to be ready..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if curl -f http://localhost:4318/health >/dev/null 2>&1; then
            break
        fi
        sleep 2
        timeout=$((timeout - 2))
    done

    if [ $timeout -le 0 ]; then
        print_error "OTLP Collector failed to start"
        exit 1
    fi

    print_status "OTLP Collector deployed successfully"
}

# Deploy Cloudflare Worker
deploy_cloudflare_worker() {
    echo "☁️ Deploying Cloudflare Worker with OpenTelemetry..."

    cd "$GOBLIN_INFRA_DIR/infra/cloudflare"

    # Deploy worker
    wrangler deploy

    print_status "Cloudflare Worker deployed successfully"
}

# Enable OpenTelemetry in backend
enable_opentelemetry_backend() {
    echo "🔧 Enabling OpenTelemetry in backend..."

    cd "$BACKEND_DIR"

    # Set environment variable
    export ENABLE_OPENTELEMETRY=true

    # Update .env file if it exists
    if [[ -f ".env" ]]; then
        if grep -q "ENABLE_OPENTELEMETRY" .env; then
            sed -i.bak 's/ENABLE_OPENTELEMETRY=.*/ENABLE_OPENTELEMETRY=true/' .env
        else
            echo "ENABLE_OPENTELEMETRY=true" >> .env
        fi
    else
        echo "ENABLE_OPENTELEMETRY=true" > .env
    fi

    print_status "OpenTelemetry enabled in backend"
}

# Deploy monitoring stack
deploy_monitoring_stack() {
    echo "📈 Deploying monitoring stack..."

    cd "$GOBLIN_INFRA_DIR/infra"

    # Start Prometheus, Grafana, and Jaeger
    docker-compose up -d prometheus grafana jaeger

    # Wait for services to be ready
    echo "Waiting for monitoring services to be ready..."
    sleep 10

    # Import Grafana dashboard
    curl -X POST -H "Content-Type: application/json" \
         -d @grafana-dashboard.json \
         http://admin:admin@localhost:3000/api/dashboards/db

    print_status "Monitoring stack deployed successfully"
}

# Configure alerting
configure_alerting() {
    echo "🚨 Configuring alerting..."

    cd "$GOBLIN_INFRA_DIR/infra"

    # Copy alert rules to Prometheus
    docker cp alert_rules.yml goblin-infra_prometheus_1:/etc/prometheus/alert_rules.yml

    # Reload Prometheus configuration
    docker exec goblin-infra_prometheus_1 kill -HUP 1

    print_status "Alerting configured successfully"
}

# Validate deployment
validate_deployment() {
    echo "✅ Validating deployment..."

    # Check if services are running
    docker ps | grep -q "otel-collector" || { print_error "OTLP Collector not running"; exit 1; }
    docker ps | grep -q "prometheus" || { print_error "Prometheus not running"; exit 1; }
    docker ps | grep -q "grafana" || { print_error "Grafana not running"; exit 1; }

    # Check Cloudflare Worker
    wrangler tail --format=pretty | head -1 >/dev/null 2>&1 || print_warning "Could not verify Cloudflare Worker status"

    # Test OTLP endpoint
    curl -f http://localhost:4318/health >/dev/null 2>&1 || { print_error "OTLP Collector health check failed"; exit 1; }

    print_status "Deployment validation passed"
}

# Main deployment flow
main() {
    echo "🎯 Starting Goblin Assistant OpenTelemetry Production Deployment"
    echo "========================================================"

    check_prerequisites
    deploy_otel_collector
    deploy_cloudflare_worker
    enable_opentelemetry_backend
    deploy_monitoring_stack
    configure_alerting
    validate_deployment

    echo ""
    echo "🎉 Deployment completed successfully!"
    echo ""
    echo "📊 Monitoring URLs:"
    echo "  - Grafana: http://localhost:3000 (admin/admin)"
    echo "  - Prometheus: http://localhost:9090"
    echo "  - Jaeger: http://localhost:16686"
    echo ""
    echo "☁️ Cloudflare Worker: https://goblin-assistant-edge.fuaadabdullah.workers.dev"
    echo ""
    echo "🔍 Next steps:"
    echo "  1. Monitor SLO compliance in Grafana dashboard"
    echo "  2. Check trace propagation in Jaeger"
    echo "  3. Review alerts in Prometheus Alertmanager"
    echo "  4. Validate end-to-end tracing from Cloudflare to backend"
}

# Run main function
main "$@"
