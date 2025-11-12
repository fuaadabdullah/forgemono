#!/usr/bin/env python3
"""
Simple test script to run FastAPI server and test endpoints
"""
import sys
import os
import time
import subprocess
import requests
from threading import Thread

# Add the api directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

def test_server():
    """Test the server endpoints"""
    time.sleep(3)  # Wait for server to start

    try:
        # Test health endpoint
        response = requests.get("http://localhost:8001/health")
        print(f"✅ Health check: {response.status_code} - {response.json()}")

        # Test risk calculation endpoint
        test_data = {
            "entry": 100,
            "stop": 95,
            "equity": 10000,
            "risk_pct": 0.01
        }
        response = requests.post("http://localhost:8001/risk/calc", json=test_data)
        print(f"✅ Risk calc: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        else:
            print(f"Error: {response.text}")

    except Exception as e:
        print(f"❌ Test failed: {e}")

def start_server():
    """Start the FastAPI server"""
    cmd = [
        sys.executable, "-m", "uvicorn",
        "main:app",
        "--host", "127.0.0.1",
        "--port", "8001",
        "--log-level", "info"
    ]

    print("🚀 Starting FastAPI server on port 8001...")
    print(f"Command: {' '.join(cmd)}")

    # Start server in background thread
    server_process = subprocess.Popen(cmd, cwd=os.path.dirname(__file__))

    # Start testing in another thread
    test_thread = Thread(target=test_server)
    test_thread.start()

    try:
        # Wait for test to complete
        test_thread.join(timeout=10)
        print("✅ Server test completed")

        # Keep server running for manual testing
        print("🔄 Server running... Press Ctrl+C to stop")
        server_process.wait()

    except KeyboardInterrupt:
        print("🛑 Stopping server...")
        server_process.terminate()
        server_process.wait()
    except Exception as e:
        print(f"❌ Error: {e}")
        server_process.terminate()

if __name__ == "__main__":
    start_server()
