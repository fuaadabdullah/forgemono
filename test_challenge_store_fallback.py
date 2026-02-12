#!/usr/bin/env python3
"""
Test script to verify challenge store behavior when Redis is unavailable
and memory fallback is disabled.
"""

import os
import sys
import logging

# Add the backend directory to the path
sys.path.insert(0, "/Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/backend")

# Set environment to disable memory fallback
os.environ["ALLOW_MEMORY_FALLBACK"] = "false"

# Force Redis usage but with invalid connection
os.environ["USE_REDIS_CHALLENGES"] = "true"
os.environ["REDIS_URL"] = "redis://invalid-host:6379"

# Configure logging
logging.basicConfig(level=logging.INFO)

try:
    from auth.challenge_store import get_challenge_store

    print(
        "Testing challenge store with Redis unavailable and memory fallback disabled..."
    )

    # This should raise ConnectionError
    store = get_challenge_store()
    print("ERROR: Expected ConnectionError but got a store:", type(store))

except ConnectionError as e:
    print("SUCCESS: ConnectionError raised as expected:", str(e))

except Exception as e:
    print("ERROR: Unexpected exception:", type(e), str(e))

print("Test completed.")
