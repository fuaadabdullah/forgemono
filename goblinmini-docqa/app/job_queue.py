# app/job_queue.py
"""
Redis Queue (RQ) based job queue system for async document analysis.
Provides job submission, status tracking, and result retrieval.
"""

import os
import redis
from rq import Queue
from rq.job import Job
from typing import Dict, Any
from datetime import datetime, timedelta


class JobQueue:
    """RQ-based job queue for document analysis tasks."""

    def __init__(self, redis_url: str = None, queue_name: str = "docqa_jobs"):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.queue_name = queue_name
        self._redis_conn = None
        self._queue = None

    @property
    def redis_conn(self):
        """Lazy initialization of Redis connection."""
        if self._redis_conn is None:
            self._redis_conn = redis.from_url(self.redis_url)
        return self._redis_conn

    @property
    def queue(self):
        """Lazy initialization of RQ queue."""
        if self._queue is None:
            self._queue = Queue(self.queue_name, connection=self.redis_conn)
        return self._queue

    def submit_job(self, func, *args, **kwargs) -> str:
        """Submit a job to the queue and return job ID."""
        job = self.queue.enqueue(
            func,
            *args,
            **kwargs,
            job_timeout=300,  # 5 minutes timeout
            result_ttl=3600,  # Keep results for 1 hour
            failure_ttl=86400,  # Keep failed jobs for 24 hours
        )
        return job.id

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get job status and result if completed."""
        try:
            job = Job.fetch(job_id, connection=self.redis_conn)

            status_info = {
                "job_id": job_id,
                "status": job.get_status(),
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "ended_at": job.ended_at.isoformat() if job.ended_at else None,
                "enqueued_at": job.enqueued_at.isoformat() if job.enqueued_at else None,
            }

            # Add result if job is finished
            if job.is_finished:
                status_info["result"] = job.result
            elif job.is_failed:
                status_info["error"] = (
                    str(job.exc_info) if job.exc_info else "Job failed"
                )

            # Add progress info if available
            if hasattr(job, "meta") and job.meta:
                status_info["progress"] = job.meta.get("progress", {})

            return status_info

        except Exception as e:
            return {
                "job_id": job_id,
                "status": "not_found",
                "error": f"Job not found: {str(e)}",
            }

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a queued job if possible."""
        try:
            job = Job.fetch(job_id, connection=self.redis_conn)
            if job.is_queued:
                job.cancel()
                return True
            return False
        except Exception:
            return False

    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        try:
            return {
                "queued_jobs": len(self.queue),
                "finished_jobs": self.queue.finished_job_registry.count,
                "failed_jobs": self.queue.failed_job_registry.count,
                "started_jobs": self.queue.started_job_registry.count,
            }
        except Exception as e:
            return {"error": f"Failed to get queue stats: {str(e)}"}

    def cleanup_old_jobs(self, days: int = 7):
        """Clean up old completed/failed jobs."""
        try:
            # Clean up finished jobs older than specified days
            cutoff = datetime.now() - timedelta(days=days)
            self.queue.finished_job_registry.cleanup(cutoff)
            self.queue.failed_job_registry.cleanup(cutoff)
            return True
        except Exception:
            return False


# Global job queue instance
job_queue = JobQueue()


def get_job_queue() -> JobQueue:
    """Get the global job queue instance."""
    return job_queue
