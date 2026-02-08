#!/usr/bin/env python3
"""
This debug script used the legacy Flask-based `api/` app and has been archived.
Use `apps/goblin-assistant/backend/` for the canonical FastAPI backend. If you need a
debug helper for the backend, consider running `uvicorn apps.goblin-assistant.backend.main:app --reload`.

This file is kept as an archive placeholder and should not be used to start the
production or development server.
"""

import sys

print(
    "This debug script is archived. See apps/goblin-assistant/backend for the current backend."
)
sys.exit(0)
