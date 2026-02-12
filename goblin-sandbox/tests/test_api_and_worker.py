from __future__ import annotations

from fastapi.testclient import TestClient

from api.deps import clear_dependency_caches_for_tests, get_redis
from api.main import app
from api.settings import Settings, get_settings
from .inmemory_redis import InMemoryRedis
from worker.worker_main import process_one_job


def _settings(*, run_mode: str = "queue") -> Settings:
    return Settings(
        redis_url="redis://example.invalid/0",
        queue_key="sandbox:jobs",
        job_key_prefix="sandbox:job:",
        max_code_chars=10_000,
        min_timeout_seconds=1,
        max_timeout_seconds=5,
        output_limit_bytes=40_000,
        mem_bytes=200 * 1024 * 1024,
        fds=32,
        job_ttl_seconds=60 * 60,
        run_mode=run_mode,
        api_key="",
        allowed_languages=frozenset({"python"}),
    )


def test_run_rejects_large_code():
    clear_dependency_caches_for_tests()
    r = InMemoryRedis()
    settings = _settings()

    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_redis] = lambda: r

    client = TestClient(app)
    resp = client.post(
        "/sandbox/run",
        json={
            "language": "python",
            "code": "x" * (settings.max_code_chars + 1),
            "timeout": 1,
        },
    )
    assert resp.status_code == 400


def test_queue_mode_end_to_end():
    clear_dependency_caches_for_tests()
    r = InMemoryRedis()
    settings = _settings(run_mode="queue")

    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_redis] = lambda: r

    client = TestClient(app)
    resp = client.post(
        "/sandbox/run",
        json={"language": "python", "code": "print('hi')", "timeout": 1},
    )
    assert resp.status_code == 200
    job_id = resp.json()["job_id"]

    job_key = f"{settings.job_key_prefix}{job_id}"
    meta = r.hgetall(job_key)
    assert meta["status"] == "queued"

    assert r.lists[settings.queue_key], "expected job to be enqueued"

    processed = process_one_job(r, settings, block_timeout_seconds=0)
    assert processed is True

    meta = r.hgetall(job_key)
    assert meta["status"] == "done"
    assert "hi" in meta.get("stdout", "")

    result_resp = client.get(f"/sandbox/result/{job_id}")
    assert result_resp.status_code == 200
    payload = result_resp.json()
    assert payload["status"] == "done"
    assert "hi" in payload["result"]["stdout"]


def test_sync_mode_returns_done_immediately():
    clear_dependency_caches_for_tests()
    r = InMemoryRedis()
    settings = _settings(run_mode="sync")

    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_redis] = lambda: r

    client = TestClient(app)
    resp = client.post(
        "/sandbox/run",
        json={"language": "python", "code": "print('sync')", "timeout": 1},
    )
    assert resp.status_code == 200
    job_id = resp.json()["job_id"]

    result_resp = client.get(f"/sandbox/result/{job_id}")
    assert result_resp.status_code == 200
    payload = result_resp.json()
    assert payload["status"] == "done"
    assert "sync" in payload["result"]["stdout"]
