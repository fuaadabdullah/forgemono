#!/usr/bin/env python
import uvicorn
import sys
import os
from pathlib import Path

# Add the parent directory (apps/goblin-assistant) to Python path so 'backend' is a package
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

if __name__ == "__main__":
    # For Fly.io, always bind to 0.0.0.0:8001
    # Fly.io sets PORT=8001 in environment, but we need to ensure proper binding
    port = int(os.getenv("PORT", "8001"))
    host = "0.0.0.0"

    print(f"Starting server on {host}:{port}")
    # Run the app as a module to support relative imports
    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        log_level="info",
        access_log=True,
        reload=False,
    )
