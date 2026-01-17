#!/bin/bash
# Kamatera Automated Monitoring & Alerting System
# Purpose: Continuous monitoring with automated alerting

set -e

SERVER1_IP="45.61.51.220"
SERVER2_IP="192.175.23.150"
OLLAMA_PORT="8002"
ROUTER_PORT="8000"
ALERT_EMAIL="admin@example.com"  # Update with actual email
LOG_FILE="kamatera_alerts_$(date +%Y%m%d).log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Alert functions
send_alert() {
    local severity=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo "[$timestamp] [$severity] $message" | tee -a "$LOG_FILE"
    
    # Log to system log
    logger -t "kamatera-monitor" "[$severity] $message"
    
    # Email alert (if configured)
    if command -v mail >/dev/null 2>&1 && [[ "$ALERT_EMAIL" != "admin@example.com" ]]; then
        echo "$message" | mail -s "Kamatera Alert: $severity" "$ALERT_EMAIL" 2>/dev/null || true
    fi
    
    # Discord/Slack webhook (optional)
    if [[ -n "$DISCORD_WEBHOOK" ]]; then
        curl -X POST "$DISCORD_WEBHOOK" \
            -H "Content-Type: application/json" \
            -d "{\"content\": \"$severity: $message\"}" 2>/dev/null || true
    fi
}

check_server() {
    local server_name=$1
    local server_ip=$2
    local service_name=$3
    local endpoint=$4
    
    echo -n "Checking $service_name on $server_name ($server_ip): "
    
    if curl -s --max-time 10 "$endpoint" > /dev/null 2>&1; then
        echo -e "${GREEN}OK${NC}"
        return 0
    else
        echo -e "${RED}FAIL${NC}"
        send_alert "CRITICAL" "$service_name on $server_name ($server_ip) is not responding"
        return 1
    fi
}

test_model_response() {
    local model_name=${1:-"phi3:latest"}
    local test_prompt="System health check test"
    
    echo -n "Testing model response ($model_name): "
    
    response=$(curl -s --max-time 15 -X POST \
        "http://$SERVER2_IP:$OLLAMA_PORT/api/generate" \
        -H "Content-Type: application/json" \
        -d "{\"model\":\"$model_name\",\"prompt\":\"$test_prompt\",\"stream\":false}" 2>/dev/null)
    
    if echo "$response" | grep -q "response"; then
        echo -e "${GREEN}OK${NC}"
        return 0
    else
        echo -e "${RED}FAIL${NC}"
        send_alert "WARNING" "Model $model_name not responding properly on $SERVER2_IP:$OLLAMA_PORT"
        return 1
    fi
}

check_load_balancing() {
    echo "🔄 Testing Load Balancing..."
    
    # Test primary Ollama server
    if check_server "Server 2 (Primary)" "$SERVER2_IP" "Ollama API" "http://$SERVER2_IP:$OLLAMA_PORT/api/tags"; then
        # Count available models
        model_count=$(curl -s --max-time 5 "http://$SERVER2_IP:$OLLAMA_PORT/api/tags" | grep -o '"name"' | wc -l)
        if [[ $model_count -lt 5 ]]; then
            send_alert "WARNING" "Low model count on primary server: $model_count models"
        fi
    fi
    
    # Test backup router
    if check_server "Server 1 (Backup)" "$SERVER1_IP" "Router API" "http://$SERVER1_IP:$ROUTER_PORT/health"; then
        echo "✅ Backup router is healthy"
    fi
}

monitor_performance() {
    echo "📊 Performance Monitoring..."
    
    # Test response times
    echo -n "Primary server response time: "
    start_time=$(date +%s%3N)
    curl -s --max-time 10 "http://$SERVER2_IP:$OLLAMA_PORT/api/tags" > /dev/null
    end_time=$(date +%s%3N)
    response_time=$((end_time - start_time))
    
    if [[ $response_time -lt 1000 ]]; then
        echo -e "${GREEN}${response_time}ms${NC}"
    elif [[ $response_time -lt 3000 ]]; then
        echo -e "${YELLOW}${response_time}ms${NC}"
        send_alert "INFO" "Slow response time on primary server: ${response_time}ms"
    else
        echo -e "${RED}${response_time}ms${NC}"
        send_alert "WARNING" "Very slow response time on primary server: ${response_time}ms"
    fi
}

run_comprehensive_check() {
    local check_type=${1:-"normal"}
    
    echo "=========================================="
    echo "Kamatera Comprehensive Health Check"
    echo "Time: $(date)"
    echo "Check Type: $check_type"
    echo "=========================================="
    
    # Basic connectivity
    echo "🌐 Basic Connectivity:"
    server1_ok=false
    server2_ok=false
    
    if ping -c 3 -W 3 "$SERVER1_IP" > /dev/null 2>&1; then
        echo -e "  Server 1 ($SERVER1_IP): ${GREEN}OK${NC}"
        server1_ok=true
    else
        echo -e "  Server 1 ($SERVER1_IP): ${RED}FAIL${NC}"
        send_alert "CRITICAL" "Server 1 ($SERVER1_IP) is not responding to ping"
    fi
    
    if ping -c 3 -W 3 "$SERVER2_IP" > /dev/null 2>&1; then
        echo -e "  Server 2 ($SERVER2_IP): ${GREEN}OK${NC}"
        server2_ok=true
    else
        echo -e "  Server 2 ($SERVER2_IP): ${RED}FAIL${NC}"
        send_alert "CRITICAL" "Server 2 ($SERVER2_IP) is not responding to ping"
    fi
    
    echo ""
    
    # Service health
    echo "🔧 Service Health:"
    if $server1_ok; then
        check_server "Server 1" "$SERVER1_IP" "Router API" "http://$SERVER1_IP:$ROUTER_PORT/health"
    fi
    
    if $server2_ok; then
        check_server "Server 2" "$SERVER2_IP" "Ollama API" "http://$SERVER2_IP:$OLLAMA_PORT/api/tags"
        test_model_response
    fi
    
    echo ""
    
    # Load balancing test
    if $server1_ok && $server2_ok; then
        check_load_balancing
    fi
    
    echo ""
    
    # Performance monitoring
    if $server2_ok; then
        monitor_performance
    fi
    
    echo ""
    
    # Generate summary
    echo "📋 Summary:"
    if $server1_ok && $server2_ok; then
        echo -e "  ${GREEN}✅ All systems operational${NC}"
        return 0
    elif $server2_ok; then
        echo -e "  ${YELLOW}⚠️  Server 1 down, Server 2 operational${NC}"
        return 1
    elif $server1_ok; then
        echo -e "  ${YELLOW}⚠️  Server 2 down, Server 1 operational${NC}"
        return 2
    else
        echo -e "  ${RED}🚨 Both servers down!${NC}"
        send_alert "CRITICAL" "Both Kamatera servers are down!"
        return 3
    fi
}

# Continuous monitoring
continuous_monitor() {
    local interval=${1:-300}  # Default 5 minutes
    local max_runs=${2:-0}   # 0 = infinite
    
    echo "Starting continuous monitoring (every ${interval}s)"
    echo "Max runs: $max_runs (0 = infinite)"
    echo "Press Ctrl+C to stop"
    
    local run_count=0
    while true; do
        run_count=$((run_count + 1))
        echo ""
        echo "=== Monitor Run #$run_count ==="
        
        run_comprehensive_check "continuous"
        
        # Check if we should stop
        if [[ $max_runs -gt 0 && $run_count -ge $max_runs ]]; then
            echo "Reached maximum run count ($max_runs). Stopping."
            break
        fi
        
        echo "Next check in ${interval} seconds..."
        sleep "$interval"
    done
}

# Setup cron job
setup_cron() {
    echo "Setting up automated monitoring via cron..."
    
    # Add to crontab (every 5 minutes)
    (crontab -l 2>/dev/null; echo "*/5 * * * * $(pwd)/kamatera_monitoring_enhanced.sh") | crontab -
    
    echo "✅ Cron job added: monitoring every 5 minutes"
    echo "To view cron jobs: crontab -l"
    echo "To remove: crontab -e (and remove the line)"
}

# Generate report
generate_report() {
    local report_file="kamatera_health_report_$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "Kamatera Server Health Report"
        echo "Generated: $(date)"
        echo "========================================"
        echo ""
        
        # Run check and capture output
        run_comprehensive_check "report" > /dev/null
        
        echo ""
        echo "Recent Alert History:"
        tail -20 "$LOG_FILE" 2>/dev/null || echo "No recent alerts"
        
        echo ""
        echo "System Resource Usage:"
        echo "CPU: $(top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1)%"
        echo "Memory: $(free | grep Mem | awk '{printf("%.1f%%", $3/$2 * 100.0)}')"
        echo "Disk: $(df -h / | awk 'NR==2{printf "%s", $5}')"
        
    } > "$report_file"
    
    echo "📄 Health report generated: $report_file"
}

# Usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  (no args)    Run single comprehensive check"
    echo "  --monitor    Run continuous monitoring (5min interval)"
    echo "  --monitor=N  Run continuous monitoring with N second interval"
    echo "  --monitor=N,M Run continuous monitoring N second interval, M max runs"
    echo "  --cron       Setup automated cron monitoring"
    echo "  --report     Generate health report"
    echo "  --help       Show this help"
    echo ""
    echo "Environment Variables:"
    echo "  ALERT_EMAIL      Email for critical alerts"
    echo "  DISCORD_WEBHOOK  Discord webhook for alerts"
}

# Parse arguments
case "$1" in
    --monitor)
        if [[ "$2" == *,* ]]; then
            IFS=',' read -ra ADDR <<< "$2"
            interval="${ADDR[0]}"
            max_runs="${ADDR[1]}"
            continuous_monitor "$interval" "$max_runs"
        elif [[ -n "$2" ]]; then
            continuous_monitor "$2" 0
        else
            continuous_monitor 300 0
        fi
        ;;
    --cron)
        setup_cron
        ;;
    --report)
        generate_report
        ;;
    --help)
        usage
        ;;
    *)
        run_comprehensive_check "manual"
        ;;
esac