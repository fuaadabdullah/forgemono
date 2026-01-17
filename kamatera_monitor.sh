#!/bin/bash
# Kamatera Infrastructure Monitoring Script
# Run this script to check the health of both servers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Load credentials
source "$(dirname "$0")/kamatera_credentials.env"

INFERENCE_IP="${KAMATERA_INFERENCE_SERVER:-192.175.23.150}"
ROUTER_IP="${KAMATERA_ROUTER_SERVER:-45.61.51.220}"
PASSWORD="${KAMATERA_PASSWORD}"

echo "========================================"
echo "  Kamatera Infrastructure Monitor"
echo "========================================"
echo ""

overall_status=0

# Function to check service
check_service() {
    local server=$1
    local port=$2
    local name=$3

    if curl -s --connect-timeout 5 "http://${server}:${port}/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} ${name} on ${server}:${port} - HEALTHY"
        return 0
    else
        echo -e "${RED}✗${NC} ${name} on ${server}:${port} - UNHEALTHY"
        return 1
    fi
}

# Function to check via SSH
check_ssh_service() {
    local server=$1
    local service=$2
    local name=$3

    if sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 "root@$server" "systemctl is-active $service" 2>/dev/null | grep -q "active"; then
        echo -e "${GREEN}✓${NC} ${name} on ${server} - ACTIVE"
        return 0
    else
        echo -e "${RED}✗${NC} ${name} on ${server} - INACTIVE"
        return 1
    fi
}

echo "=== Router Server (${ROUTER_IP}) ==="
check_ssh_service "$ROUTER_IP" "goblin-router" "goblin-router"
overall_status=$((overall_status + $?))

sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no "root@$ROUTER_IP" "redis-cli ping" 2>/dev/null | grep -q "PONG"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Redis on ${ROUTER_IP} - PONG"
else
    echo -e "${RED}✗${NC} Redis on ${ROUTER_IP} - NOT RESPONDING"
    overall_status=$((overall_status + 1))
fi

echo ""
echo "=== Inference Server (${INFERENCE_IP}) ==="
check_ssh_service "$INFERENCE_IP" "ollama" "Ollama"
overall_status=$((overall_status + $?))

check_ssh_service "$INFERENCE_IP" "local-llm-proxy" "local-llm-proxy"
overall_status=$((overall_status + $?))

# Check available models
model_count=$(sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no "root@$INFERENCE_IP" "curl -s http://localhost:8002/api/tags" 2>/dev/null | jq -r '.models | length' 2>/dev/null || echo "0")
if [ "$model_count" -gt 0 ]; then
    echo -e "${GREEN}✓${NC} Models loaded: ${model_count}"
else
    echo -e "${RED}✗${NC} No models detected"
    overall_status=$((overall_status + 1))
fi

echo ""
echo "=== Connectivity Tests ==="
# Test router to inference connectivity
if sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no "root@$ROUTER_IP" "curl -s --connect-timeout 5 http://${INFERENCE_IP}:8003/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Router -> Inference (8003) - REACHABLE"
else
    echo -e "${RED}✗${NC} Router -> Inference (8003) - UNREACHABLE"
    overall_status=$((overall_status + 1))
fi

echo ""
echo "========================================"
if [ $overall_status -eq 0 ]; then
    echo -e "${GREEN}Overall Status: HEALTHY${NC}"
    exit 0
else
    echo -e "${RED}Overall Status: ISSUES DETECTED ($overall_status checks failed)${NC}"
    exit 1
fi
