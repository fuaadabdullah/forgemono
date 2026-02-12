#!/bin/bash
# Comprehensive AI Resource Monitoring Script
# Monitors CPU, memory, GPU, disk, and network usage for AI services

set -euo pipefail

# Configuration
LOG_DIR="/var/log/ai-monitoring"
METRICS_FILE="$LOG_DIR/metrics.json"
ALERT_LOG="$LOG_DIR/alerts.log"
PROMETHEUS_METRICS="$LOG_DIR/prometheus_metrics.txt"

# Alert thresholds
MEMORY_ALERT_THRESHOLD=85
CPU_ALERT_THRESHOLD=90
DISK_ALERT_THRESHOLD=90
SWAP_ALERT_THRESHOLD=70

# Create log directory
mkdir -p "$LOG_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" >&2
}

log_alert() {
    echo -e "${RED}[ALERT $(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" >&2
    echo "$(date '+%Y-%m-%d %H:%M:%S') ALERT: $1" >> "$ALERT_LOG"
}

# Get system memory info
get_memory_info() {
    local total_mem_kb used_mem_kb free_mem_kb available_mem_kb
    read -r total_mem_kb used_mem_kb free_mem_kb available_mem_kb <<< "$(free | awk 'NR==2{print $2,$3,$4,$7}')"

    local total_mem_gb used_mem_gb free_mem_gb available_mem_gb
    total_mem_gb=$((total_mem_kb / 1024 / 1024))
    used_mem_gb=$((used_mem_kb / 1024 / 1024))
    free_mem_gb=$((free_mem_kb / 1024 / 1024))
    available_mem_gb=$((available_mem_kb / 1024 / 1024))

    local mem_percent=$((used_mem_kb * 100 / total_mem_kb))

    # Check for alerts
    if [[ $mem_percent -gt $MEMORY_ALERT_THRESHOLD ]]; then
        log_alert "High memory usage: ${mem_percent}% (${used_mem_gb}GB/${total_mem_gb}GB)"
    fi

    cat << EOF
{
  "memory": {
    "total_gb": $total_mem_gb,
    "used_gb": $used_mem_gb,
    "free_gb": $free_mem_gb,
    "available_gb": $available_mem_gb,
    "usage_percent": $mem_percent
  }
}
EOF
}

# Get swap info
get_swap_info() {
    local total_swap_kb used_swap_kb
    read -r total_swap_kb used_swap_kb <<< "$(free | awk '/Swap/{print $2,$3}')"

    if [[ $total_swap_kb -eq 0 ]]; then
        cat << EOF
{
  "swap": {
    "total_gb": 0,
    "used_gb": 0,
    "usage_percent": 0
  }
}
EOF
        return
    fi

    local total_swap_gb used_swap_gb swap_percent
    total_swap_gb=$((total_swap_kb / 1024 / 1024))
    used_swap_gb=$((used_swap_kb / 1024 / 1024))
    swap_percent=$((used_swap_kb * 100 / total_swap_kb))

    # Check for alerts
    if [[ $swap_percent -gt $SWAP_ALERT_THRESHOLD ]]; then
        log_alert "High swap usage: ${swap_percent}% (${used_swap_gb}GB/${total_swap_gb}GB)"
    fi

    cat << EOF
{
  "swap": {
    "total_gb": $total_swap_gb,
    "used_gb": $used_swap_gb,
    "usage_percent": $swap_percent
  }
}
EOF
}

# Get CPU info
get_cpu_info() {
    local cpu_usage
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')

    # Check for alerts
    if [[ $(echo "$cpu_usage > $CPU_ALERT_THRESHOLD" | bc -l) -eq 1 ]]; then
        log_alert "High CPU usage: ${cpu_usage}%"
    fi

    # Get load average
    local load_avg
    read -r load_avg <<< "$(uptime | awk -F'load average:' '{ print $2 }' | sed 's/,//g')"

    cat << EOF
{
  "cpu": {
    "usage_percent": $cpu_usage,
    "load_average": "$load_avg"
  }
}
EOF
}

# Get disk info for AI models directory
get_disk_info() {
    local mount_point="/srv/models"
    if [[ ! -d "$mount_point" ]]; then
        mount_point="/srv/ai/models"
    fi
    if [[ ! -d "$mount_point" ]]; then
        mount_point="/"
    fi

    local total_kb used_kb available_kb usage_percent
    read -r total_kb used_kb available_kb usage_percent <<< "$(df "$mount_point" | awk 'NR==2{print $2,$3,$4,$5}' | sed 's/%//')"

    local total_gb used_gb available_gb
    total_gb=$((total_kb / 1024 / 1024))
    used_gb=$((used_kb / 1024 / 1024))
    available_gb=$((available_kb / 1024 / 1024))

    # Check for alerts
    if [[ $usage_percent -gt $DISK_ALERT_THRESHOLD ]]; then
        log_alert "High disk usage on $mount_point: ${usage_percent}% (${used_gb}GB/${total_gb}GB)"
    fi

    cat << EOF
{
  "disk": {
    "mount_point": "$mount_point",
    "total_gb": $total_gb,
    "used_gb": $used_gb,
    "available_gb": $available_gb,
    "usage_percent": $usage_percent
  }
}
EOF
}

# Get service-specific resource usage
get_service_info() {
    local services=("ollama" "llamacpp" "local-llm-proxy")
    local service_info="{"

    for service in "${services[@]}"; do
        if systemctl is-active --quiet "$service" 2>/dev/null; then
            # Get memory usage
            local mem_bytes mem_limit_bytes
            mem_bytes=$(systemctl show "$service" -p MemoryCurrent --value 2>/dev/null || echo "0")
            mem_limit_bytes=$(systemctl show "$service" -p MemoryLimit --value 2>/dev/null || echo "0")

            local mem_mb="0"
            local mem_limit_mb="0"
            local mem_percent="0"

            if [[ $mem_bytes != "0" && -n "$mem_bytes" ]]; then
                mem_mb=$((mem_bytes / 1024 / 1024))
            fi
            if [[ $mem_limit_bytes != "0" && -n "$mem_limit_bytes" ]]; then
                mem_limit_mb=$((mem_limit_bytes / 1024 / 1024))
                if [[ $mem_limit_mb -gt 0 ]]; then
                    mem_percent=$((mem_mb * 100 / mem_limit_mb))
                fi
            fi

            # Get CPU usage (rough estimate)
            local cpu_nsec
            cpu_nsec=$(systemctl show "$service" -p CPUUsageNSec --value 2>/dev/null || echo "0")
            local cpu_percent="0"
            if [[ $cpu_nsec != "0" && -n "$cpu_nsec" ]]; then
                # Convert to rough percentage (this is approximate)
                cpu_percent=$((cpu_nsec / 100000000))
            fi

            service_info="${service_info}\"$service\": {\"memory_mb\": $mem_mb, \"memory_limit_mb\": $mem_limit_mb, \"memory_percent\": $mem_percent, \"cpu_percent\": $cpu_percent},"
        fi
    done

    # Remove trailing comma and close JSON
    service_info="${service_info%,}}"

    cat << EOF
{
  "services": $service_info
}
EOF
}

# Get GPU info (if available)
get_gpu_info() {
    if command -v nvidia-smi &> /dev/null; then
        local gpu_usage gpu_memory
        gpu_usage=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits | head -1)
        gpu_memory=$(nvidia-smi --query-gpu=utilization.memory --format=csv,noheader,nounits | head -1)

        cat << EOF
{
  "gpu": {
    "available": true,
    "gpu_utilization_percent": $gpu_usage,
    "memory_utilization_percent": $gpu_memory
  }
}
EOF
    else
        cat << EOF
{
  "gpu": {
    "available": false
  }
}
EOF
    fi
}

# Generate Prometheus metrics
generate_prometheus_metrics() {
    local timestamp
    timestamp=$(date +%s)

    cat > "$PROMETHEUS_METRICS" << EOF
# HELP ai_memory_usage_percent Current memory usage percentage
# TYPE ai_memory_usage_percent gauge
ai_memory_usage_percent $(jq -r '.memory.usage_percent' "$METRICS_FILE" 2>/dev/null || echo 0) $timestamp

# HELP ai_cpu_usage_percent Current CPU usage percentage
# TYPE ai_cpu_usage_percent gauge
ai_cpu_usage_percent $(jq -r '.cpu.usage_percent' "$METRICS_FILE" 2>/dev/null || echo 0) $timestamp

# HELP ai_disk_usage_percent Current disk usage percentage
# TYPE ai_disk_usage_percent gauge
ai_disk_usage_percent $(jq -r '.disk.usage_percent' "$METRICS_FILE" 2>/dev/null || echo 0) $timestamp

# HELP ai_swap_usage_percent Current swap usage percentage
# TYPE ai_swap_usage_percent gauge
ai_swap_usage_percent $(jq -r '.swap.usage_percent' "$METRICS_FILE" 2>/dev/null || echo 0) $timestamp

# HELP ai_ollama_memory_mb Ollama memory usage in MB
# TYPE ai_ollama_memory_mb gauge
ai_ollama_memory_mb $(jq -r '.services.ollama.memory_mb' "$METRICS_FILE" 2>/dev/null || echo 0) $timestamp

# HELP ai_llamacpp_memory_mb llama.cpp memory usage in MB
# TYPE ai_llamacpp_memory_mb gauge
ai_llamacpp_memory_mb $(jq -r '.services.llamacpp.memory_mb' "$METRICS_FILE" 2>/dev/null || echo 0) $timestamp

# HELP ai_proxy_memory_mb Proxy memory usage in MB
# TYPE ai_proxy_memory_mb gauge
ai_proxy_memory_mb $(jq -r '.services["local-llm-proxy"].memory_mb' "$METRICS_FILE" 2>/dev/null || echo 0) $timestamp
EOF
}

# Main monitoring function
collect_metrics() {
    local memory_info swap_info cpu_info disk_info service_info gpu_info

    memory_info=$(get_memory_info)
    swap_info=$(get_swap_info)
    cpu_info=$(get_cpu_info)
    disk_info=$(get_disk_info)
    service_info=$(get_service_info)
    gpu_info=$(get_gpu_info)

    # Combine all metrics into JSON
    jq -n \
        --argjson memory "$memory_info" \
        --argjson swap "$swap_info" \
        --argjson cpu "$cpu_info" \
        --argjson disk "$disk_info" \
        --argjson services "$service_info" \
        --argjson gpu "$gpu_info" \
        '{timestamp: now | strftime("%Y-%m-%dT%H:%M:%SZ")} + $memory + $swap + $cpu + $disk + $services + $gpu' > "$METRICS_FILE"

    # Generate Prometheus metrics
    generate_prometheus_metrics

    log_info "Metrics collected and saved to $METRICS_FILE"
}

# Display current metrics
display_metrics() {
    if [[ -f "$METRICS_FILE" ]]; then
        echo "=== AI System Resource Metrics ==="
        echo "Timestamp: $(jq -r '.timestamp' "$METRICS_FILE")"
        echo ""
        echo "Memory: $(jq -r '.memory.usage_percent' "$METRICS_FILE")% ($(jq -r '.memory.used_gb' "$METRICS_FILE")GB/$(jq -r '.memory.total_gb' "$METRICS_FILE")GB)"
        echo "Swap: $(jq -r '.swap.usage_percent' "$METRICS_FILE")% ($(jq -r '.swap.used_gb' "$METRICS_FILE")GB/$(jq -r '.swap.total_gb' "$METRICS_FILE")GB)"
        echo "CPU: $(jq -r '.cpu.usage_percent' "$METRICS_FILE")%"
        echo "Disk ($(jq -r '.disk.mount_point' "$METRICS_FILE")): $(jq -r '.disk.usage_percent' "$METRICS_FILE")% ($(jq -r '.disk.used_gb' "$METRICS_FILE")GB/$(jq -r '.disk.total_gb' "$METRICS_FILE")GB)"
        echo ""
        echo "Services:"
        jq -r '.services | to_entries[] | "  \(.key): \(.value.memory_mb)MB / \(.value.memory_limit_mb)MB (\(.value.memory_percent)%) CPU: \(.value.cpu_percent)%"' "$METRICS_FILE" 2>/dev/null || echo "  No service data available"
        echo ""
        if [[ "$(jq -r '.gpu.available' "$METRICS_FILE")" == "true" ]]; then
            echo "GPU: $(jq -r '.gpu.gpu_utilization_percent' "$METRICS_FILE")% GPU util, $(jq -r '.gpu.memory_utilization_percent' "$METRICS_FILE")% memory util"
        else
            echo "GPU: Not available"
        fi
    else
        echo "No metrics file found. Run with --collect first."
    fi
}

# Main execution
case "${1:-}" in
    --collect)
        collect_metrics
        ;;
    --display)
        display_metrics
        ;;
    --json)
        if [[ -f "$METRICS_FILE" ]]; then
            cat "$METRICS_FILE"
        else
            echo '{"error": "No metrics file found"}'
        fi
        ;;
    --prometheus)
        if [[ -f "$PROMETHEUS_METRICS" ]]; then
            cat "$PROMETHEUS_METRICS"
        else
            echo "# No metrics available"
        fi
        ;;
    --alerts)
        if [[ -f "$ALERT_LOG" ]]; then
            echo "=== Recent Alerts ==="
            tail -20 "$ALERT_LOG"
        else
            echo "No alerts logged yet."
        fi
        ;;
    *)
        echo "Usage: $0 [--collect|--display|--json|--prometheus|--alerts]"
        echo "  --collect: Collect current metrics"
        echo "  --display: Display current metrics in human-readable format"
        echo "  --json: Output metrics as JSON"
        echo "  --prometheus: Output metrics in Prometheus format"
        echo "  --alerts: Show recent alerts"
        exit 1
        ;;
esac</content>
<parameter name="filePath">/Users/fuaadabdullah/ForgeMonorepo/scripts/ai-resource-monitor.sh
