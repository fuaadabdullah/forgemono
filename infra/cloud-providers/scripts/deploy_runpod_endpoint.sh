#!/bin/bash
# Deploy RunPod Serverless Endpoint
#
# Prerequisites:
# - RunPod API key set in environment or tfvars
# - Terraform applied to generate config
#
# Usage:
#   ./scripts/deploy_runpod_endpoint.sh [--dry-run]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/../generated/runpod-config.json"
RUNPOD_API_KEY="${RUNPOD_API_KEY:-}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check prerequisites
check_prerequisites() {
    if [[ -z "$RUNPOD_API_KEY" ]]; then
        log_error "RUNPOD_API_KEY not set"
        echo "Set it in your environment: export RUNPOD_API_KEY=rpa_..."
        exit 1
    fi
    
    if [[ ! -f "$CONFIG_FILE" ]]; then
        log_error "Config file not found: $CONFIG_FILE"
        echo "Run 'terraform apply' first to generate the config"
        exit 1
    fi
    
    if ! command -v jq &> /dev/null; then
        log_error "jq is required but not installed"
        exit 1
    fi
}

# Create or update RunPod endpoint
deploy_endpoint() {
    local dry_run="${1:-false}"
    
    # Read config
    local endpoint_name
    endpoint_name=$(jq -r '.endpoint_name' "$CONFIG_FILE")
    local gpu_types
    gpu_types=$(jq -r '.config.gpu_types | join(",")' "$CONFIG_FILE")
    local min_workers
    min_workers=$(jq -r '.config.min_workers' "$CONFIG_FILE")
    local max_workers
    max_workers=$(jq -r '.config.max_workers' "$CONFIG_FILE")
    local idle_timeout
    idle_timeout=$(jq -r '.config.idle_timeout' "$CONFIG_FILE")
    
    log_info "Deploying RunPod endpoint: $endpoint_name"
    log_info "  GPU Types: $gpu_types"
    log_info "  Workers: $min_workers - $max_workers"
    log_info "  Idle Timeout: ${idle_timeout}s"
    
    if [[ "$dry_run" == "true" ]]; then
        log_warn "Dry run mode - no changes will be made"
        return
    fi
    
    # Check if endpoint exists
    local existing
    existing=$(curl -s -H "Authorization: Bearer $RUNPOD_API_KEY" \
        "https://api.runpod.io/graphql" \
        -H "Content-Type: application/json" \
        -d '{"query": "query { myself { endpoints { id name } } }"}' | \
        jq -r ".data.myself.endpoints[] | select(.name == \"$endpoint_name\") | .id")
    
    if [[ -n "$existing" ]]; then
        log_info "Endpoint exists with ID: $existing"
        log_info "Updating endpoint configuration..."
        
        # Update endpoint
        curl -s -H "Authorization: Bearer $RUNPOD_API_KEY" \
            "https://api.runpod.io/graphql" \
            -H "Content-Type: application/json" \
            -d "{
                \"query\": \"mutation { updateEndpoint(input: { id: \\\"$existing\\\", minWorkers: $min_workers, maxWorkers: $max_workers, idleTimeout: $idle_timeout }) { id } }\"
            }"
        
        log_info "Endpoint updated successfully"
    else
        log_info "Creating new endpoint..."
        log_warn "Manual endpoint creation via API is limited"
        log_warn "Please create the endpoint via the RunPod dashboard:"
        log_warn "  1. Go to https://www.runpod.io/console/serverless"
        log_warn "  2. Create new endpoint with name: $endpoint_name"
        log_warn "  3. Configure GPU types and scaling settings"
    fi
}

# Get endpoint status
get_endpoint_status() {
    log_info "Fetching endpoint status..."
    
    curl -s -H "Authorization: Bearer $RUNPOD_API_KEY" \
        "https://api.runpod.io/graphql" \
        -H "Content-Type: application/json" \
        -d '{"query": "query { myself { endpoints { id name workersMax workersMin idleTimeout gpuIds } } }"}' | \
        jq '.data.myself.endpoints'
}

# Main
main() {
    local dry_run=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                dry_run=true
                shift
                ;;
            --status)
                check_prerequisites
                get_endpoint_status
                exit 0
                ;;
            *)
                echo "Usage: $0 [--dry-run] [--status]"
                exit 1
                ;;
        esac
    done
    
    check_prerequisites
    deploy_endpoint "$dry_run"
}

main "$@"
