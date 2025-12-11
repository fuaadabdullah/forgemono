#!/bin/bash
cd /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/api
exec uvicorn main:app --host 0.0.0.0 --port 8000
