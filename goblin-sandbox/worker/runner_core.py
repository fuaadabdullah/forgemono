from __future__ import annotations

import os
import selectors
import signal
import subprocess
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class RunResult:
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool
    duration_ms: int
    truncated_stdout: bool
    truncated_stderr: bool


def build_sanitized_env(*, cwd: str) -> dict[str, str]:
    # Keep env minimal to reduce accidental access to host secrets.
    return {
        "PATH": os.getenv("PATH", "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"),
        "HOME": cwd,
        "TMPDIR": cwd,
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
    }


def _kill_process_group(proc: subprocess.Popen[bytes]) -> None:
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def run_subprocess(
    argv: list[str],
    *,
    cwd: str,
    timeout_seconds: int,
    output_limit_bytes: int,
    cpu_seconds: int,
    mem_bytes: int,
    fds: int,
    env: dict[str, str] | None = None,
) -> RunResult:
    start = time.time()

    def _preexec() -> None:
        # New session: allows killing the whole process group on timeout.
        try:
            os.setsid()
        except Exception:
            pass

        try:
            import resource

            cpu_limit = max(1, int(cpu_seconds))
            resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit, cpu_limit + 1))

            # Best-effort memory limit.
            for limit_name in ("RLIMIT_AS", "RLIMIT_DATA"):
                if hasattr(resource, limit_name):
                    resource.setrlimit(getattr(resource, limit_name), (mem_bytes, mem_bytes))
                    break

            if hasattr(resource, "RLIMIT_FSIZE"):
                resource.setrlimit(resource.RLIMIT_FSIZE, (2 * 1024 * 1024, 2 * 1024 * 1024))
            if hasattr(resource, "RLIMIT_NOFILE"):
                resource.setrlimit(resource.RLIMIT_NOFILE, (fds, fds))
            if hasattr(resource, "RLIMIT_CORE"):
                resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
            if hasattr(resource, "RLIMIT_NPROC"):
                resource.setrlimit(resource.RLIMIT_NPROC, (32, 32))
        except Exception:
            # Limits are best-effort (platform differences).
            pass

    proc = subprocess.Popen(
        argv,
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False,
        preexec_fn=_preexec,
    )

    assert proc.stdout is not None
    assert proc.stderr is not None

    sel = selectors.DefaultSelector()
    sel.register(proc.stdout, selectors.EVENT_READ, data="stdout")
    sel.register(proc.stderr, selectors.EVENT_READ, data="stderr")

    stdout_buf = bytearray()
    stderr_buf = bytearray()
    truncated_stdout = False
    truncated_stderr = False
    timed_out = False

    deadline = start + float(timeout_seconds)

    def _read_chunk(stream) -> bytes:
        try:
            if hasattr(stream, "read1"):
                return stream.read1(4096)
            return stream.read(4096)
        except Exception:
            return b""

    while sel.get_map():
        now = time.time()
        if now >= deadline:
            timed_out = True
            _kill_process_group(proc)
            break

        events = sel.select(timeout=min(0.2, max(0.0, deadline - now)))
        if not events:
            # If the process already exited, keep draining until pipes close.
            if proc.poll() is not None:
                continue
            continue

        for key, _mask in events:
            stream = key.fileobj
            kind = key.data
            chunk = _read_chunk(stream)

            if not chunk:
                try:
                    sel.unregister(stream)
                except Exception:
                    pass
                try:
                    stream.close()
                except Exception:
                    pass
                continue

            if kind == "stdout":
                if len(stdout_buf) < output_limit_bytes:
                    remaining = output_limit_bytes - len(stdout_buf)
                    stdout_buf.extend(chunk[:remaining])
                    if len(chunk) > remaining:
                        truncated_stdout = True
                else:
                    truncated_stdout = True
            else:
                if len(stderr_buf) < output_limit_bytes:
                    remaining = output_limit_bytes - len(stderr_buf)
                    stderr_buf.extend(chunk[:remaining])
                    if len(chunk) > remaining:
                        truncated_stderr = True
                else:
                    truncated_stderr = True

    # If we timed out, drain a little more (best-effort) then give up.
    if timed_out and sel.get_map():
        drain_deadline = time.time() + 1.0
        while sel.get_map() and time.time() < drain_deadline:
            events = sel.select(timeout=0.1)
            if not events:
                continue
            for key, _mask in events:
                stream = key.fileobj
                kind = key.data
                chunk = _read_chunk(stream)
                if not chunk:
                    try:
                        sel.unregister(stream)
                    except Exception:
                        pass
                    try:
                        stream.close()
                    except Exception:
                        pass
                    continue
                if kind == "stdout":
                    if len(stdout_buf) < output_limit_bytes:
                        remaining = output_limit_bytes - len(stdout_buf)
                        stdout_buf.extend(chunk[:remaining])
                    else:
                        truncated_stdout = True
                else:
                    if len(stderr_buf) < output_limit_bytes:
                        remaining = output_limit_bytes - len(stderr_buf)
                        stderr_buf.extend(chunk[:remaining])
                    else:
                        truncated_stderr = True

    # Ensure the process is reaped.
    try:
        proc.wait(timeout=1 if timed_out else None)
    except Exception:
        _kill_process_group(proc)
        try:
            proc.wait(timeout=1)
        except Exception:
            pass

    duration_ms = int((time.time() - start) * 1000)
    exit_code = 124 if timed_out else int(proc.returncode or 0)

    stdout = stdout_buf.decode("utf-8", errors="replace")
    stderr = stderr_buf.decode("utf-8", errors="replace")

    return RunResult(
        stdout=stdout,
        stderr=stderr,
        exit_code=exit_code,
        timed_out=timed_out,
        duration_ms=duration_ms,
        truncated_stdout=truncated_stdout,
        truncated_stderr=truncated_stderr,
    )
