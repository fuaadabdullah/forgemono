from __future__ import annotations

import os
import shutil
import sys
import tempfile

from ..runner_core import RunResult, build_sanitized_env, run_subprocess


def run_python(
    code: str,
    *,
    timeout_seconds: int,
    output_limit_bytes: int,
    mem_bytes: int,
    fds: int,
) -> RunResult:
    tmpdir = tempfile.mkdtemp(prefix="sandbox_")
    try:
        filename = os.path.join(tmpdir, "code.py")
        with open(filename, "w", encoding="utf-8") as handle:
            handle.write(code)

        env = build_sanitized_env(cwd=tmpdir)

        return run_subprocess(
            [sys.executable, "-I", "-B", "code.py"],
            cwd=tmpdir,
            timeout_seconds=timeout_seconds,
            output_limit_bytes=output_limit_bytes,
            cpu_seconds=timeout_seconds,
            mem_bytes=mem_bytes,
            fds=fds,
            env=env,
        )
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
