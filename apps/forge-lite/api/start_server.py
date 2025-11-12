#!/usr/bin/env python3
"""
Startup script for Forge Lite FastAPI backend
"""
import sys
import os
import subprocess

# Add the api directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

def start_server():
    """Start the FastAPI server"""
    cmd = [
        sys.executable, "-m", "uvicorn",
        "main:app",
        "--host", "127.0.0.1",
        "--port", "8000",
        "--log-level", "info",
        "--reload"
    ]

    print("Starting FastAPI server...")
    print(f"Command: {' '.join(cmd)}")

    try:
        subprocess.run(cmd, cwd=os.path.dirname(__file__))
    except KeyboardInterrupt:
        print("Server stopped")
    except Exception as e:
        print(f"Error starting server: {e}")

if __name__ == "__main__":
    start_server()
