"""
Sandbox Execution API v1 - Hardened and Observable

Features:
- API versioning for stability
- Capability flags (allow_math, allow_random, allow_datetime)
- Output size limits
- Per-user rate limiting
- Observability metrics
- Stderr/stdout separation
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal
import uuid
import asyncio
import subprocess
import os
import sys
import logging
import time
import base64
from collections import defaultdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/execute", tags=["execute-v1"])

# Configuration
EXECUTION_TIMEOUT = 30
MAX_OUTPUT_SIZE = 10 * 1024 * 1024  # 10MB hard limit
MAX_OUTPUT_LINES = 10000  # Line count limit
RATE_LIMIT_WINDOW = 60  # 60 seconds
RATE_LIMIT_MAX_REQUESTS = 20  # 20 requests per minute per user

# Metrics storage (in production, use Prometheus/Datadog)
METRICS = {
    "execution_count": 0,
    "timeout_count": 0,
    "error_count": 0,
    "syntax_error_count": 0,
    "runtime_error_count": 0,
    "policy_block_count": 0,
    "total_execution_time": 0.0,
    "output_truncated_count": 0,
}

# Rate limiting storage (in production, use Redis)
RATE_LIMIT_STORE: Dict[str, list] = defaultdict(list)


class Capabilities(BaseModel):
    """Explicit capability flags for auditable policy control."""

    allow_math: bool = Field(
        True, description="Allow math module (sin, cos, sqrt, etc)"
    )
    allow_random: bool = Field(True, description="Allow random module")
    allow_datetime: bool = Field(True, description="Allow datetime module")
    allow_json: bool = Field(True, description="Allow json module")
    allow_re: bool = Field(True, description="Allow regex (re) module")
    allow_itertools: bool = Field(True, description="Allow itertools module")
    allow_collections: bool = Field(True, description="Allow collections module")


class CodeExecuteRequest(BaseModel):
    code: str = Field(..., description="Python code to execute")
    language: Literal["python"] = Field("python", description="Programming language")
    timeout: int = Field(
        EXECUTION_TIMEOUT, ge=1, le=60, description="Execution timeout in seconds"
    )
    capabilities: Capabilities = Field(
        default_factory=Capabilities, description="Capability flags"
    )
    user_id: Optional[str] = Field(
        None, description="User ID for rate limiting (optional)"
    )


class ExecutionOutput(BaseModel):
    """Separated stdout and stderr for better UX."""

    stdout: str = Field("", description="Standard output")
    stderr: str = Field("", description="Standard error")
    truncated: bool = Field(False, description="Output was truncated due to size limit")
    truncation_reason: Optional[str] = Field(
        None, description="Why output was truncated"
    )


class CodeExecuteResponse(BaseModel):
    success: bool
    output: ExecutionOutput
    execution_time: float
    error_class: Optional[str] = Field(
        None, description="Error classification: syntax, runtime, policy, timeout"
    )


class MetricsResponse(BaseModel):
    """Observability metrics."""

    execution_count: int
    timeout_count: int
    timeout_rate: float
    error_count: int
    syntax_error_count: int
    runtime_error_count: int
    policy_block_count: int
    avg_execution_time: float
    output_truncated_count: int


def check_rate_limit(user_id: str) -> bool:
    """Check if user has exceeded rate limit."""
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW

    # Clean old entries
    RATE_LIMIT_STORE[user_id] = [
        ts for ts in RATE_LIMIT_STORE[user_id] if ts > window_start
    ]

    # Check limit
    if len(RATE_LIMIT_STORE[user_id]) >= RATE_LIMIT_MAX_REQUESTS:
        return False

    # Add current request
    RATE_LIMIT_STORE[user_id].append(now)
    return True


def validate_capabilities(code: str, capabilities: Capabilities) -> Optional[str]:
    """Validate code against capability flags."""
    code_lower = code.lower()

    if not capabilities.allow_math and "import math" in code_lower:
        return "math module not allowed"
    if not capabilities.allow_random and "import random" in code_lower:
        return "random module not allowed"
    if not capabilities.allow_datetime and "import datetime" in code_lower:
        return "datetime module not allowed"
    if not capabilities.allow_json and "import json" in code_lower:
        return "json module not allowed"
    if not capabilities.allow_re and "import re" in code_lower:
        return "re module not allowed"
    if not capabilities.allow_itertools and "import itertools" in code_lower:
        return "itertools module not allowed"
    if not capabilities.allow_collections and "import collections" in code_lower:
        return "collections module not allowed"

    return None


def check_dangerous_patterns(code: str) -> Optional[str]:
    """Check for blocked patterns."""
    code_lower = code.lower()

    dangerous_patterns = [
        ("import os", "os module (file system access)"),
        ("import subprocess", "subprocess module (command execution)"),
        ("import shutil", "shutil module (file operations)"),
        ("import socket", "socket module (network access)"),
        ("__import__", "__import__ function"),
        ("from os", "os module"),
        ("from subprocess", "subprocess module"),
        ("open(", "file operations"),
        ("eval(", "eval function"),
        ("exec(", "exec function"),
        ("compile(", "compile function"),
    ]

    for pattern, description in dangerous_patterns:
        if pattern in code_lower:
            return description

    return None


def truncate_output(
    output: str, max_size: int = MAX_OUTPUT_SIZE
) -> tuple[str, bool, Optional[str]]:
    """Truncate output if it exceeds limits."""
    truncated = False
    reason = None

    # Check size
    if len(output) > max_size:
        output = output[:max_size] + "\n\n[output truncated: exceeded size limit]"
        truncated = True
        reason = "exceeded_size_limit"
        METRICS["output_truncated_count"] += 1

    # Check line count
    lines = output.split("\n")
    if len(lines) > MAX_OUTPUT_LINES:
        output = (
            "\n".join(lines[:MAX_OUTPUT_LINES])
            + "\n\n[output truncated: exceeded line limit]"
        )
        truncated = True
        reason = "exceeded_line_limit"
        METRICS["output_truncated_count"] += 1

    return output, truncated, reason


def execute_python_safe(code: str, timeout: int = EXECUTION_TIMEOUT) -> Dict[str, Any]:
    """Execute Python code with output separation and limits."""
    start_time = time.time()

    # Encode code as base64
    code_b64 = base64.b64encode(code.encode()).decode()

    # Wrapper script with stdout/stderr separation
    wrapper_code = f'''
import sys
import io
import base64
from contextlib import redirect_stdout, redirect_stderr

# Decode user code
user_code = base64.b64decode("{code_b64}").decode()

# Capture output
stdout_capture = io.StringIO()
stderr_capture = io.StringIO()

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

print("__STDOUT__:" + stdout_capture.getvalue())
print("__STDERR__:" + stderr_capture.getvalue())
print("__SUCCESS__:" + str(success))
print("__ERROR_CLASS__:" + (error_class or "none"))
'''

    try:
        # Run subprocess
        result = subprocess.run(
            [sys.executable, "-c", wrapper_code],
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )

        execution_time = time.time() - start_time

        # Parse output - extract markers and content
        stdout = ""
        stderr = ""
        success = False
        error_class = None

        output_text = result.stdout

        # Extract stdout
        if "__STDOUT__:" in output_text:
            start = output_text.find("__STDOUT__:") + 11
            end = (
                output_text.find("__STDERR__:", start)
                if "__STDERR__:" in output_text
                else len(output_text)
            )
            stdout = output_text[start:end].strip()

        # Extract stderr
        if "__STDERR__:" in output_text:
            start = output_text.find("__STDERR__:") + 11
            end = (
                output_text.find("__SUCCESS__:", start)
                if "__SUCCESS__:" in output_text
                else len(output_text)
            )
            stderr = output_text[start:end].strip()

        # Extract success flag
        if "__SUCCESS__:" in output_text:
            start = output_text.find("__SUCCESS__:") + 12
            end = (
                output_text.find("__ERROR_CLASS__:", start)
                if "__ERROR_CLASS__:" in output_text
                else len(output_text)
            )
            success = output_text[start:end].strip() == "True"

        # Extract error class
        if "__ERROR_CLASS__:" in output_text:
            start = output_text.find("__ERROR_CLASS__:") + 16
            error_class_str = output_text[start:].strip()
            error_class = error_class_str if error_class_str != "none" else None

        # Add subprocess stderr if present
        if result.stderr:
            stderr = (stderr + "\n" + result.stderr) if stderr else result.stderr
            if not error_class:
                error_class = "runtime"

        # Truncate output
        stdout, stdout_truncated, stdout_reason = truncate_output(stdout)
        stderr, stderr_truncated, stderr_reason = truncate_output(stderr)

        return {
            "success": success and result.returncode == 0,
            "stdout": stdout,
            "stderr": stderr,
            "truncated": stdout_truncated or stderr_truncated,
            "truncation_reason": stdout_reason or stderr_reason,
            "execution_time": execution_time,
            "error_class": error_class,
        }

    except subprocess.TimeoutExpired:
        METRICS["timeout_count"] += 1
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Execution timed out after {timeout} seconds",
            "truncated": False,
            "truncation_reason": None,
            "execution_time": timeout,
            "error_class": "timeout",
        }
    except Exception as e:
        METRICS["error_count"] += 1
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "truncated": False,
            "truncation_reason": None,
            "execution_time": time.time() - start_time,
            "error_class": "runtime",
        }


@router.post("/code", response_model=CodeExecuteResponse)
async def execute_code(request: CodeExecuteRequest, http_request: Request):
    """
    Execute Python code with capability controls and abuse protection.

    Features:
    - Output size limits (10MB, 10k lines)
    - Rate limiting (20 req/min per user)
    - Capability flags for auditable policy
    - Stdout/stderr separation
    - Error classification
    """
    # Update metrics
    METRICS["execution_count"] += 1

    # Rate limiting
    user_id = request.user_id or http_request.client.host
    if not check_rate_limit(user_id):
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {RATE_LIMIT_MAX_REQUESTS} requests per {RATE_LIMIT_WINDOW} seconds.",
        )

    # Validate code
    if not request.code or not request.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty")

    # Check capabilities
    capability_error = validate_capabilities(request.code, request.capabilities)
    if capability_error:
        METRICS["policy_block_count"] += 1
        raise HTTPException(
            status_code=403, detail=f"Policy violation: {capability_error}"
        )

    # Check dangerous patterns
    dangerous_pattern = check_dangerous_patterns(request.code)
    if dangerous_pattern:
        METRICS["policy_block_count"] += 1
        logger.warning(f"Blocked dangerous pattern: {dangerous_pattern}")
        raise HTTPException(
            status_code=403, detail=f"Blocked pattern: {dangerous_pattern}"
        )

    # Execute code
    result = await asyncio.get_event_loop().run_in_executor(
        None, lambda: execute_python_safe(request.code, request.timeout)
    )

    # Update metrics
    METRICS["total_execution_time"] += result["execution_time"]
    if result["error_class"] == "syntax":
        METRICS["syntax_error_count"] += 1
    elif result["error_class"] == "runtime":
        METRICS["runtime_error_count"] += 1
    elif result["error_class"]:
        METRICS["error_count"] += 1

    return CodeExecuteResponse(
        success=result["success"],
        output=ExecutionOutput(
            stdout=result["stdout"],
            stderr=result["stderr"],
            truncated=result["truncated"],
            truncation_reason=result["truncation_reason"],
        ),
        execution_time=result["execution_time"],
        error_class=result["error_class"],
    )


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """
    Get observability metrics for the sandbox.

    Tracks:
    - Execution count
    - Timeout rate
    - Error classes (syntax, runtime, policy)
    - Average execution time
    - Output truncation rate
    """
    avg_time = (
        METRICS["total_execution_time"] / METRICS["execution_count"]
        if METRICS["execution_count"] > 0
        else 0.0
    )
    timeout_rate = (
        METRICS["timeout_count"] / METRICS["execution_count"]
        if METRICS["execution_count"] > 0
        else 0.0
    )

    return MetricsResponse(
        execution_count=METRICS["execution_count"],
        timeout_count=METRICS["timeout_count"],
        timeout_rate=timeout_rate,
        error_count=METRICS["error_count"],
        syntax_error_count=METRICS["syntax_error_count"],
        runtime_error_count=METRICS["runtime_error_count"],
        policy_block_count=METRICS["policy_block_count"],
        avg_execution_time=avg_time,
        output_truncated_count=METRICS["output_truncated_count"],
    )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "v1",
        "features": [
            "capability_flags",
            "rate_limiting",
            "output_limits",
            "stdout_stderr_separation",
            "error_classification",
            "metrics",
        ],
    }
