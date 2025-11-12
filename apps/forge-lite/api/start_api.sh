#!/bin/bash
# Start FastAPI server for Forge Lite

cd /Users/fuaadabdullah/ForgeMonorepo/apps/forge-lite/api

# Set Python path
export PYTHONPATH=/Users/fuaadabdullah/ForgeMonorepo/apps/forge-lite/api:$PYTHONPATH

# Start server
/Users/fuaadabdullah/ForgeMonorepo/apps/forge-lite/api/venv/bin/python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --log-level info --reload
