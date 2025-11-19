#!/bin/bash
# Start Forge Lite FastAPI Backend
# This script starts the FastAPI server in the background using nohup

cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found. Please run 'pip3 install -r requirements.txt' first."
    exit 1
fi

# Set Python path for ingestion packages
export PYTHONPATH=/Users/fuaadabdullah/ForgeMonorepo/GoblinOS/packages/ingestion-market-data-python/src:$PYTHONPATH

# Start the server
echo "Starting Forge Lite FastAPI backend on http://localhost:8000..."
nohup ./venv/bin/python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --log-level info > server.log 2>&1 &

# Wait a moment for startup
sleep 2

# Test the server
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Server started successfully!"
    echo "📝 Logs: server.log"
    echo "🛑 To stop: pkill -f uvicorn"
else
    echo "❌ Server failed to start. Check server.log for details."
fi
