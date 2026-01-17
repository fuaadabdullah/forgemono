#!/usr/bin/env bash
# Production Monitoring Setup Script
# Configures Redis, Datadog, and Sentry for production monitoring
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}📊 Production Monitoring Setup${NC}"

# Check for required tools
check_dependencies() {
    local missing_tools=()

    if ! command -v redis-cli >/dev/null 2>&1; then
        missing_tools+=("redis-cli")
    fi

    if ! command -v curl >/dev/null 2>&1; then
        missing_tools+=("curl")
    fi

    if [ ${#missing_tools[@]} -ne 0 ]; then
        echo -e "${YELLOW}⚠️  Missing tools (optional for basic setup):${NC}"
        printf '  - %s\n' "${missing_tools[@]}"
    fi
}

# Validate Redis connection
setup_redis() {
    echo "🔴 Setting up Redis monitoring..."

    if [ -n "${REDIS_URL:-}" ]; then
        # Extract Redis connection details
        local redis_host=$(echo "$REDIS_URL" | sed -E 's|redis://([^:]*):([^@]*)@([^:]*):([^/]*)/.*|\3|')
        local redis_port=$(echo "$REDIS_URL" | sed -E 's|redis://([^:]*):([^@]*)@([^:]*):([^/]*)/.*|\4|')
        local redis_password=$(echo "$REDIS_URL" | sed -E 's|redis://([^:]*):([^@]*)@([^:]*):([^/]*)/.*|\2|')

        echo "Testing Redis connection to $redis_host:$redis_port..."

        if command -v redis-cli >/dev/null 2>&1; then
            if REDISCLI_AUTH="$redis_password" timeout 5 redis-cli -h "$redis_host" -p "$redis_port" ping >/dev/null 2>&1; then
                echo -e "${GREEN}✅ Redis connection successful${NC}"

                # Get basic Redis info
                local redis_info=$(REDISCLI_AUTH="$redis_password" redis-cli -h "$redis_host" -p "$redis_port" info server 2>/dev/null | head -10)
                echo "Redis server info:"
                echo "$redis_info" | head -5
            else
                echo -e "${RED}❌ Redis connection failed${NC}"
                echo -e "${YELLOW}💡 Check REDIS_URL and network connectivity${NC}"
            fi
        else
            echo -e "${YELLOW}⚠️  redis-cli not available, skipping connection test${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  REDIS_URL not set, skipping Redis setup${NC}"
    fi
}

# Validate Datadog configuration
setup_datadog() {
    echo "🐕 Setting up Datadog monitoring..."

    if [ -n "${DD_API_KEY:-}" ]; then
        echo "Validating Datadog API key..."

        # Test Datadog API (basic validation)
        local response=$(curl -s -o /dev/null -w "%{http_code}" \
            -H "DD-API-KEY: $DD_API_KEY" \
            -H "Content-Type: application/json" \
            -X POST "https://api.datadoghq.com/api/v1/validate" \
            -d '{}' 2>/dev/null || echo "000")

        if [ "$response" = "200" ]; then
            echo -e "${GREEN}✅ Datadog API key valid${NC}"
        else
            echo -e "${RED}❌ Datadog API key validation failed (HTTP $response)${NC}"
            echo -e "${YELLOW}💡 Check DD_API_KEY in your environment${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  DD_API_KEY not set, skipping Datadog validation${NC}"
    fi

    if [ -n "${DD_SITE:-}" ]; then
        echo "Datadog site: $DD_SITE"
    fi
}

# Validate Sentry configuration
setup_sentry() {
    echo "🦅 Setting up Sentry error monitoring..."

    if [ -n "${SENTRY_DSN:-}" ]; then
        echo "Validating Sentry DSN..."

        # Extract Sentry project info from DSN
        local sentry_host=$(echo "$SENTRY_DSN" | sed -E 's|https://[^@]*@([^/]*)/.*|\1|')
        local sentry_project=$(echo "$SENTRY_DSN" | sed -E 's|https://[^@]*@[^/]*/([^/]*).*|\1|')

        if [ -n "$sentry_host" ] && [ -n "$sentry_project" ]; then
            echo -e "${GREEN}✅ Sentry DSN format valid${NC}"
            echo "Sentry host: $sentry_host"
            echo "Project ID: $sentry_project"
        else
            echo -e "${RED}❌ Invalid Sentry DSN format${NC}"
        fi

        # Test Sentry endpoint (basic connectivity)
        local test_response=$(curl -s -o /dev/null -w "%{http_code}" \
            --max-time 5 \
            "$sentry_host/api/$sentry_project/envelope/" \
            -H "Content-Type: application/x-sentry-envelope" \
            -d "test" 2>/dev/null || echo "000")

        if [ "$test_response" = "200" ] || [ "$test_response" = "400" ]; then
            echo -e "${GREEN}✅ Sentry endpoint reachable${NC}"
        else
            echo -e "${YELLOW}⚠️  Sentry endpoint test inconclusive (HTTP $test_response)${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  SENTRY_DSN not set, skipping Sentry validation${NC}"
    fi
}

# Generate monitoring configuration summary
generate_config_summary() {
    echo ""
    echo -e "${BLUE}📋 Monitoring Configuration Summary${NC}"
    echo "========================================"

    echo "Redis:"
    if [ -n "${REDIS_URL:-}" ]; then
        echo "  ✅ Configured"
    else
        echo "  ❌ Not configured"
    fi

    echo "Datadog:"
    if [ -n "${DD_API_KEY:-}" ]; then
        echo "  ✅ API Key configured"
    else
        echo "  ❌ API Key missing"
    fi

    if [ -n "${DD_SITE:-}" ]; then
        echo "  ✅ Site: $DD_SITE"
    else
        echo "  ⚠️  Site not specified (using default)"
    fi

    echo "Sentry:"
    if [ -n "${SENTRY_DSN:-}" ]; then
        echo "  ✅ DSN configured"
    else
        echo "  ❌ DSN missing"
    fi

    echo ""
    echo -e "${GREEN}🎯 Next Steps:${NC}"
    echo "1. Ensure Datadog agent is running in production"
    echo "2. Configure Datadog dashboards and monitors"
    echo "3. Set up Sentry alerts and releases"
    echo "4. Monitor Redis memory usage and connection pools"
}

# Main execution
main() {
    check_dependencies
    setup_redis
    setup_datadog
    setup_sentry
    generate_config_summary

    echo ""
    echo -e "${GREEN}🎉 Monitoring setup validation complete!${NC}"
}

main "$@"
