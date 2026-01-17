"""
Sandbox Execution API v2 - Docker Isolated

Features:
- Docker-based isolation when available (auto-fallback to simulated mode)
- API versioning for stability
- Capability flags (allow_math, allow_random, allow_datetime)
- Output size limits
- Per-user rate limiting
- Observability metrics
- Stderr/stdout separation
- Automatic sandbox mode detection

This is an upgrade from v1 that adds proper Docker isolation.
The API is backwards compatible with v1.
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal
import logging
import time
from collections import defaultdict

# Import sandbox module
try:
    from sandbox import get_sandbox_executor, SandboxConfig
    SANDBOX_AVAILABLE = True
except ImportError:
    SANDBOX_AVAILABLE = False
    logging.warning("Sandbox module not available, using v1 fallback")

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v2/execute", tags=["execute-v2"])

# Configuration
EXECUTION_TIMEOUT = 30
MAX_OUTPUT_SIZE = 10 * 1024 * 1024  # 10MB hard limit
MAX_OUTPUT_LINES = 10000  # Line count limit
RATE_LIMIT_WINDOW = 60  # 60 seconds
RATE_LIMIT_MAX_REQUESTS = 20  # 20 requests per minute per user

# Metrics storage (in production, use Prometheus/Datadog)
METRICS = {
    "execution_count": 0,
    "docker_execution_count": 0,
    "simulated_execution_count": 0,
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

# Dangerous patterns to block
DANGEROUS_PATTERNS = [
    "import os",
    "from os",
    "import subprocess",
    "from subprocess",
    "import socket",
    "from socket",
    "import shutil",
    "from shutil",
    "__import__",
    "eval(",
    "exec(",
    "compile(",
    "open(",
    "file(",
    "input(",
]


class Capabilities(BaseModel):
    """Explicit capability flags for auditable policy control."""

    allow_math: bool = Field(True, description="Allow math module")
    allow_random: bool = Field(True, description="Allow random module")
    allow_datetime: bool = Field(True, description="Allow datetime module")
    allow_json: bool = Field(True, description="Allow json module")
    allow_re: bool = Field(True, description="Allow regex (re) module")
    allow_itertools: bool = Field(True, description="Allow itertools module")
    allow_collections: bool = Field(True, description="Allow collections module")
    allow_numpy: bool = Field(True, description="Allow numpy module (Docker mode only)")
    allow_pandas: bool = Field(True, description="Allow pandas module (Docker mode only)")


class CodeExecuteRequest(BaseModel):
    code: str = Field(..., description="Python code to execute")
    language: Literal["python"] = Field("python", description="Programming language")
    timeout: int = Field(EXECUTION_TIMEOUT, ge=1, le=60, description="Timeout in seconds")
    capabilities: Capabilities = Field(default_factory=Capabilities)
    user_id: Optional[str] = Field(None, description="User ID for rate limiting")


class ExecutionOutput(BaseModel):
    """Separated stdout and stderr."""

    stdout: str = Field("", description="Standard output")
    stderr: str = Field("", description="Standard error")
    truncated: bool = Field(False, description="Output was truncated")
    truncation_reason: Optional[str] = Field(None)


class CodeExecuteResponse(BaseModel):
    success: bool
    output: ExecutionOutput
    execution_time: float
    error_class: Optional[str] = Field(None, description="syntax, runtime, policy, timeout")
    sandbox_mode: str = Field("unknown", description="docker or simulated")


class SandboxStatus(BaseModel):
    """Sandbox status information."""

    mode: str
    available: bool
    docker_available: bool
    docker_image_found: bool
    isolation_level: str
    image: Optional[str]


class MetricsResponse(BaseModel):
    """Observability metrics."""

    execution_count: int
    docker_execution_count: int
    simulated_execution_count: int
    timeout_count: int
    timeout_rate: float
    error_count: int
    syntax_error_count: int
    runtime_error_count: int
    policy_block_count: int
    avg_execution_time: float
    output_truncated_count: int


def check_rate_limit(user_id: str) -> bool:
    """Check if user is within rate limit."""
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW

    # Clean old entries
    RATE_LIMIT_STORE[user_id] = [
        ts for ts in RATE_LIMIT_STORE[user_id] if ts > window_start
    ]

    # Check limit
    if len(RATE_LIMIT_STORE[user_id]) >= RATE_LIMIT_MAX_REQUESTS:
        return False

    # Record this request
    RATE_LIMIT_STORE[user_id].append(now)
    return True


def check_dangerous_patterns(code: str) -> Optional[str]:
    """Check for dangerous code patterns."""
    code_lower = code.lower()
    for pattern in DANGEROUS_PATTERNS:
        if pattern.lower() in code_lower:
            return pattern
    return None


def validate_capabilities(code: str, capabilities: Capabilities) -> Optional[str]:
    """Validate code against capability restrictions."""
    checks = [
        (not capabilities.allow_math, "import math", "math module not allowed"),
        (not capabilities.allow_random, "import random", "random module not allowed"),
        (not capabilities.allow_datetime, "import datetime", "datetime module not allowed"),
        (not capabilities.allow_json, "import json", "json module not allowed"),
        (not capabilities.allow_re, "import re", "re module not allowed"),
        (not capabilities.allow_itertools, "import itertools", "itertools module not allowed"),
        (not capabilities.allow_collections, "import collections", "collections module not allowed"),
        (not capabilities.allow_numpy, "import numpy", "numpy module not allowed"),
        (not capabilities.allow_pandas, "import pandas", "pandas module not allowed"),
    ]

    for disabled, pattern, error in checks:
        if disabled and pattern in code:
            return error

    return None


@router.post("/code", response_model=CodeExecuteResponse)
async def execute_code(request: CodeExecuteRequest, http_request: Request):
    """
    Execute Python code with Docker isolation when available.

    Features:
    - Docker-based isolation (auto-detects availability)
    - Output size limits (10MB, 10k lines)
    - Rate limiting (20 req/min per user)
    - Capability flags for auditable policy
    - Stdout/stderr separation
    - Error classification
    """
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
        raise HTTPException(status_code=403, detail=f"Policy violation: {capability_error}")

    # Check dangerous patterns
    dangerous_pattern = check_dangerous_patterns(request.code)
    if dangerous_pattern:
        METRICS["policy_block_count"] += 1
        logger.warning(f"Blocked dangerous pattern: {dangerous_pattern}")
        raise HTTPException(status_code=403, detail=f"Blocked pattern: {dangerous_pattern}")

    # Execute code
    if SANDBOX_AVAILABLE:
        executor = get_sandbox_executor()
        result = await executor.execute(request.code, request.timeout)
        
        status = executor.get_status()
        sandbox_mode = status.mode
        
        if sandbox_mode == "docker":
            METRICS["docker_execution_count"] += 1
        else:
            METRICS["simulated_execution_count"] += 1
    else:
        # Fallback to v1 execution
        from execute_router_v1 import execute_python_safe
        import asyncio
        
        result_dict = await asyncio.get_event_loop().run_in_executor(
            None, lambda: execute_python_safe(request.code, request.timeout)
        )
        
        # Convert to SandboxResult-like structure
        class MockResult:
            def __init__(self, d):
                self.success = d["success"]
                self.stdout = d["stdout"]
                self.stderr = d["stderr"]
                self.execution_time = d["execution_time"]
                self.truncated = d["truncated"]
                self.truncation_reason = d["truncation_reason"]
                self.error_class = d["error_class"]
        
        result = MockResult(result_dict)
        sandbox_mode = "simulated-v1"
        METRICS["simulated_execution_count"] += 1

    # Update metrics
    METRICS["total_execution_time"] += result.execution_time
    if result.error_class == "syntax":
        METRICS["syntax_error_count"] += 1
    elif result.error_class == "runtime":
        METRICS["runtime_error_count"] += 1
    elif result.error_class == "timeout":
        METRICS["timeout_count"] += 1
    elif result.error_class:
        METRICS["error_count"] += 1
    if result.truncated:
        METRICS["output_truncated_count"] += 1

    return CodeExecuteResponse(
        success=result.success,
        output=ExecutionOutput(
            stdout=result.stdout,
            stderr=result.stderr,
            truncated=result.truncated,
            truncation_reason=result.truncation_reason,
        ),
        execution_time=result.execution_time,
        error_class=result.error_class,
        sandbox_mode=sandbox_mode,
    )


@router.get("/status", response_model=SandboxStatus)
async def get_status():
    """
    Get sandbox executor status.

    Returns information about:
    - Current execution mode (docker/simulated)
    - Docker availability
    - Sandbox image status
    - Isolation level
    """
    if SANDBOX_AVAILABLE:
        executor = get_sandbox_executor()
        status = executor.get_status()
        return SandboxStatus(
            mode=status.mode,
            available=status.available,
            docker_available=status.docker_available,
            docker_image_found=status.docker_image_found,
            isolation_level=status.isolation_level,
            image=status.image,
        )
    else:
        return SandboxStatus(
            mode="simulated-v1",
            available=True,
            docker_available=False,
            docker_image_found=False,
            isolation_level="process",
            image=None,
        )


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """
    Get observability metrics for the sandbox.

    Tracks:
    - Execution count (total, docker, simulated)
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
        docker_execution_count=METRICS["docker_execution_count"],
        simulated_execution_count=METRICS["simulated_execution_count"],
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
    if SANDBOX_AVAILABLE:
        executor = get_sandbox_executor()
        status = executor.get_status()
        return {
            "status": "healthy",
            "version": "v2",
            "mode": status.mode,
            "isolation": status.isolation_level,
            "docker_available": status.docker_available,
            "features": [
                "docker_isolation",
                "capability_flags",
                "rate_limiting",
                "output_limits",
                "stdout_stderr_separation",
                "error_classification",
                "metrics",
                "auto_mode_selection",
            ],
        }
    else:
        return {
            "status": "healthy",
            "version": "v2",
            "mode": "simulated-v1",
            "isolation": "process",
            "docker_available": False,
            "features": [
                "capability_flags",
                "rate_limiting",
                "output_limits",
                "stdout_stderr_separation",
                "error_classification",
                "metrics",
            ],
        }
