from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from GoblinOS.raptor_mini import raptor
import os

app = FastAPI()


@app.on_event("startup")
def startup_event():
    # Start the raptor monitoring loop on FastAPI startup
    try:
        raptor.start()
    except Exception:
        # Keep server running even if raptor fails to start
        pass


@app.on_event("shutdown")
def shutdown_event():
    # stop raptor monitoring on shutdown
    try:
        raptor.stop()
    except Exception:
        pass


@app.get("/health")
def health():
    return {"status": "ok"}


# Control endpoints
@app.post("/raptor/start")
def raptor_start():
    raptor.start()
    return {"running": True}


@app.post("/raptor/stop")
def raptor_stop():
    raptor.stop()
    return {"running": False}


@app.get("/raptor/status")
def raptor_status():
    status = {
        "running": bool(raptor.running),
        "config_file": getattr(raptor, "ini_path", None),
    }
    return status


# read last lines of log file safely
class LogQuery(BaseModel):
    max_chars: int = 4000


@app.post("/raptor/logs")
def raptor_logs(query: LogQuery = LogQuery()):
    logfile = raptor.cfg.get("logging", "file", fallback="logs/raptor.log")
    if not os.path.exists(logfile):
        raise HTTPException(status_code=404, detail="Log file not found")
    try:
        with open(logfile, "rb") as f:
            f.seek(0, os.SEEK_END)
            length = f.tell()
            # read last query.max_chars bytes (approx), ensure not negative
            read_from = max(0, length - query.max_chars)
            f.seek(read_from)
            data = f.read().decode("utf-8", errors="replace")
            return {"log_tail": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/raptor/demo/{value}")
def raptor_demo(value: str):
    try:
        # Trigger a demo critical worker with trace here; this helps confirm exception logging.
        if value == "boom":

            @raptor.trace
            def raise_err():
                raise RuntimeError("boom")

            try:
                raise_err()
            except RuntimeError:
                # expected - we just test trace logging
                pass
        return {"result": value}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Example of using the trace decorator on a critical function
@raptor.trace
def critical_worker(value):
    # Simulate possible error
    if value == "boom":
        raise ValueError("boom")
    return f"processed {value}"


@app.get("/demo-work/{value}")
def demo_work(value: str):
    return {"result": critical_worker(value)}
