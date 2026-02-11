from __future__ import annotations

from .python_runner import run_python


def run_code(
    *,
    language: str,
    code: str,
    timeout_seconds: int,
    output_limit_bytes: int,
    mem_bytes: int,
    fds: int,
):
    lang = language.strip().lower()
    if lang in {"python", "py"}:
        return run_python(
            code,
            timeout_seconds=timeout_seconds,
            output_limit_bytes=output_limit_bytes,
            mem_bytes=mem_bytes,
            fds=fds,
        )

    raise ValueError(f"Unsupported language: {language}")
