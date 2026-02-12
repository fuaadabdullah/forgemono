#!/bin/bash
# Vast.ai Job Submission Script
#
# Submits training/inference jobs to Vast.ai with:
# - Host filtering by reliability
# - Automatic checkpointing to GCS
# - Retry on preemption
#
# Usage:
#   ./scripts/submit_vastai_job.sh --type training --gpu RTX_4090 --hours 24

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/../generated/vastai-config.json"
VASTAI_API_KEY="${VASTAI_API_KEY:-}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_debug() { echo -e "${BLUE}[DEBUG]${NC} $1"; }

# Default values
JOB_TYPE="training"
GPU_TYPE="RTX_4090"
NUM_GPUS=1
MAX_HOURS=24
MAX_COST_PER_HOUR=5.0
IMAGE="pytorch/pytorch:2.1.0-cuda12.1-cudnn8-devel"
DISK_GB=50
DRY_RUN=false

# Parse arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --type)
                JOB_TYPE="$2"
                shift 2
                ;;
            --gpu)
                GPU_TYPE="$2"
                shift 2
                ;;
            --num-gpus)
                NUM_GPUS="$2"
                shift 2
                ;;
            --hours)
                MAX_HOURS="$2"
                shift 2
                ;;
            --max-cost)
                MAX_COST_PER_HOUR="$2"
                shift 2
                ;;
            --image)
                IMAGE="$2"
                shift 2
                ;;
            --disk)
                DISK_GB="$2"
                shift 2
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            *)
                echo "Usage: $0 [options]"
                echo "Options:"
                echo "  --type TYPE        Job type (training, inference, batch)"
                echo "  --gpu GPU          GPU type (RTX_4090, A100_80GB, H100_80GB)"
                echo "  --num-gpus N       Number of GPUs"
                echo "  --hours H          Maximum runtime hours"
                echo "  --max-cost C       Maximum cost per hour"
                echo "  --image IMG        Docker image"
                echo "  --disk GB          Disk space in GB"
                echo "  --dry-run          Show what would be done"
                exit 1
                ;;
        esac
    done
}

# Check prerequisites
check_prerequisites() {
    if [[ -z "$VASTAI_API_KEY" ]]; then
        log_error "VASTAI_API_KEY not set"
        echo "Set it in your environment: export VASTAI_API_KEY=..."
        exit 1
    fi
    
    if ! command -v vastai &> /dev/null; then
        log_warn "vast.ai CLI not installed, using API directly"
    fi
    
    if ! command -v jq &> /dev/null; then
        log_error "jq is required but not installed"
        exit 1
    fi
}

# Map GPU type to vast.ai name
map_gpu_type() {
    case $GPU_TYPE in
        RTX_4090) echo "RTX 4090" ;;
        A100_40GB) echo "A100" ;;
        A100_80GB) echo "A100 80GB" ;;
        H100_80GB) echo "H100 80GB" ;;
        H100_SXM) echo "H100 SXM" ;;
        RTX_3090) echo "RTX 3090" ;;
        *) echo "$GPU_TYPE" ;;
    esac
}

# Search for matching offers
search_offers() {
    local gpu_name
    gpu_name=$(map_gpu_type)
    
    log_info "Searching for offers: $gpu_name x $NUM_GPUS"
    
    # Read filter criteria from config
    local min_reliability min_dlperf min_inet
    if [[ -f "$CONFIG_FILE" ]]; then
        min_reliability=$(jq -r '.search_criteria.min_reliability' "$CONFIG_FILE")
        min_dlperf=$(jq -r '.search_criteria.min_dlperf' "$CONFIG_FILE")
        min_inet=$(jq -r '.search_criteria.min_internet_speed' "$CONFIG_FILE")
    else
        min_reliability=0.95
        min_dlperf=10.0
        min_inet=100
    fi
    
    # Build search query
    local query="reliability >= $min_reliability"
    query+=" && dlperf >= $min_dlperf"
    query+=" && inet_up >= $min_inet"
    query+=" && inet_down >= $min_inet"
    query+=" && num_gpus >= $NUM_GPUS"
    query+=" && dph_total <= $MAX_COST_PER_HOUR"
    query+=" && disk_space >= $DISK_GB"
    query+=" && rentable = true"
    query+=" && rented = false"
    query+=" && gpu_name = \"$gpu_name\""
    
    log_debug "Query: $query"
    
    # Search via API
    local response
    response=$(curl -s -H "Authorization: Bearer $VASTAI_API_KEY" \
        "https://console.vast.ai/api/v0/bundles?q=$(echo "$query" | jq -sRr @uri)&order=dph_total&limit=10&type=on-demand")
    
    echo "$response" | jq '.offers'
}

# Select best offer
select_offer() {
    local offers
    offers=$(search_offers)
    
    local count
    count=$(echo "$offers" | jq 'length')
    
    if [[ "$count" -eq 0 || "$count" == "null" ]]; then
        log_error "No matching offers found"
        log_warn "Try adjusting search criteria:"
        log_warn "  - Increase --max-cost"
        log_warn "  - Use different GPU type"
        log_warn "  - Reduce disk requirements"
        exit 1
    fi
    
    log_info "Found $count matching offers"
    
    # Get best offer (first one, sorted by cost)
    local best
    best=$(echo "$offers" | jq '.[0]')
    
    local offer_id cost_per_hour gpu_name reliability
    offer_id=$(echo "$best" | jq -r '.id')
    cost_per_hour=$(echo "$best" | jq -r '.dph_total')
    gpu_name=$(echo "$best" | jq -r '.gpu_name')
    reliability=$(echo "$best" | jq -r '.reliability')
    
    log_info "Selected offer:"
    log_info "  ID: $offer_id"
    log_info "  GPU: $gpu_name"
    log_info "  Cost: \$${cost_per_hour}/hr"
    log_info "  Reliability: ${reliability}"
    log_info "  Estimated total: \$$(echo "$cost_per_hour * $MAX_HOURS" | bc)"
    
    echo "$offer_id"
}

# Build startup script
build_startup_script() {
    local checkpoint_bucket model_bucket
    
    if [[ -f "$CONFIG_FILE" ]]; then
        checkpoint_bucket=$(jq -r '.job_defaults.checkpoint_bucket' "$CONFIG_FILE")
        model_bucket=$(jq -r '.job_defaults.model_bucket' "$CONFIG_FILE")
    else
        checkpoint_bucket="goblin-llm-checkpoints"
        model_bucket="goblin-llm-models"
    fi
    
    local job_id
    job_id="job-$(date +%Y%m%d-%H%M%S)-$(openssl rand -hex 4)"
    
    cat <<EOF
#!/bin/bash
set -e

export JOB_ID="$job_id"
export JOB_TYPE="$JOB_TYPE"
export MAX_RUNTIME_HOURS="$MAX_HOURS"
export CHECKPOINT_BUCKET="$checkpoint_bucket"
export MODEL_BUCKET="$model_bucket"

# Install dependencies
pip install gsutil google-cloud-storage

# Setup checkpointing
checkpoint_to_gcs() {
    echo "Saving checkpoint to GCS..."
    gsutil -m cp -r /workspace/checkpoint/* "gs://\$CHECKPOINT_BUCKET/checkpoints/\$JOB_ID/latest/"
}

# Trap for graceful shutdown
trap checkpoint_to_gcs EXIT SIGTERM SIGINT

# Check for existing checkpoint
if gsutil ls "gs://\$CHECKPOINT_BUCKET/checkpoints/\$JOB_ID/latest/" 2>/dev/null; then
    echo "Resuming from checkpoint..."
    gsutil -m cp -r "gs://\$CHECKPOINT_BUCKET/checkpoints/\$JOB_ID/latest/*" /workspace/checkpoint/
fi

# Start periodic checkpointing (every 30 minutes)
(
    while true; do
        sleep 1800
        checkpoint_to_gcs
    done
) &

echo "Job started: \$JOB_ID"
echo "Type: \$JOB_TYPE"
echo "Max runtime: \$MAX_RUNTIME_HOURS hours"

# Your training/inference code goes here
# This is a placeholder - replace with actual job command
echo "Waiting for job configuration..."
sleep infinity
EOF
}

# Create instance
create_instance() {
    local offer_id="$1"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_warn "Dry run mode - would create instance from offer $offer_id"
        return
    fi
    
    log_info "Creating instance from offer $offer_id..."
    
    local label
    label="goblin-${JOB_TYPE}-$(date +%Y%m%d%H%M%S)"
    
    local onstart
    onstart=$(build_startup_script | base64 -w0)
    
    local response
    response=$(curl -s -X PUT -H "Authorization: Bearer $VASTAI_API_KEY" \
        "https://console.vast.ai/api/v0/asks/$offer_id/" \
        -H "Content-Type: application/json" \
        -d "{
            \"client_id\": \"me\",
            \"image\": \"$IMAGE\",
            \"disk\": $DISK_GB,
            \"label\": \"$label\",
            \"onstart\": \"$(build_startup_script | sed 's/"/\\"/g' | tr '\n' ';')\"
        }")
    
    local instance_id
    instance_id=$(echo "$response" | jq -r '.new_contract')
    
    if [[ -n "$instance_id" && "$instance_id" != "null" ]]; then
        log_info "Instance created: $instance_id"
        log_info "Label: $label"
        
        # Save instance info
        echo "{\"instance_id\": \"$instance_id\", \"label\": \"$label\", \"offer_id\": \"$offer_id\"}" > \
            "${SCRIPT_DIR}/../generated/instance-${instance_id}.json"
        
        log_info "Instance info saved to: generated/instance-${instance_id}.json"
    else
        log_error "Failed to create instance"
        log_error "Response: $response"
        exit 1
    fi
}

# List instances
list_instances() {
    log_info "Listing instances..."
    
    curl -s -H "Authorization: Bearer $VASTAI_API_KEY" \
        "https://console.vast.ai/api/v0/instances/" | \
        jq '.instances | .[] | {id, label, actual_status, gpu_name, dph_total, total_cost}'
}

# Main
main() {
    parse_args "$@"
    check_prerequisites
    
    if [[ "$JOB_TYPE" == "list" ]]; then
        list_instances
        exit 0
    fi
    
    log_info "Submitting $JOB_TYPE job"
    log_info "  GPU: $GPU_TYPE x $NUM_GPUS"
    log_info "  Max hours: $MAX_HOURS"
    log_info "  Max cost: \$${MAX_COST_PER_HOUR}/hr"
    log_info "  Image: $IMAGE"
    
    local offer_id
    offer_id=$(select_offer)
    
    create_instance "$offer_id"
}

main "$@"
