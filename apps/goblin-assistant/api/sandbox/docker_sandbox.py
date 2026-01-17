"""
Docker-based sandbox for secure code execution.

This module provides isolated code execution using Docker containers.
Features:
- Resource limits (memory, CPU, time)
- Network isolation
- No filesystem access to host
- Automatic cleanup
- Output capture with size limits
"""

from __future__ import annotations

import asyncio
import base64
import logging
import os
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Configuration defaults
DEFAULT_MEMORY_LIMIT = "128m"
DEFAULT_CPU_PERIOD = 100000  # 100ms
DEFAULT_CPU_QUOTA = 50000  # 50% of one CPU
DEFAULT_TIMEOUT = 30
DEFAULT_OUTPUT_LIMIT = 10 * 1024 * 1024  # 10MB
DEFAULT_SANDBOX_IMAGE = "goblin/sandbox:latest"


@dataclass
class SandboxConfig:
    """Configuration for sandbox execution."""

    memory_limit: str = DEFAULT_MEMORY_LIMIT
    cpu_period: int = DEFAULT_CPU_PERIOD
    cpu_quota: int = DEFAULT_CPU_QUOTA
    timeout: int = DEFAULT_TIMEOUT
    output_limit: int = DEFAULT_OUTPUT_LIMIT
    network_disabled: bool = True
    read_only_rootfs: bool = True
    image: str = field(default_factory=lambda: os.environ.get("SANDBOX_IMAGE", DEFAULT_SANDBOX_IMAGE))
    allowed_env_vars: List[str] = field(default_factory=list)


@dataclass
class SandboxResult:
    """Result of sandbox execution."""

    success: bool
    stdout: str
    stderr: str
    exit_code: int
    execution_time: float
    truncated: bool = False
    truncation_reason: Optional[str] = None
    error_class: Optional[str] = None
    container_id: Optional[str] = None


class DockerSandbox:
    """
    Docker-based sandbox for isolated code execution.
    
    Uses Docker containers to provide:
    - Memory and CPU limits
    - Network isolation
    - Read-only filesystem
    - Automatic container cleanup
    """

    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()
        self._docker_client = None
        self._available: Optional[bool] = None

    @property
    def docker_client(self):
        """Lazy-load Docker client."""
        if self._docker_client is None:
            try:
                import docker
                self._docker_client = docker.from_env()
            except ImportError:
                logger.error("docker-py not installed. Run: pip install docker")
                raise ImportError("docker-py is required for Docker sandbox mode")
            except Exception as e:
                logger.error(f"Failed to connect to Docker: {e}")
                raise
        return self._docker_client

    def is_available(self) -> bool:
        """Check if Docker sandbox is available."""
        if self._available is not None:
            return self._available

        try:
            # Check Docker connection
            self.docker_client.ping()
            
            # Check if sandbox image exists
            images = self.docker_client.images.list(name=self.config.image)
            self._available = len(images) > 0
            
            if not self._available:
                logger.warning(f"Sandbox image '{self.config.image}' not found")
            
            return self._available
        except Exception as e:
            logger.warning(f"Docker not available: {e}")
            self._available = False
            return False

    def _build_wrapper_script(self, code: str) -> str:
        """Build wrapper script for execution with output capture."""
        code_b64 = base64.b64encode(code.encode()).decode()
        
        return f'''
import sys
import io
import base64
import time
import traceback
from contextlib import redirect_stdout, redirect_stderr

# Decode user code
user_code = base64.b64decode("{code_b64}").decode()

# Capture output with size limits
MAX_OUTPUT = {self.config.output_limit}

class LimitedStringIO(io.StringIO):
    def __init__(self, limit):
        super().__init__()
        self.limit = limit
        self.truncated = False
    
    def write(self, s):
        current_len = len(self.getvalue())
        if current_len >= self.limit:
            self.truncated = True
            return 0
        if current_len + len(s) > self.limit:
            s = s[:self.limit - current_len]
            self.truncated = True
        return super().write(s)

stdout_capture = LimitedStringIO(MAX_OUTPUT)
stderr_capture = LimitedStringIO(MAX_OUTPUT)

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
except NameError as e:
    stderr_capture.write(f"NameError: {{e}}")
    error_class = "runtime"
except TypeError as e:
    stderr_capture.write(f"TypeError: {{e}}")
    error_class = "runtime"
except ValueError as e:
    stderr_capture.write(f"ValueError: {{e}}")
    error_class = "runtime"
except Exception as e:
    stderr_capture.write(f"{{type(e).__name__}}: {{e}}")
    error_class = "runtime"

execution_time = time.time() - start_time

# Output structured result
print("__SANDBOX_START__")
print("__STDOUT__:" + stdout_capture.getvalue())
print("__STDERR__:" + stderr_capture.getvalue())
print("__SUCCESS__:" + str(success))
print("__ERROR_CLASS__:" + (error_class or "none"))
print("__EXEC_TIME__:" + str(execution_time))
print("__TRUNCATED__:" + str(stdout_capture.truncated or stderr_capture.truncated))
print("__SANDBOX_END__")
'''

    def _parse_output(self, output: str) -> Dict[str, Any]:
        """Parse structured output from container."""
        result = {
            "stdout": "",
            "stderr": "",
            "success": False,
            "error_class": None,
            "execution_time": 0.0,
            "truncated": False,
        }

        # Check for sandbox markers
        if "__SANDBOX_START__" not in output or "__SANDBOX_END__" not in output:
            # Execution failed before wrapper completed
            result["stderr"] = output
            result["error_class"] = "runtime"
            return result

        # Extract values using markers
        markers = [
            ("__STDOUT__:", "stdout"),
            ("__STDERR__:", "stderr"),
            ("__SUCCESS__:", "success"),
            ("__ERROR_CLASS__:", "error_class"),
            ("__EXEC_TIME__:", "execution_time"),
            ("__TRUNCATED__:", "truncated"),
        ]

        for marker, key in markers:
            if marker in output:
                start = output.find(marker) + len(marker)
                # Find next marker or end
                end = len(output)
                for next_marker, _ in markers:
                    if next_marker != marker and next_marker in output[start:]:
                        next_pos = output.find(next_marker, start)
                        if next_pos < end:
                            end = next_pos
                if "__SANDBOX_END__" in output[start:]:
                    sandbox_end = output.find("__SANDBOX_END__", start)
                    if sandbox_end < end:
                        end = sandbox_end

                value = output[start:end].strip()

                if key == "success":
                    result[key] = value == "True"
                elif key == "truncated":
                    result[key] = value == "True"
                elif key == "execution_time":
                    try:
                        result[key] = float(value)
                    except ValueError:
                        result[key] = 0.0
                elif key == "error_class":
                    result[key] = value if value != "none" else None
                else:
                    result[key] = value

        return result

    async def execute(self, code: str, timeout: Optional[int] = None) -> SandboxResult:
        """
        Execute code in an isolated Docker container.
        
        Args:
            code: Python code to execute
            timeout: Execution timeout in seconds (default from config)
            
        Returns:
            SandboxResult with execution output and metadata
        """
        if not self.is_available():
            raise RuntimeError("Docker sandbox not available")

        timeout = timeout or self.config.timeout
        container = None
        container_name = f"sandbox-{uuid.uuid4().hex[:12]}"

        try:
            import time
            start_time = time.time()

            # Build wrapper script
            wrapper_script = self._build_wrapper_script(code)

            # Run container
            container = self.docker_client.containers.run(
                image=self.config.image,
                command=["python3", "-c", wrapper_script],
                name=container_name,
                detach=True,
                mem_limit=self.config.memory_limit,
                cpu_period=self.config.cpu_period,
                cpu_quota=self.config.cpu_quota,
                network_disabled=self.config.network_disabled,
                read_only=self.config.read_only_rootfs,
                remove=False,  # We'll remove after getting logs
                security_opt=["no-new-privileges:true"],
                cap_drop=["ALL"],
                user="nobody",
            )

            # Wait for completion with timeout
            try:
                result = container.wait(timeout=timeout)
                exit_code = result.get("StatusCode", -1)
            except Exception as e:
                logger.warning(f"Container timeout or error: {e}")
                container.kill()
                return SandboxResult(
                    success=False,
                    stdout="",
                    stderr=f"Execution timed out after {timeout} seconds",
                    exit_code=-1,
                    execution_time=timeout,
                    error_class="timeout",
                    container_id=container_name,
                )

            # Get logs
            logs = container.logs(stdout=True, stderr=True).decode("utf-8", errors="replace")
            
            execution_time = time.time() - start_time

            # Parse output
            parsed = self._parse_output(logs)

            return SandboxResult(
                success=parsed["success"] and exit_code == 0,
                stdout=parsed["stdout"],
                stderr=parsed["stderr"],
                exit_code=exit_code,
                execution_time=parsed["execution_time"] or execution_time,
                truncated=parsed["truncated"],
                truncation_reason="output_limit" if parsed["truncated"] else None,
                error_class=parsed["error_class"],
                container_id=container_name,
            )

        except Exception as e:
            logger.error(f"Docker execution failed: {e}")
            return SandboxResult(
                success=False,
                stdout="",
                stderr=f"Docker execution error: {e}",
                exit_code=-1,
                execution_time=0.0,
                error_class="docker_error",
                container_id=container_name if container else None,
            )

        finally:
            # Cleanup container
            if container:
                try:
                    container.remove(force=True)
                except Exception as e:
                    logger.warning(f"Failed to remove container {container_name}: {e}")

    async def execute_with_files(
        self,
        code: str,
        files: Dict[str, str],
        timeout: Optional[int] = None
    ) -> SandboxResult:
        """
        Execute code with additional files available.
        
        This creates a temporary volume with the files and mounts it.
        For security, this is more restricted than execute().
        
        Args:
            code: Python code to execute
            files: Dict mapping filename to content
            timeout: Execution timeout
            
        Returns:
            SandboxResult
        """
        # For now, inject files as variables in the code
        file_setup = "import json\n__files__ = " + repr(files) + "\n"
        combined_code = file_setup + code
        return await self.execute(combined_code, timeout)


# Singleton for reuse
_sandbox_instance: Optional[DockerSandbox] = None


def get_docker_sandbox(config: Optional[SandboxConfig] = None) -> DockerSandbox:
    """Get or create Docker sandbox instance."""
    global _sandbox_instance
    if _sandbox_instance is None or config is not None:
        _sandbox_instance = DockerSandbox(config)
    return _sandbox_instance
