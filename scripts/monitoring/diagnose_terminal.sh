#!/usr/bin/env bash
set -euo pipefail

# Simple diagnose script for integrated terminal issues
# - Lists listening ports
# - Lists vite/node/uvicorn/python processes
# - Optionally kills vite or uvicorn processes

echo "Listening TCP ports:" 
ss -tlnp 2>/dev/null || lsof -PiTCP -sTCP:LISTEN -n -P

echo

echo "Processes: (vite/node/python/uvicorn)"
ps aux | egrep 'vite|npx|node|python|uvicorn|uvicorn' --color=never || true

echo
read -p "Would you like to kill all vite/npX/node processes? (y/N): " reply
if [[ $reply =~ ^[Yy]$ ]]; then
  pkill -f 'vite' || true
  pkill -f 'npx vite' || true
  pkill -f 'npx' || true
  echo "Killed vite/npx processes."
else
  echo "No action taken."
fi

# Print instructions
cat <<'EOF'

If you are unable to type in the VS Code integrated terminal:
  - Open a separate terminal app and run this script: ./scripts/diagnose_terminal.sh
  - If port 1420 or 3001 is occupied, kill the process or alter the port.
  - Restart VS Code and open a fresh terminal (Terminal -> New Terminal).
  - If you have persistent issues, re-open VS Code Developer Tools (Help -> Toggle Developer Tools) and copy any errors from Console.

EOF
