#!/bin/bash
# Kamatera Quick Health Check - Fast Version
# Purpose: Quick health check without slow model testing

set -e

SERVER1_IP="45.61.51.220"
SERVER2_IP="192.175.23.150"
OLLAMA_PORT="8002"
ROUTER_PORT="8000"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "⚡ Kamatera Quick Health Check"
echo "=================================="

# Basic connectivity
echo "🌐 Basic Connectivity:"
if ping -c 2 -W 2 "$SERVER1_IP" > /dev/null 2>&1; then
    echo -e "  Server 1 ($SERVER1_IP): ${GREEN}OK${NC}"
    server1_ok=true
else
    echo -e "  Server 1 ($SERVER1_IP): ${RED}FAIL${NC}"
    server1_ok=false
fi

if ping -c 2 -W 2 "$SERVER2_IP" > /dev/null 2>&1; then
    echo -e "  Server 2 ($SERVER2_IP): ${GREEN}OK${NC}"
    server2_ok=true
else
    echo -e "  Server 2 ($SERVER2_IP): ${RED}FAIL${NC}"
    server2_ok=false
fi

echo ""
echo "🔧 Service Health:"

# Test Server 1 Router
if $server1_ok; then
    echo -n "  Router API (Server 1): "
    if curl -s --max-time 5 "http://$SERVER1_IP:$ROUTER_PORT/health" > /dev/null 2>&1; then
        echo -e "${GREEN}OK${NC}"
    else
        echo -e "${RED}FAIL${NC}"
    fi
fi

# Test Server 2 Ollama
if $server2_ok; then
    echo -n "  Ollama API (Server 2): "
    if curl -s --max-time 5 "http://$SERVER2_IP:$OLLAMA_PORT/api/tags" > /dev/null 2>&1; then
        echo -e "${GREEN}OK${NC}"
        
        # Get model count
        model_count=$(curl -s --max-time 5 "http://$SERVER2_IP:$OLLAMA_PORT/api/tags" | grep -o '"name"' | wc -l)
        echo -e "    Available models: ${GREEN}$model_count${NC}"
    else
        echo -e "${RED}FAIL${NC}"
    fi
fi

echo ""
echo "📋 Summary:"

if $server1_ok && $server2_ok; then
    echo -e "  ${GREEN}✅ Both servers operational${NC}"
    echo "  📊 Status: Full redundancy available"
    exit 0
elif $server2_ok; then
    echo -e "  ${YELLOW}⚠️  Server 1 down, Server 2 operational${NC}"
    echo "  📊 Status: Limited redundancy (primary only)"
    exit 1
elif $server1_ok; then
    echo -e "  ${YELLOW}⚠️  Server 2 down, Server 1 operational${NC}"
    echo "  📊 Status: Limited redundancy (backup only)"
    exit 2
else
    echo -e "  ${RED}🚨 Both servers down!${NC}"
    echo "  📊 Status: Complete system failure"
    exit 3
fi