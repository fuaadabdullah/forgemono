# Raptor Mini — Lightweight Diagnostics

A compact diagnostics module that provides minimal performance logging, crash tracing, and a simple ini-driven configuration.

## Why Raptor Mini

- Lightweight and non-invasive
- Toggleable via `config/raptor.ini`
- Provides CPU/memory sampling and exception trace logging
- Works for FastAPI apps and worker processes

## Quick Start

1. Ensure `config/raptor.ini` exists (a sample has been added):

```
[logging]
level = INFO
file = logs/raptor.log

[performance]
enable_cpu = true
enable_memory = true
sample_rate_ms = 200

[features]
trace_exceptions = true
enable_dev_flags = false
```

2. Import and start Raptor Mini in your app (FastAPI example):

```python
from GoblinOS.raptor_mini import raptor

# In FastAPI app startup
@ap.on_event("startup")
def startup():
    raptor.start()

@ap.on_event("shutdown")
def shutdown():
    raptor.stop()
```

3. To trace a critical function:

```python

@raptor.trace
def critical_job(...):
    # do the work
```

## Diagnostics

- Log file is controlled by `config/raptor.ini`
- Sampling rate and metrics are configured under `[performance]`
- Toggle exception tracing under `[features]`

## Notes

- `psutil` is optional; if not installed, CPU/memory sampling will be disabled gracefully.
- Keep `sample_rate_ms` reasonably large to avoid expensive sampling; defaults are conservative.
- Thread is started as a daemon to avoid blocking shutdown.

## Testing

- Basic tests are included under `GoblinOS/tests/test_raptor_mini.py`.


## Extensibility

- Add additional metrics in `monitor_loop` as needed, but keep checks cheap and minimal.
- Consider adding a rotating file handler if log size management is desired.

## Demo Integration in Goblin Assistant

A simple UI demo is available in the goblin assistant frontend. It adds a "Raptor Mini Demo" panel that allows you to control the raptor monitor and view logs.

How to use the demo:

- Start your backend (FastAPI).
- Open the goblin assistant UI and navigate to the Cost Estimation panel (demo includes the Raptor Mini panel).
- Use the Start/Stop buttons to enable/disable monitoring on the server.
- Click "Fetch Logs" to retrieve the last log tail from the raptor log file.
- Click "Trigger Boom" to trigger a demo exception that will be logged by Raptor Mini and view the log tail.

For automated control, the following endpoints are added to the FastAPI backend:

- POST /raptor/start — start monitoring
- POST /raptor/stop — stop monitoring
- GET /raptor/status — return running status and config file
- POST /raptor/logs — return tail of the raptor log file
- GET /raptor/demo/{value} — demo trigger; use 'boom' to trigger an error and examine logs

The Goblin Assistant demo uses these endpoints and the frontend calls named client helpers.
