#!/usr/bin/env bash
# ForgeTM Backend Deployment Script
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
FORGE_TM_DIR="${REPO_ROOT}/ForgeTM"
BACKEND_DIR="${FORGE_TM_DIR}/apps/backend"
SMITHY_PY="${REPO_ROOT}/GoblinOS/packages/goblins/forge-smithy/.venv/bin/python"
REFRESH_WORKFLOWS="false"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required tools are available
check_dependencies() {
    log_info "Checking dependencies..."

    local missing_deps=()

    if ! command -v python3 >/dev/null 2>&1; then
        missing_deps+=("python3")
    fi

    if ! command -v uv >/dev/null 2>&1; then
        missing_deps+=("uv")
    fi

    if ! command -v docker >/dev/null 2>&1; then
        missing_deps+=("docker")
    fi

    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "Missing required dependencies: ${missing_deps[*]}"
        log_info "Please install missing dependencies and try again."
        exit 1
    fi

    if [ ! -x "${SMITHY_PY}" ]; then
        log_warning "Smithy virtualenv not found. Workflow regeneration will be skipped."
    fi

    log_success "All dependencies are available"
}

# Setup Python environment
setup_environment() {
    log_info "Setting up Python environment..."

    cd "${BACKEND_DIR}"

    # Create virtual environment if it doesn't exist
    if [ ! -d ".venv" ]; then
        log_info "Creating virtual environment..."
        python3 -m venv .venv
    fi

    # Activate virtual environment and install dependencies
    log_info "Installing/updating dependencies..."
    source .venv/bin/activate
    uv sync

    log_success "Python environment ready"
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."

    cd "${BACKEND_DIR}"
    source .venv/bin/activate

    # Run Alembic migrations
    PYTHONPATH=src uv run alembic upgrade head

    log_success "Database migrations completed"
}

regenerate_workflows() {
    if [ ! -x "${SMITHY_PY}" ]; then
        log_warning "Smithy CLI unavailable; skipping workflow regeneration"
        return
    fi

    log_info "Regenerating GitHub Actions workflows via smithy pipeline templates..."
    pushd "${BACKEND_DIR}" >/dev/null
    ${SMITHY_PY} -m smithy.cli pipeline generate python-ci python-ci.yml --branch main || \
        log_warning "Failed to regenerate python-ci workflow"
    ${SMITHY_PY} -m smithy.cli pipeline generate release release.yml --envs staging,production || \
        log_warning "Failed to regenerate release workflow"
    popd >/dev/null
}

# Run health checks
health_check() {
    log_info "Running health checks..."

    cd "${BACKEND_DIR}"
    source .venv/bin/activate

    # Start server in background for testing
    PYTHONPATH=src uv run uvicorn forge.main:app --host 127.0.0.1 --port 8000 &
    SERVER_PID=$!

    # Wait for server to start
    sleep 5

    # Test health endpoint
    if curl -s http://127.0.0.1:8000/health | grep -q '"status":"ok"'; then
        log_success "Health check passed"
    else
        log_error "Health check failed"
        kill $SERVER_PID 2>/dev/null || true
        exit 1
    fi

    # Test authentication endpoints
    if curl -s -X POST http://127.0.0.1:8000/auth/register \
        -H "Content-Type: application/json" \
        -d '{"email":"test@example.com","username":"testuser","password":"testpass123"}' | grep -q '"id"'; then
        log_success "Authentication endpoints working"
    else
        log_warning "Authentication test failed (user may already exist)"
    fi

    # Stop server
    kill $SERVER_PID 2>/dev/null || true
    sleep 2
}

# Build Docker image
build_docker() {
    log_info "Building Docker image..."

    cd "${FORGE_TM_DIR}"

    # Build Docker image
    docker build -f apps/backend/Dockerfile -t forge-backend:latest apps/backend

    log_success "Docker image built successfully"
}

# Deploy using Docker Compose
deploy_docker() {
    log_info "Deploying with Docker Compose..."

    cd "${FORGE_TM_DIR}"

    # Start services
    docker-compose up -d

    # Wait for services to be healthy
    log_info "Waiting for services to be healthy..."
    sleep 10

    # Check if services are running
    if docker-compose ps | grep -q "Up"; then
        log_success "Services deployed successfully"
    else
        log_error "Service deployment failed"
        docker-compose logs
        exit 1
    fi
}

# Main deployment function
deploy() {
    local deploy_mode="${1:-local}"

    log_info "Starting ForgeTM Backend deployment (mode: ${deploy_mode})"

    check_dependencies

    case "${deploy_mode}" in
        "local")
            if [ "${REFRESH_WORKFLOWS}" = "true" ]; then
                regenerate_workflows
            fi
            setup_environment
            run_migrations
            health_check
            log_success "Local deployment completed successfully"
            ;;
        "docker")
            build_docker
            deploy_docker
            log_success "Docker deployment completed successfully"
            ;;
        "production")
            log_warning "Production deployment not yet implemented"
            log_info "Use 'docker' mode for containerized deployment"
            exit 1
            ;;
        *)
            log_error "Unknown deployment mode: ${deploy_mode}"
            log_info "Available modes: local, docker, production"
            exit 1
            ;;
    esac
}

# Cleanup function
cleanup() {
    log_info "Cleaning up..."

    # Stop any running servers
    pkill -f uvicorn || true
    pkill -f "uvicorn forge.main:app" || true

    # Stop Docker services if running
    cd "${FORGE_TM_DIR}"
    docker-compose down 2>/dev/null || true

    log_success "Cleanup completed"
}

# Show usage
usage() {
    cat << EOF
ForgeTM Backend Deployment Script

USAGE:
    $0 [OPTIONS] [MODE]

MODES:
    local       Deploy locally with virtual environment (default)
    docker      Deploy using Docker Compose
    production  Deploy to production (not yet implemented)

OPTIONS:
    -h, --help  Show this help message
    --cleanup   Clean up running services and exit
    --refresh-workflows  Regenerate GitHub Actions workflows before deployment (local mode)

EXAMPLES:
    $0                    # Deploy locally
    $0 docker             # Deploy with Docker
    $0 --cleanup          # Clean up and exit

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                usage
                exit 0
                ;;
            --cleanup)
                cleanup
                exit 0
                ;;
            --refresh-workflows)
                REFRESH_WORKFLOWS="true"
                shift
                ;;
            -*)
                log_error "Unknown option: $1"
                usage
                exit 1
                ;;
            *)
                DEPLOY_MODE="$1"
                shift
                ;;
        esac
    done
}

# Main script
main() {
    local DEPLOY_MODE="local"

    # Parse arguments
    parse_args "$@"

    # Set trap for cleanup on exit
    trap cleanup EXIT

    # Run deployment
    deploy "${DEPLOY_MODE}"
}

# Run main function with all arguments
main "$@"
