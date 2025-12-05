#!/usr/bin/env python
import uvicorn
import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

if __name__ == "__main__":
    # For Fly.io, always bind to 0.0.0.0:8001
    # Fly.io sets PORT=8001 in environment, but we need to ensure proper binding
    port = 8001  # Hardcode for Fly.io to ensure correct binding
    host = "0.0.0.0"

    print(f"Starting server on {host}:{port}")
    uvicorn.run("main:app", host=host, port=port, log_level="info", access_log=True)
