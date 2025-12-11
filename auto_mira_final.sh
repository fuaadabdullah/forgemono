#!/bin/bash
# auto_mira_final.sh
# One-command final step automation

echo "🚀 MIRA LINKER - ULTIMATE AUTOMATION"
echo "===================================="

# Download and run the automation
curl -sSL https://raw.githubusercontent.com/your-org/mira-automation/main/complete_mira_integration.sh | bash

# Alternative: Run step-by-step
echo -e "\n📦 Alternative step-by-step installation:"
cat << 'EOF'

# Option 1: Full automation (recommended)
curl -sSL https://get.mira.tools/install | bash

# Option 2: Manual steps with assistance
wget https://raw.githubusercontent.com/your-org/mira-automation/main/mira_console_automation.py
python3 mira_console_automation.py --interactive

# Option 3: Docker-based installation
docker run -it \
  -e GITHUB_TOKEN=$(gh auth token) \
  -v $(pwd)/mira-linker-config.yml:/config.yml \
  mira/tools-automation:latest

EOF

# Quick verification
echo -e "\n🔍 Quick verification:"
if [ -f "mira-linker-config.yml" ]; then
    echo "✅ Configuration file exists"

    if grep -q "PROJ-" mira-linker-config.yml; then
        echo "✅ JIRA project pattern detected"
    fi

    echo -e "\n🎯 To test immediately:"
    echo "1. Create test PR: gh pr create --title 'TEST: JIRA-123 Integration test' --body 'Testing Mira integration'"
    echo "2. Check status: ./verify_mira_setup.sh"
fi
