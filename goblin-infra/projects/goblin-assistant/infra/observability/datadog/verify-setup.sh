#!/usr/bin/env bash
# Verify Datadog process monitoring setup

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== Datadog Process Monitoring Verification ===${NC}\n"

# Check 1: Agent Running
echo -e "${YELLOW}1. Checking if Datadog Agent is running...${NC}"
if pgrep -x "agent" > /dev/null || pgrep -x "datadog-agent" > /dev/null; then
  echo -e "${GREEN}✓ Datadog Agent is running${NC}"
else
  echo -e "${RED}✗ Datadog Agent is NOT running${NC}"
  exit 1
fi

# Check 2: Process Collection Enabled
echo -e "\n${YELLOW}2. Checking process collection configuration...${NC}"
if sudo datadog-agent status 2>/dev/null | grep -q "process"; then
  echo -e "${GREEN}✓ Process collection is enabled${NC}"
else
  echo -e "${RED}✗ Process collection is NOT enabled${NC}"
fi

# Check 3: System Probe Running
echo -e "\n${YELLOW}3. Checking system-probe status...${NC}"
if pgrep -x "system-probe" > /dev/null; then
  echo -e "${GREEN}✓ System-probe is running (I/O stats available)${NC}"
else
  echo -e "${YELLOW}⚠ System-probe is NOT running (no I/O stats)${NC}"
fi

# Check 4: Agent Version
echo -e "\n${YELLOW}4. Checking agent version...${NC}"
DD_VERSION=$(datadog-agent version 2>/dev/null | grep "Agent" | awk '{print $2}' || echo "unknown")
echo "   Version: $DD_VERSION"

# Check 5: Process Count
echo -e "\n${YELLOW}5. Checking monitored process count...${NC}"
PROCESS_COUNT=$(sudo datadog-agent status 2>/dev/null | grep "Process Count" | awk '{print $3}' || echo "0")
echo "   Monitoring $PROCESS_COUNT processes"

# Check 6: Configuration Files
echo -e "\n${YELLOW}6. Checking configuration files...${NC}"
if [ -f "/etc/datadog-agent/datadog.yaml" ]; then
  echo -e "${GREEN}✓ Main config exists${NC}"
else
  echo -e "${RED}✗ Main config missing${NC}"
fi

if [ -f "/etc/datadog-agent/system-probe.yaml" ]; then
  echo -e "${GREEN}✓ System-probe config exists${NC}"
else
  echo -e "${YELLOW}⚠ System-probe config missing${NC}"
fi

# Check 7: Recent Logs
echo -e "\n${YELLOW}7. Recent log entries...${NC}"
if [ -f "/var/log/datadog/agent.log" ]; then
  echo "   Last 3 process-related log entries:"
  tail -1000 /var/log/datadog/agent.log | grep -i "process" | tail -3 || echo "   No recent process logs"
fi

# Check 8: Datadog UI
echo -e "\n${YELLOW}8. Next Steps:${NC}"
echo "   → View processes: https://app.datadoghq.com/process"
echo "   → Create monitors: https://app.datadoghq.com/monitors/create"
echo "   → Build dashboards: https://app.datadoghq.com/dashboard/lists"

echo -e "\n${GREEN}=== Verification Complete ===${NC}"
