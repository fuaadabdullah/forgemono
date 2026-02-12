import os
import subprocess
import sys
import tempfile
import time
from typing import Optional

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, Field

app = FastAPI(title="Goblin Sandbox Runner", version="1.0.0")


class RunRequest(BaseModel):
    code: str = Field(..., min_length=1)
    language: str = "python"
    timeout_seconds: int = Field(10, ge=1, le=60)
    max_output_chars: int = Field(12000, ge=1000, le=50000)


class RunResponse(BaseModel):
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool
    duration_ms: int


def _limit_output(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 60] + "\n... output truncated ..."


def _build_env() -> dict:
    return {
        "PATH": os.getenv("PATH", "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"),
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
    }


def _apply_resource_limits(timeout_seconds: int) -> None:
    try:
        import resource

        cpu_limit = max(1, min(timeout_seconds, 60))
        resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit, cpu_limit + 1))
        memory_limit = 512 * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))
        resource.setrlimit(resource.RLIMIT_FSIZE, (2 * 1024 * 1024, 2 * 1024 * 1024))
        resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
    except Exception:
        # Best effort: ignore if limits are unsupported in the environment.
        return


def _run_python(code: str, timeout_seconds: int) -> tuple[int, str, str, bool, int]:
    start = time.time()
    timed_out = False

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as temp_file:
        temp_file.write(code)
        script_path = temp_file.name

    try:
        result = subprocess.run(
            [sys.executable, "-I", "-B", script_path],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            env=_build_env(),
            preexec_fn=lambda: _apply_resource_limits(timeout_seconds),
        )
        stdout = result.stdout
        stderr = result.stderr
        exit_code = result.returncode
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stdout = exc.stdout or ""
        stderr = exc.stderr or "Execution timed out"
        exit_code = 124
    finally:
        try:
            os.unlink(script_path)
        except Exception:
            pass

    duration_ms = int((time.time() - start) * 1000)
    return exit_code, stdout, stderr, timed_out, duration_ms


@app.post("/run", response_model=RunResponse)
async def run_code(request: RunRequest, x_api_key: Optional[str] = Header(default=None)):
    required_key = os.getenv("SANDBOX_RUNNER_API_KEY")
    if required_key and x_api_key != required_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    language = request.language.lower().strip()
    if language not in {"python", "py"}:
        raise HTTPException(status_code=400, detail="Only Python is supported right now")

    exit_code, stdout, stderr, timed_out, duration_ms = _run_python(
        request.code, request.timeout_seconds
    )

    stdout = _limit_output(stdout, request.max_output_chars)
    stderr = _limit_output(stderr, request.max_output_chars)

    return RunResponse(
        stdout=stdout,
        stderr=stderr,
        exit_code=exit_code,
        timed_out=timed_out,
        duration_ms=duration_ms,
    )
