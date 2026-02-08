#!/usr/bin/env python3
"""
RQ Worker script for processing document analysis jobs asynchronously.
Run this script to start workers that will process jobs from the Redis queue.
"""

import os
import sys
from rq import Worker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.job_queue import JobQueue


def main():
    """Start RQ worker to process jobs."""
    # Get Redis connection from job queue
    job_queue = JobQueue()
    redis_conn = job_queue.redis_conn

    # Define the queues to listen to
    queues = [job_queue.queue]

    # Start the worker
    worker = Worker(queues, connection=redis_conn, name=f"docqa-worker-{os.getpid()}")
    print(f"🚀 Starting RQ worker {worker.name}...")
    print(f"   Listening on queue: {job_queue.queue_name}")
    print(f"   Redis URL: {job_queue.redis_url}")
    print("   Press Ctrl+C to stop")

    try:
        worker.work()
    except KeyboardInterrupt:
        print("\n🛑 Worker stopped by user")
    except Exception as e:
        print(f"\n❌ Worker error: {e}")
        raise


if __name__ == "__main__":
    main()
