#!/bin/bash
# Legacy script replaced to start the canonical FastAPI backend.
cd /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/backend
export PYTHONPATH=/Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/backend
# Use Uvicorn to run the FastAPI app
exec uvicorn main:app --host 0.0.0.0 --port 5000
