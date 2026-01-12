#!/bin/bash
# CI/CD Pipeline Monitoring Script
# Provides comprehensive monitoring and alerting for CI/CD pipelines

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../" && pwd)"
LOG_FILE="${REPO_ROOT}/logs/ci-cd-monitor.log"
ALERT_THRESHOLD_MINUTES=30
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    log "ERROR: $1"
    send_alert "🚨 CI/CD Pipeline Error: $1"
    exit 1
}

# Send Slack notification
send_alert() {
    local message="$1"
    if [[ -n "$SLACK_WEBHOOK_URL" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"$message\"}" \
            "$SLACK_WEBHOOK_URL" 2>/dev/null || true
    fi
}

# Check CircleCI status
check_circleci() {
    log "Checking CircleCI pipeline status..."
    
    # Get recent builds
    local builds
    builds=$(curl -s -H "Circle-Token: ${CIRCLECI_TOKEN}" \
        "https://circleci.com/api/v2/me" 2>/dev/null || echo "")
    
    if [[ -z "$builds" ]]; then
        log "WARNING: Could not fetch CircleCI status"
        return 1
    fi
    
    # Check for failed builds in last 24 hours
    local failed_builds
    failed_builds=$(curl -s -H "Circle-Token: ${CIRCLECI_TOKEN}" \
        "https://circleci.com/api/v2/project/gh/fuaadabdullah/forgemono/pipeline" 2>/dev/null | \
        jq -r '.items[] | select(.created_at > "'$(date -d '24 hours ago' -Iseconds)'") | .state' 2>/dev/null | \
        grep -c "failed" || echo "0")
    
    if [[ "$failed_builds" -gt 0 ]]; then
        log "WARNING: Found $failed_builds failed builds in last 24 hours"
        send_alert "⚠️ CircleCI: $failed_builds failed builds in last 24 hours"
    fi
    
    log "CircleCI check completed"
}

# Check GitHub Actions status
check_github_actions() {
    log "Checking GitHub Actions status..."
    
    # Get workflow runs
    local runs
    runs=$(curl -s -H "Authorization: token ${GITHUB_TOKEN}" \
        "https://api.github.com/repos/fuaadabdullah/forgemono/actions/runs" 2>/dev/null || echo "")
    
    if [[ -z "$runs" ]]; then
        log "WARNING: Could not fetch GitHub Actions status"
        return 1
    fi
    
    # Check for failed runs in last 24 hours
    local failed_runs
    failed_runs=$(echo "$runs" | jq -r '.workflow_runs[] | select(.created_at > "'$(date -d '24 hours ago' -Iseconds)'") | .conclusion' 2>/dev/null | \
        grep -c "failure\|cancelled" || echo "0")
    
    if [[ "$failed_runs" -gt 0 ]]; then
        log "WARNING: Found $failed_runs failed GitHub Actions runs in last 24 hours"
        send_alert "⚠️ GitHub Actions: $failed_runs failed runs in last 24 hours"
    fi
    
    log "GitHub Actions check completed"
}

# Check Docker registry status
check_docker_registry() {
    log "Checking Docker registry status..."
    
    # Check if latest image exists and is recent
    local image_age
    image_age=$(curl -s -H "Authorization: Bearer ${DOCKER_HUB_TOKEN}" \
        "https://hub.docker.com/v2/repositories/fuaadabdullah/goblin-assistant/tags/latest" 2>/dev/null | \
        jq -r '.last_updated' 2>/dev/null || echo "")
    
    if [[ -n "$image_age" ]]; then
        local age_hours
        age_hours=$(($(date +%s) - $(date -d "$image_age" +%s)))
        age_hours=$((age_hours / 3600))
        
        if [[ $age_hours -gt 24 ]]; then
            log "WARNING: Docker image is $age_hours hours old"
            send_alert "⚠️ Docker: Image is $age_hours hours old"
        fi
    fi
    
    log "Docker registry check completed"
}

# Check Terraform Cloud status
check_terraform_cloud() {
    log "Checking Terraform Cloud status..."
    
    # Check workspace status
    local workspaces=("GoblinOSAssistant" "GoblinOSAssistant-staging" "GoblinOSAssistant-prod")
    
    for workspace in "${workspaces[@]}"; do
        local status
        status=$(curl -s -H "Authorization: Bearer ${TF_TOKEN}" \
            "https://app.terraform.io/api/v2/organizations/fuaadabdullah/workspaces/$workspace" 2>/dev/null | \
            jq -r '.data.attributes["latest-run-status"]' 2>/dev/null || echo "unknown")
        
        if [[ "$status" == "errored" ]]; then
            log "WARNING: Terraform workspace $workspace has errors"
            send_alert "⚠️ Terraform: Workspace $workspace has errors"
        fi
    done
    
    log "Terraform Cloud check completed"
}

# Check deployment health
check_deployment_health() {
    log "Checking deployment health..."
    
    # Check main application endpoints
    local endpoints=(
        "https://goblin.fuaad.ai/health"
        "https://goblin-assistant-git-develop.vercel.app/health"
        "https://api.goblin.fuaad.ai/health"
    )
    
    for endpoint in "${endpoints[@]}"; do
        local response
        response=$(curl -s -o /dev/null -w "%{http_code}" "$endpoint" 2>/dev/null || echo "000")
        
        if [[ "$response" != "200" ]]; then
            log "WARNING: Endpoint $endpoint returned status $response"
            send_alert "⚠️ Health Check: $endpoint returned status $response"
        fi
    done
    
    log "Deployment health check completed"
}

# Generate performance metrics
generate_metrics() {
    log "Generating CI/CD performance metrics..."
    
    # Calculate average build time
    local avg_build_time
    avg_build_time=$(curl -s -H "Circle-Token: ${CIRCLECI_TOKEN}" \
        "https://circleci.com/api/v2/project/gh/fuaadabdullah/forgemono/pipeline" 2>/dev/null | \
        jq -r '.items[] | .created_at' 2>/dev/null | head -10 | \
        while read -r date; do
            echo $(date -d "$date" +%s)
        done | \
        awk 'BEGIN{sum=0; count=0} {sum+=$1; count++} END{if(count>0) print sum/count}')
    
    if [[ -n "$avg_build_time" ]]; then
        local current_time
        current_time=$(date +%s)
        local avg_duration
        avg_duration=$((current_time - avg_build_time))
        avg_duration=$((avg_duration / 60))
        
        log "Average build time: ${avg_duration} minutes"
    fi
    
    log "Metrics generation completed"
}

# Main execution
main() {
    log "Starting CI/CD pipeline monitoring..."
    
    # Create log directory if it doesn't exist
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # Run checks
    check_circleci
    check_github_actions
    check_docker_registry
    check_terraform_cloud
    check_deployment_health
    generate_metrics
    
    log "CI/CD pipeline monitoring completed successfully"
    
    # Send summary notification
    send_alert "✅ CI/CD Pipeline monitoring completed successfully"
}

# Run main function
main "$@"
