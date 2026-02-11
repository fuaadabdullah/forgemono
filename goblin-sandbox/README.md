# Goblin Sandbox

FastAPI API + queue + worker for running small code snippets in a resource-limited subprocess.

## Architecture

Goblin UI -> FastAPI API (auth, validation, queue) -> worker(s) (resource-limited subprocess; optionally nsjail/firejail) -> results store/logs.

## API

- `POST /sandbox/run` - submit code, returns `job_id`
- `GET /sandbox/status/{job_id}` - quick status (`queued|running|done|failed`)
- `GET /sandbox/result/{job_id}` - result payload when ready
- `GET /sandbox/health` - health check

## Quickstart (Local)

1. Start Redis (example):

```bash
docker run --rm -p 6379:6379 redis:7
```

2. Run API:

```bash
cd goblin-sandbox
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt

export REDIS_URL="redis://localhost:6379/0"
uvicorn api.main:app --reload --host 0.0.0.0 --port 8010
```

3. Run worker (separate terminal):

```bash
cd goblin-sandbox
. .venv/bin/activate
export REDIS_URL="redis://localhost:6379/0"
python -m worker.worker_main
```

## Notes

- MVP runner uses `resource` rlimits + subprocess isolation. This is not production-grade isolation.
- Default language support is Python only.
