#!/usr/bin/env python3
import subprocess
import time
import signal
import sys

# Start the server
print("Starting FastAPI server...")
server = subprocess.Popen([
    "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"
], cwd="/Users/fuaadabdullah/ForgeMonorepo/goblin-assistant/api")

# Wait for server to start
time.sleep(5)

# Run the integration test
print("Running integration test...")
test = subprocess.Popen([
    "python3", "scripts/test_goblin_colab_integration.py", "--backend-url", "http://localhost:8000"
], cwd="/Users/fuaadabdullah/ForgeMonorepo")

# Wait for test to complete
test.wait()

# Stop the server
print("Stopping server...")
server.terminate()
server.wait()

sys.exit(test.returncode)
