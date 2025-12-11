#!/bin/bash
cd /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/api
export PYTHONPATH=/Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/api
/Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/api/venv/bin/python3 -c "from app import app; app.run(host='0.0.0.0', port=5000, debug=True)"
