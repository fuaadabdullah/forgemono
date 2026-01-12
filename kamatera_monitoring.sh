#!/bin/bash
# Kamatera Server Health Monitoring Script
# Created: 2025-01-06
# Purpose: Monitor both Kamatera servers and services

SERVER1_IP="45.61.51.220"
SERVER2_IP="192.175.23.150"
OLLAMA_PORT="8002"
LLAMACPP_PORT="8003"
ROUTER_PORT="8000"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Log file
LOG_FILE="kamatera_health_$(date +%Y%m%d_%H%M%S).log"

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

test_ping() {
    local ip=$1
    local name=$2
    if ping -c 3 -W 3 "$ip" > /dev/null 2>&1; then
        echo -e "${GREEN}✅${NC} $name ($ip) - Ping OK"
        return 0
    else
        echo -e "${RED}❌${NC} $name ($ip) - Ping FAILED"
        return 1
    fi
}

test_http() {
    local ip=$1
    local port=$2
    local path=$3
    local name=$4
    local timeout=10
    
    if curl -s --max-time "$timeout" "http://$ip:$port$path" > /dev/null 2>&1; then
        echo -e "${GREEN}✅${NC} $name ($ip:$port$path) - HTTP OK"
        return 0
    else
        echo -e "${RED}❌${NC} $name ($ip:$port$path) - HTTP FAILED"
        return 1
    fi
}

get_models() {
    local ip=$1
    local port=$2
    local timeout=5
    local response=$(curl -s --max-time "$timeout" "http://$ip:$port/api/tags" 2>/dev/null)
    if [ $? -eq 0 ]; then
        local count=$(echo "$response" | grep -o '"name"' | wc -l)
        echo "$count"
    else
        echo "0"
    fi
}

# Main monitoring function
run_health_check() {
    echo "=============================================="
    echo "Kamatera Server Health Check"
    echo "Time: $(date)"
    echo "=============================================="
    echo ""
    
    log_message "Starting health check for Kamatera servers"
    
    # Test Server 1 (Data/Compute Server)
    echo "🖥️  Testing Server 1 (Data/Compute - $SERVER1_IP):"
    server1_ok=false
    if test_ping "$SERVER1_IP" "Server 1"; then
        server1_ok=true
        test_http "$SERVER1_IP" "$ROUTER_PORT" "/health" "Router API" || server1_ok=false
    fi
    echo ""
    
    # Test Server 2 (LLM Inference Server)
    echo "🤖 Testing Server 2 (LLM Inference - $SERVER2_IP):"
    server2_ok=false
    if test_ping "$SERVER2_IP" "Server 2"; then
        server2_ok=true
        
        # Test Ollama service
        if test_http "$SERVER2_IP" "$OLLAMA_PORT" "/api/tags" "Ollama API"; then
            local model_count=$(get_models "$SERVER2_IP" "$OLLAMA_PORT")
            echo -e "   Models available: ${GREEN}$model_count${NC}"
            log_message "Server 2 Ollama: $model_count models available"
        fi
        
        # Test llama.cpp services
        echo -n "   llama.cpp (port $LLAMACPP_PORT): "
        if test_http "$SERVER2_IP" "$LLAMACPP_PORT" "/health" "llama.cpp API" 2>/dev/null; then
            echo -e "${GREEN}✅${NC} llama.cpp API OK"
        else
            echo -e "${RED}❌${NC} llama.cpp API FAILED"
            log_message "Server 2 llama.cpp service is not responding"
        fi
        
        echo -n "   llama.cpp (port $ROUTER_PORT): "
        if test_http "$SERVER2_IP" "$ROUTER_PORT" "/health" "llama.cpp Router" 2>/dev/null; then
            echo -e "${GREEN}✅${NC} llama.cpp Router OK"
        else
            echo -e "${RED}❌${NC} llama.cpp Router FAILED"
        fi
    fi
    echo ""
    
    # Summary
    echo "📊 Summary:"
    if $server1_ok && $server2_ok; then
        echo -e "${GREEN}🎉 Both servers are healthy!${NC}"
        log_message "Health check: Both servers operational"
        exit 0
    elif $server2_ok; then
        echo -e "${YELLOW}⚠️  Server 1 is down, but Server 2 is operational${NC}"
        log_message "Health check: Server 1 down, Server 2 operational"
        exit 1
    elif $server1_ok; then
        echo -e "${YELLOW}⚠️  Server 2 is down, but Server 1 is operational${NC}"
        log_message "Health check: Server 2 down, Server 1 operational"
        exit 2
    else
        echo -e "${RED}🚨 Both servers are down!${NC}"
        log_message "Health check: Both servers down!"
        exit 3
    fi
}

# Continuous monitoring mode
continuous_monitor() {
    local interval=${1:-60}  # Default 60 seconds
    echo "Starting continuous monitoring (every ${interval}s)"
    echo "Press Ctrl+C to stop"
    
    while true; do
        clear
        run_health_check
        echo ""
        echo "Next check in ${interval} seconds..."
        sleep "$interval"
    done
}

# Usage information
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  (no args)    Run single health check"
    echo "  --monitor    Run continuous monitoring (60s interval)"
    echo "  --monitor=N  Run continuous monitoring with N second interval"
    echo "  --help       Show this help message"
    echo ""
    echo "Log file: $LOG_FILE"
}

# Parse command line arguments
case "$1" in
    --monitor)
        continuous_monitor
        ;;
    --monitor=*)
        interval="${1#*=}"
        continuous_monitor "$interval"
        ;;
    --help)
        usage
        ;;
    *)
        run_health_check
        ;;
esac