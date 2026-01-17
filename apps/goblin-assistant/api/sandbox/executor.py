"""
Sandbox executor with automatic mode selection.

This module provides a unified interface for code execution that:
1. Uses Docker isolation when available (SANDBOX_IMAGE configured)
2. Falls back to subprocess-based execution (simulated mode)

This ensures the sandbox always works while providing full isolation
when Docker is properly configured.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .docker_sandbox import DockerSandbox, SandboxConfig, SandboxResult, get_docker_sandbox

logger = logging.getLogger(__name__)

# Constants for simulated mode
SIMULATED_TIMEOUT = 30
SIMULATED_MAX_OUTPUT = 10 * 1024 * 1024  # 10MB
SIMULATED_MAX_LINES = 10000


@dataclass
class ExecutorStatus:
    """Status information about the sandbox executor."""

    mode: str  # "docker" or "simulated"
    available: bool
    image: Optional[str]
    isolation_level: str  # "full", "process", or "none"
    docker_available: bool
    docker_image_found: bool


class SandboxExecutor:
    """
    Unified sandbox executor with automatic mode selection.
    
    Provides a consistent interface regardless of whether Docker
    is available. Always tries Docker first for full isolation,
    then falls back to subprocess execution.
    """

    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()
        self._docker_sandbox: Optional[DockerSandbox] = None
        self._status: Optional[ExecutorStatus] = None

    def _get_docker_sandbox(self) -> DockerSandbox:
        """Get or create Docker sandbox instance."""
        if self._docker_sandbox is None:
            self._docker_sandbox = DockerSandbox(self.config)
        return self._docker_sandbox

    def get_status(self) -> ExecutorStatus:
        """Get current executor status."""
        if self._status is not None:
            return self._status

        # Check Docker availability
        docker_available = False
        docker_image_found = False
        image = self.config.image

        try:
            sandbox = self._get_docker_sandbox()
            docker_available = True
            docker_image_found = sandbox.is_available()
        except ImportError:
            logger.info("docker-py not installed, using simulated mode")
        except Exception as e:
            logger.warning(f"Docker not available: {e}")

        # Determine mode
        if docker_image_found:
            mode = "docker"
            isolation = "full"
        else:
            mode = "simulated"
            isolation = "process"

        self._status = ExecutorStatus(
            mode=mode,
            available=True,
            image=image if docker_image_found else None,
            isolation_level=isolation,
            docker_available=docker_available,
            docker_image_found=docker_image_found,
        )

        return self._status

    async def execute(
        self,
        code: str,
        timeout: Optional[int] = None,
        capabilities: Optional[Dict[str, bool]] = None,
    ) -> SandboxResult:
        """
        Execute code in the best available sandbox.
        
        Args:
            code: Python code to execute
            timeout: Execution timeout (default 30s)
            capabilities: Optional capability flags for policy checks
            
        Returns:
            SandboxResult with execution output
        """
        timeout = timeout or self.config.timeout
        status = self.get_status()

        if status.mode == "docker":
            try:
                sandbox = self._get_docker_sandbox()
                return await sandbox.execute(code, timeout)
            except Exception as e:
                logger.warning(f"Docker execution failed, falling back to simulated: {e}")
                # Fall through to simulated mode

        # Simulated mode (subprocess-based)
        return await self._execute_simulated(code, timeout)

    async def _execute_simulated(self, code: str, timeout: int) -> SandboxResult:
        """Execute code using subprocess (simulated sandbox)."""
        start_time = time.time()

        # Encode code as base64
        code_b64 = base64.b64encode(code.encode()).decode()

        # Wrapper script with output separation
        wrapper_code = f'''
import sys
import io
import base64
import time
from contextlib import redirect_stdout, redirect_stderr

# Decode user code
user_code = base64.b64decode("{code_b64}").decode()

# Capture output
stdout_capture = io.StringIO()
stderr_capture = io.StringIO()

start_time = time.time()
success = False
error_class = None

try:
    with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
        exec(user_code)
    success = True
except SyntaxError as e:
    stderr_capture.write(f"SyntaxError: {{e}}")
    error_class = "syntax"
except Exception as e:
    stderr_capture.write(f"{{type(e).__name__}}: {{e}}")
    error_class = "runtime"

execution_time = time.time() - start_time

print("__STDOUT__:" + stdout_capture.getvalue())
print("__STDERR__:" + stderr_capture.getvalue())
print("__SUCCESS__:" + str(success))
print("__ERROR_CLASS__:" + (error_class or "none"))
print("__EXEC_TIME__:" + str(execution_time))
'''

        try:
            # Run subprocess
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    [sys.executable, "-c", wrapper_code],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                )
            )

            execution_time = time.time() - start_time

            # Parse output
            output = result.stdout
            stdout = self._extract_marker(output, "__STDOUT__:", "__STDERR__:")
            stderr = self._extract_marker(output, "__STDERR__:", "__SUCCESS__:")
            success_str = self._extract_marker(output, "__SUCCESS__:", "__ERROR_CLASS__:")
            error_class = self._extract_marker(output, "__ERROR_CLASS__:", "__EXEC_TIME__:")
            exec_time_str = self._extract_marker(output, "__EXEC_TIME__:", None)

            # Add subprocess stderr if present
            if result.stderr:
                stderr = (stderr + "\n" + result.stderr) if stderr else result.stderr

            # Truncate output
            stdout, stdout_truncated = self._truncate(stdout)
            stderr, stderr_truncated = self._truncate(stderr)
            truncated = stdout_truncated or stderr_truncated

            return SandboxResult(
                success=(success_str == "True") and result.returncode == 0,
                stdout=stdout,
                stderr=stderr,
                exit_code=result.returncode,
                execution_time=float(exec_time_str) if exec_time_str else execution_time,
                truncated=truncated,
                truncation_reason="output_limit" if truncated else None,
                error_class=error_class if error_class != "none" else None,
            )

        except subprocess.TimeoutExpired:
            return SandboxResult(
                success=False,
                stdout="",
                stderr=f"Execution timed out after {timeout} seconds",
                exit_code=-1,
                execution_time=timeout,
                error_class="timeout",
            )
        except Exception as e:
            return SandboxResult(
                success=False,
                stdout="",
                stderr=str(e),
                exit_code=-1,
                execution_time=time.time() - start_time,
                error_class="runtime",
            )

    def _extract_marker(self, text: str, start_marker: str, end_marker: Optional[str]) -> str:
        """Extract text between markers."""
        if start_marker not in text:
            return ""
        start = text.find(start_marker) + len(start_marker)
        if end_marker and end_marker in text[start:]:
            end = text.find(end_marker, start)
            return text[start:end].strip()
        return text[start:].strip()

    def _truncate(self, text: str) -> tuple[str, bool]:
        """Truncate text if too long."""
        if not text:
            return text, False

        truncated = False
        
        # Check byte size
        if len(text.encode("utf-8")) > SIMULATED_MAX_OUTPUT:
            # Truncate to approximate size
            text = text[:SIMULATED_MAX_OUTPUT // 2]
            text += "\n\n[output truncated: exceeded size limit]"
            truncated = True

        # Check line count
        lines = text.split("\n")
        if len(lines) > SIMULATED_MAX_LINES:
            text = "\n".join(lines[:SIMULATED_MAX_LINES])
            text += "\n\n[output truncated: exceeded line limit]"
            truncated = True

        return text, truncated


# Singleton for reuse
_executor_instance: Optional[SandboxExecutor] = None


def get_sandbox_executor(config: Optional[SandboxConfig] = None) -> SandboxExecutor:
    """Get or create sandbox executor instance."""
    global _executor_instance
    if _executor_instance is None or config is not None:
        _executor_instance = SandboxExecutor(config)
    return _executor_instance
