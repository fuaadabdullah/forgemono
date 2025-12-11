#!/bin/bash
# NOTE: This script previously started the legacy `api/` app. The canonical backend
# has been consolidated into `apps/goblin-assistant/backend/`.
cd /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/backend
exec uvicorn main:app --host 0.0.0.0 --port 8000
