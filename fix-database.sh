#!/bin/bash
# Goblin Assistant Database Connection Fix Wrapper
# Run this from the project root to fix database connection issues

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/apps/goblin-assistant/backend"

echo "🔧 Goblin Assistant Database Connection Fix"
echo "============================================"
echo

# Check if we're in the right directory
if [ ! -d "apps/goblin-assistant" ]; then
    echo "❌ Error: Please run this script from the ForgeMonorepo root directory"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is required but not found"
    exit 1
fi

# Run the Python script
cd "$BACKEND_DIR"
python3 fix_database_connection.py

echo
echo "🎉 Database connection fix completed!"
echo "You can now start the backend with:"
echo "  cd apps/goblin-assistant/backend"
echo "  python -m uvicorn main:app --reload --host 0.0.0.0 --port 8001"
