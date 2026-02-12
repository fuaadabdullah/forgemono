#!/usr/bin/env python3
"""
Launcher script for Goblin Assistant backend.

This script properly sets up the Python path and runs the FastAPI application.
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path for absolute imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Also add backend directory for relative imports
backend_dir = current_dir / "backend"
sys.path.insert(0, str(backend_dir))

if __name__ == "__main__":
    # Import and run the app
    from backend.main import app
    import uvicorn

    port = int(os.getenv("PORT", "8001"))
    host = os.getenv("HOST", "0.0.0.0")

    print(f"🚀 Starting Goblin Assistant backend on {host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info", access_log=True)