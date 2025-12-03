#!/usr/bin/env bash
# Setup script for Datadog Process Monitoring on Goblin Assistant Backend
# This script configures Datadog Agent to collect process metrics with I/O stats

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DATADOG_AGENT_CONFIG_DIR="${DATADOG_AGENT_CONFIG_DIR:-/etc/datadog-agent}"
SYSTEM_PROBE_CONFIG="${DATADOG_AGENT_CONFIG_DIR}/system-probe.yaml"
AGENT_CONFIG="${DATADOG_AGENT_CONFIG_DIR}/datadog.yaml"

echo -e "${GREEN}=== Datadog Process Monitoring Setup ===${NC}"

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}ERROR: This script must be run as root or with sudo${NC}"
  echo "Usage: sudo $0"
  exit 1
fi

# Check if Datadog Agent is installed
if ! command -v datadog-agent &> /dev/null; then
  echo -e "${RED}ERROR: Datadog Agent is not installed${NC}"
  echo "Please install Datadog Agent first:"
  echo "  DD_API_KEY=<YOUR_KEY> DD_SITE=\"datadoghq.com\" bash -c \"\$(curl -L https://s3.amazonaws.com/dd-agent/scripts/install_script_agent7.sh)\""
  exit 1
fi

# Get Datadog Agent version
DD_VERSION=$(datadog-agent version | grep "Agent" | awk '{print $2}' | cut -d'.' -f1,2)
echo -e "${GREEN}Detected Datadog Agent version: ${DD_VERSION}${NC}"

# Check if version supports optimized process collection (v7.53.0+)
MAJOR=$(echo "$DD_VERSION" | cut -d'.' -f1)
MINOR=$(echo "$DD_VERSION" | cut -d'.' -f2)
SUPPORTS_OPTIMIZED=false
if [ "$MAJOR" -ge 7 ] && [ "$MINOR" -ge 53 ]; then
  SUPPORTS_OPTIMIZED=true
fi

# Step 1: Copy system-probe example config if not exists
echo -e "\n${YELLOW}Step 1: Setting up system-probe configuration${NC}"
if [ ! -f "$SYSTEM_PROBE_CONFIG" ]; then
  if [ -f "${SYSTEM_PROBE_CONFIG}.example" ]; then
    echo "Creating system-probe.yaml from example..."
    sudo -u dd-agent install -m 0640 "${SYSTEM_PROBE_CONFIG}.example" "$SYSTEM_PROBE_CONFIG"
    echo -e "${GREEN}✓ Created ${SYSTEM_PROBE_CONFIG}${NC}"
  else
    echo -e "${YELLOW}⚠ Example config not found, creating from template...${NC}"
    cat > "$SYSTEM_PROBE_CONFIG" <<'EOF'
system_probe_config:
  enabled: true
  process_config:
    enabled: true
  log_file: /var/log/datadog/system-probe.log
  log_level: info
EOF
    chown dd-agent:dd-agent "$SYSTEM_PROBE_CONFIG"
    chmod 0640 "$SYSTEM_PROBE_CONFIG"
    echo -e "${GREEN}✓ Created ${SYSTEM_PROBE_CONFIG} from template${NC}"
  fi
else
  echo -e "${GREEN}✓ ${SYSTEM_PROBE_CONFIG} already exists${NC}"
fi

# Step 2: Enable process module in system-probe
echo -e "\n${YELLOW}Step 2: Enabling process module in system-probe${NC}"
if grep -q "process_config:" "$SYSTEM_PROBE_CONFIG"; then
  # Update existing entry
  sed -i.bak 's/enabled: false/enabled: true/g' "$SYSTEM_PROBE_CONFIG"
  echo -e "${GREEN}✓ Enabled process module${NC}"
else
  # Add process config
  cat >> "$SYSTEM_PROBE_CONFIG" <<'EOF'
system_probe_config:
  process_config:
    enabled: true
EOF
  echo -e "${GREEN}✓ Added process module configuration${NC}"
fi

# Step 3: Enable process collection in main agent config
echo -e "\n${YELLOW}Step 3: Enabling process collection in agent${NC}"
if [ -f "$AGENT_CONFIG" ]; then
  # Check if process_config already exists
  if grep -q "process_config:" "$AGENT_CONFIG"; then
    echo "Updating existing process_config..."
    # Enable process collection
    sed -i.bak '/process_config:/,/enabled:/ s/enabled: false/enabled: true/' "$AGENT_CONFIG"

    # Enable optimized collection if supported
    if $SUPPORTS_OPTIMIZED; then
      if grep -q "run_in_core_agent:" "$AGENT_CONFIG"; then
        sed -i.bak '/run_in_core_agent:/ s/false/true/' "$AGENT_CONFIG"
      else
        # Add run_in_core_agent under process_config
        sed -i.bak '/process_config:/a\  run_in_core_agent: true' "$AGENT_CONFIG"
      fi
      echo -e "${GREEN}✓ Enabled optimized process collection (run_in_core_agent)${NC}"
    fi
  else
    # Add process_config section
    echo "Adding process_config to agent configuration..."
    if $SUPPORTS_OPTIMIZED; then
      cat >> "$AGENT_CONFIG" <<'EOF'

# Process collection configuration
process_config:
  enabled: true
  run_in_core_agent: true
  scrub_args: true
  custom_sensitive_words: ['api_key', 'token', 'password', 'secret']
EOF
    else
      cat >> "$AGENT_CONFIG" <<'EOF'

# Process collection configuration
process_config:
  enabled: true
  scrub_args: true
  custom_sensitive_words: ['api_key', 'token', 'password', 'secret']
EOF
    fi
    echo -e "${GREEN}✓ Added process_config to agent${NC}"
  fi
else
  echo -e "${YELLOW}⚠ Main agent config not found at ${AGENT_CONFIG}${NC}"
  echo "Please ensure Datadog Agent is properly installed"
fi

# Step 4: Set proper permissions
echo -e "\n${YELLOW}Step 4: Setting permissions${NC}"
chown dd-agent:dd-agent "$SYSTEM_PROBE_CONFIG" 2>/dev/null || true
chmod 0640 "$SYSTEM_PROBE_CONFIG"
echo -e "${GREEN}✓ Set proper permissions on system-probe.yaml${NC}"

# Step 5: Restart Datadog Agent
echo -e "\n${YELLOW}Step 5: Restarting Datadog Agent${NC}"
if command -v systemctl &> /dev/null; then
  systemctl restart datadog-agent
  echo -e "${GREEN}✓ Restarted Datadog Agent via systemctl${NC}"
elif command -v service &> /dev/null; then
  service datadog-agent restart
  echo -e "${GREEN}✓ Restarted Datadog Agent via service${NC}"
else
  echo -e "${RED}ERROR: Could not restart agent - no systemctl or service command found${NC}"
  exit 1
fi

# Step 6: Verify setup
echo -e "\n${YELLOW}Step 6: Verifying setup${NC}"
sleep 5  # Give agent time to start

# Check if process-agent is running (or not running if optimized)
if $SUPPORTS_OPTIMIZED; then
  # In optimized mode, process-agent should NOT run separately
  if pgrep -x "process-agent" > /dev/null; then
    echo -e "${YELLOW}⚠ process-agent is running separately (expected to run in core agent)${NC}"
    echo "Check /var/log/datadog/process-agent.log for details"
  else
    echo -e "${GREEN}✓ Process collection running in core agent (optimized mode)${NC}"
  fi

  # Check core agent logs
  if tail -20 /var/log/datadog/agent.log | grep -q "Starting process-agent"; then
    echo -e "${GREEN}✓ Process-agent started in core agent${NC}"
  else
    echo -e "${YELLOW}⚠ Could not verify process-agent in core agent logs${NC}"
  fi
else
  # In non-optimized mode, process-agent should run separately
  if pgrep -x "process-agent" > /dev/null; then
    echo -e "${GREEN}✓ process-agent is running${NC}"
  else
    echo -e "${RED}✗ process-agent is NOT running${NC}"
    echo "Check /var/log/datadog/process-agent.log for errors"
  fi
fi

# Check system-probe
if pgrep -x "system-probe" > /dev/null; then
  echo -e "${GREEN}✓ system-probe is running${NC}"
else
  echo -e "${YELLOW}⚠ system-probe is not running${NC}"
  echo "This is required for I/O stats. Check /var/log/datadog/system-probe.log"
fi

# Display summary
echo -e "\n${GREEN}=== Setup Complete ===${NC}"
echo ""
echo "Process monitoring is now enabled with:"
echo "  • Process discovery and metrics collection"
echo "  • I/O and open files stats (via system-probe)"
echo "  • Sensitive argument scrubbing"
if $SUPPORTS_OPTIMIZED; then
  echo "  • Optimized collection (running in core agent)"
fi
echo ""
echo "View your processes in Datadog:"
echo "  → https://app.datadoghq.com/process"
echo ""
echo "Log files:"
echo "  • Agent: /var/log/datadog/agent.log"
echo "  • Process Agent: /var/log/datadog/process-agent.log"
echo "  • System Probe: /var/log/datadog/system-probe.log"
echo ""
echo "To verify:"
echo "  • Check agent status: sudo datadog-agent status"
echo "  • View process metrics: datadog-agent status | grep -A 20 'Process Agent'"
