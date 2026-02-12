from __future__ import annotations

import json
import logging
import time

import redis
from redis import Redis

from api.settings import Settings, get_settings

from .processor import run_job

logger = logging.getLogger("goblin_sandbox_worker")


def _job_key(settings: Settings, job_id: str) -> str:
    return f"{settings.job_key_prefix}{job_id}"


def process_one_job(r: Redis, settings: Settings, *, block_timeout_seconds: int = 5) -> bool:
    item = r.blpop(settings.queue_key, timeout=block_timeout_seconds)
    if not item:
        return False

    _queue, raw_job = item
    if isinstance(raw_job, bytes):
        raw_job = raw_job.decode("utf-8", errors="replace")

    try:
        job = json.loads(raw_job)
    except Exception:
        logger.exception("Failed to decode job payload")
        return True

    job_id = str(job.get("job_id", "")).strip()
    if not job_id:
        logger.error("Job missing job_id")
        return True

    job_key = _job_key(settings, job_id)

    started_at = time.time()
    r.hset(job_key, mapping={"status": "running", "started_at": str(started_at)})

    try:
        result = run_job(job, settings)
        finished_at = time.time()
        r.hset(
            job_key,
            mapping={
                "status": "done",
                "finished_at": str(finished_at),
                **result,
            },
        )
        return True
    except Exception as exc:
        logger.exception("Job failed")
        r.hset(
            job_key,
            mapping={
                "status": "failed",
                "finished_at": str(time.time()),
                "error": str(exc),
            },
        )
        return True
    finally:
        if settings.job_ttl_seconds > 0:
            try:
                r.expire(job_key, settings.job_ttl_seconds)
            except Exception:
                pass


def main() -> None:
    logging.basicConfig(level=logging.INFO)

    settings = get_settings()
    r = redis.from_url(settings.redis_url, decode_responses=True)

    logger.info("Worker started")
    while True:
        try:
            process_one_job(r, settings, block_timeout_seconds=5)
        except KeyboardInterrupt:
            raise
        except Exception:
            logger.exception("Worker loop error")
            time.sleep(0.5)


if __name__ == "__main__":
    main()
