from __future__ import annotations

from typing import Any

from api.settings import Settings

from .runners import run_code


def run_job(job: dict[str, Any], settings: Settings) -> dict[str, str]:
    language = str(job.get("language", "")).strip().lower()
    code = str(job.get("code", ""))
    timeout_seconds = int(job.get("timeout", settings.max_timeout_seconds))

    if language not in settings.allowed_languages:
        raise ValueError(f"Unsupported language: {language}")

    result = run_code(
        language=language,
        code=code,
        timeout_seconds=timeout_seconds,
        output_limit_bytes=settings.output_limit_bytes,
        mem_bytes=settings.mem_bytes,
        fds=settings.fds,
    )

    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "exit_code": str(result.exit_code),
        "timed_out": "1" if result.timed_out else "0",
        "duration_ms": str(result.duration_ms),
        "truncated_stdout": "1" if result.truncated_stdout else "0",
        "truncated_stderr": "1" if result.truncated_stderr else "0",
    }
