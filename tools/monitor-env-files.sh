#!/bin/bash
# ForgeMonorepo - .env File Monitor
# Monitors for unauthorized .env files that shouldn't exist
# Run this in CI/CD pipelines or as a pre-commit hook

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Find all .env files
find_env_files() {
    find "$PROJECT_ROOT" -name "*.env*" -type f 2>/dev/null | grep -v node_modules | grep -v __pycache__
}

# Check if a file contains real secrets
contains_real_secrets() {
    local file="$1"

    # Skip example/template files
    if [[ "$file" == *".env.example" ]] || [[ "$file" == *".env.template" ]]; then
        return 1
    fi

    # Check for patterns that indicate real secrets
    if grep -qE "(sk-|AIza|SECRET|TOKEN|PASSWORD|API_KEY)" "$file" 2>/dev/null; then
        # Additional check: exclude placeholder values
        if ! grep -qE "(REDACTED|your-|example-|placeholder-|CHANGE_ME)" "$file" 2>/dev/null; then
            return 0  # Contains real secrets
        fi
    fi

    return 1  # No real secrets
}

# Check if file is in allowed locations
is_allowed_location() {
    local file="$1"

    # Allow .env files in these specific locations for development
    local allowed_paths=(
        "/tools/"
        "/scripts/"
        "/.env.example"
        "/.env.template"
    )

    for allowed in "${allowed_paths[@]}"; do
        if [[ "$file" == *"$allowed"* ]]; then
            return 0
        fi
    done

    return 1
}

# Main monitoring function
monitor_env_files() {
    log_info "🔍 Monitoring for unauthorized .env files..."

    local env_files
    env_files=$(find_env_files)

    local violations=()
    local warnings=()

    while IFS= read -r file; do
        [ -z "$file" ] && continue

        if contains_real_secrets "$file"; then
            if is_allowed_location "$file"; then
                warnings+=("$file (allowed location but contains secrets)")
            else
                violations+=("$file")
            fi
        fi
    done <<< "$env_files"

    # Report findings
    if [ ${#violations[@]} -gt 0 ]; then
        log_error "🚨 SECURITY VIOLATION: Found .env files with real secrets!"
        printf '  %s\n' "${violations[@]}"
        echo ""
        log_error "These files must be removed immediately!"
        log_info "Move secrets to Bitwarden using: ./tools/secrets.sh set <name> <value>"
        return 1
    fi

    if [ ${#warnings[@]} -gt 0 ]; then
        log_warning "⚠️  WARNING: Found .env files with secrets in allowed locations:"
        printf '  %s\n' "${warnings[@]}"
        echo ""
        log_info "Consider moving these to Bitwarden as well"
    fi

    if [ ${#violations[@]} -eq 0 ] && [ ${#warnings[@]} -eq 0 ]; then
        log_success "✅ No unauthorized .env files found"
    fi
}

# Generate report
generate_report() {
    local report_file="$PROJECT_ROOT/.env-monitor-report.json"

    log_info "Generating .env monitoring report..."

    local env_files
    env_files=$(find_env_files)

    local report_data="{\"timestamp\":\"$(date -Iseconds)\",\"files\":["

    local first=true
    while IFS= read -r file; do
        [ -z "$file" ] && continue

        if [ "$first" = true ]; then
            first=false
        else
            report_data+=","
        fi

        local has_secrets="false"
        local is_allowed="false"

        if contains_real_secrets "$file"; then
            has_secrets="true"
        fi

        if is_allowed_location "$file"; then
            is_allowed="true"
        fi

        report_data+="{\"path\":\"$file\",\"has_secrets\":$has_secrets,\"is_allowed\":$is_allowed}"
    done <<< "$env_files"

    report_data+="]}"

    echo "$report_data" > "$report_file"
    log_success "Report saved to $report_file"
}

# Main function
main() {
    local command="${1:-monitor}"

    case "$command" in
        "monitor")
            monitor_env_files
            ;;
        "report")
            generate_report
            ;;
        "help"|*)
            echo "ForgeMonorepo .env File Monitor"
            echo ""
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  monitor    Check for unauthorized .env files (default)"
            echo "  report     Generate JSON report of all .env files"
            echo "  help       Show this help"
            ;;
    esac
}

main "$@"
