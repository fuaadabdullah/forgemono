from __future__ import annotations

import json
import time
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException
from redis import Redis

from ..deps import get_redis
from ..schemas import HealthResp, ResultData, ResultResp, RunReq, RunResp, StatusResp
from ..settings import Settings, get_settings

router = APIRouter(prefix="/sandbox", tags=["sandbox"])


def _job_key(settings: Settings, job_id: str) -> str:
    return f"{settings.job_key_prefix}{job_id}"


def _require_api_key(settings: Settings, provided: str | None) -> None:
    if not settings.api_key:
        return
    if provided != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


def _to_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _to_int(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _to_bool(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y"}


@router.post("/run", response_model=RunResp)
async def run(
    req: RunReq,
    r: Redis = Depends(get_redis),
    settings: Settings = Depends(get_settings),
    x_api_key: str | None = Header(default=None),
):
    _require_api_key(settings, x_api_key)

    if len(req.code) > settings.max_code_chars:
        raise HTTPException(status_code=400, detail="Code too large")

    language = req.language.lower().strip()
    if language not in settings.allowed_languages:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {language}")

    timeout = int(req.timeout)
    if timeout < settings.min_timeout_seconds or timeout > settings.max_timeout_seconds:
        raise HTTPException(
            status_code=400,
            detail=f"Timeout must be between {settings.min_timeout_seconds} and {settings.max_timeout_seconds} seconds",
        )

    job_id = str(uuid.uuid4())
    created_at = time.time()

    job_key = _job_key(settings, job_id)
    r.hset(
        job_key,
        mapping={
            "status": "queued",
            "language": language,
            "timeout": str(timeout),
            "created_at": str(created_at),
        },
    )
    if settings.job_ttl_seconds > 0:
        r.expire(job_key, settings.job_ttl_seconds)

    job = {
        "job_id": job_id,
        "language": language,
        "code": req.code,
        "timeout": timeout,
    }

    if settings.run_mode == "sync":
        # MVP mode: execute in-process (still uses subprocess + rlimits). Avoid in production.
        from worker.processor import run_job  # local package import

        r.hset(job_key, mapping={"status": "running", "started_at": str(time.time())})
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
        except Exception as exc:
            r.hset(
                job_key,
                mapping={
                    "status": "failed",
                    "finished_at": str(time.time()),
                    "error": str(exc),
                },
            )
    else:
        r.rpush(settings.queue_key, json.dumps(job))

    return RunResp(job_id=job_id)


@router.get("/status/{job_id}", response_model=StatusResp)
async def status(
    job_id: str,
    r: Redis = Depends(get_redis),
    settings: Settings = Depends(get_settings),
    x_api_key: str | None = Header(default=None),
):
    _require_api_key(settings, x_api_key)

    meta = r.hgetall(_job_key(settings, job_id))
    if not meta:
        raise HTTPException(status_code=404, detail="Job not found")

    return StatusResp(
        job_id=job_id,
        status=meta.get("status", "unknown"),
        created_at=_to_float(meta.get("created_at")),
        started_at=_to_float(meta.get("started_at")),
        finished_at=_to_float(meta.get("finished_at")),
    )


@router.get("/result/{job_id}", response_model=ResultResp)
async def result(
    job_id: str,
    r: Redis = Depends(get_redis),
    settings: Settings = Depends(get_settings),
    x_api_key: str | None = Header(default=None),
):
    _require_api_key(settings, x_api_key)

    meta = r.hgetall(_job_key(settings, job_id))
    if not meta:
        raise HTTPException(status_code=404, detail="Job not found")

    job_status = meta.get("status", "unknown")

    if job_status not in {"done", "failed"}:
        return ResultResp(job_id=job_id, status=job_status)

    if job_status == "failed":
        return ResultResp(
            job_id=job_id,
            status=job_status,
            error=meta.get("error") or "Job failed",
        )

    data = ResultData(
        stdout=meta.get("stdout", ""),
        stderr=meta.get("stderr", ""),
        exit_code=int(meta.get("exit_code", "0")),
        timed_out=_to_bool(meta.get("timed_out")),
        duration_ms=_to_int(meta.get("duration_ms")),
        truncated_stdout=_to_bool(meta.get("truncated_stdout")),
        truncated_stderr=_to_bool(meta.get("truncated_stderr")),
    )

    return ResultResp(job_id=job_id, status=job_status, result=data)


@router.get("/health", response_model=HealthResp)
async def health(r: Redis = Depends(get_redis)):
    try:
        ok = bool(r.ping())
    except Exception:
        ok = False

    return HealthResp(status="ok" if ok else "down", redis="ok" if ok else "down")
