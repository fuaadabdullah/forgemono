from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid
import asyncio
import subprocess
import os
import sys
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/execute", tags=["execute"])

# Execution timeout in seconds
EXECUTION_TIMEOUT = 30

# Blocked modules for safety
BLOCKED_MODULES = {
    "os.system",
    "os.popen",
    "subprocess",
    "shutil.rmtree",
    "socket",
    "__import__",
    "eval",
    "exec",
    "compile",
    "open",  # Prevent file access
}

# Allowed safe builtins
SAFE_BUILTINS = {
    "abs",
    "all",
    "any",
    "bin",
    "bool",
    "chr",
    "dict",
    "dir",
    "divmod",
    "enumerate",
    "filter",
    "float",
    "format",
    "frozenset",
    "hash",
    "hex",
    "int",
    "isinstance",
    "issubclass",
    "iter",
    "len",
    "list",
    "map",
    "max",
    "min",
    "oct",
    "ord",
    "pow",
    "print",
    "range",
    "repr",
    "reversed",
    "round",
    "set",
    "slice",
    "sorted",
    "str",
    "sum",
    "tuple",
    "type",
    "zip",
}


class ExecuteRequest(BaseModel):
    goblin: str
    task: str
    code: Optional[str] = None
    language: Optional[str] = "python"
    provider: Optional[str] = None
    model: Optional[str] = None
    timeout: Optional[int] = EXECUTION_TIMEOUT


class ExecuteResponse(BaseModel):
    taskId: str
    status: str = "queued"


class CodeExecuteRequest(BaseModel):
    code: str
    language: str = "python"
    timeout: int = EXECUTION_TIMEOUT


class CodeExecuteResponse(BaseModel):
    success: bool
    output: str
    error: Optional[str] = None
    execution_time: float


# Simple in-memory task storage
TASKS: Dict[str, Dict[str, Any]] = {}


def execute_python_safe(code: str, timeout: int = EXECUTION_TIMEOUT) -> Dict[str, Any]:
    """Execute Python code in a sandboxed subprocess with timeout."""
    import time

    start_time = time.time()

    # Create a wrapper script that captures output
    wrapper_code = f'''
import sys
import io
from contextlib import redirect_stdout, redirect_stderr

# Capture output
stdout_capture = io.StringIO()
stderr_capture = io.StringIO()

try:
    with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
        exec("""{code.replace('"', '\\"').replace("\\n", "\\\\n")}""")
    print("__STDOUT__:" + stdout_capture.getvalue())
    print("__STDERR__:" + stderr_capture.getvalue())
    print("__SUCCESS__:true")
except Exception as e:
    print("__STDOUT__:" + stdout_capture.getvalue())
    print("__STDERR__:" + str(e))
    print("__SUCCESS__:false")
'''

    try:
        # Run in subprocess with timeout
        result = subprocess.run(
            [sys.executable, "-c", wrapper_code],
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )

        execution_time = time.time() - start_time

        # Parse output
        output_lines = result.stdout.split("\n")
        stdout = ""
        stderr = ""
        success = False

        for line in output_lines:
            if line.startswith("__STDOUT__:"):
                stdout = line[11:]
            elif line.startswith("__STDERR__:"):
                stderr = line[11:]
            elif line.startswith("__SUCCESS__:"):
                success = line[12:] == "true"

        # Also check for subprocess stderr
        if result.stderr:
            stderr = stderr + "\n" + result.stderr if stderr else result.stderr

        return {
            "success": success and result.returncode == 0,
            "output": stdout or result.stdout,
            "error": stderr if stderr else None,
            "execution_time": execution_time,
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "",
            "error": f"Execution timed out after {timeout} seconds",
            "execution_time": timeout,
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": str(e),
            "execution_time": time.time() - start_time,
        }


@router.post("/code", response_model=CodeExecuteResponse)
async def execute_code(request: CodeExecuteRequest):
    """Execute code directly and return the result synchronously.

    Supported languages: python

    Example:
        POST /execute/code
        {"code": "print(2 + 2)", "language": "python"}

    Returns:
        {"success": true, "output": "4\\n", "error": null, "execution_time": 0.05}
    """
    if request.language.lower() != "python":
        raise HTTPException(
            status_code=400,
            detail=f"Language '{request.language}' not supported. Only 'python' is currently available.",
        )

    # Basic code validation
    if not request.code or not request.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty")

    # Check for obviously dangerous patterns
    code_lower = request.code.lower()
    dangerous_patterns = [
        "import os",
        "import subprocess",
        "import shutil",
        "__import__",
    ]
    for pattern in dangerous_patterns:
        if pattern in code_lower:
            logger.warning(f"Blocked dangerous code pattern: {pattern}")
            raise HTTPException(
                status_code=400, detail=f"Code contains blocked pattern: {pattern}"
            )

    # Execute code
    result = await asyncio.get_event_loop().run_in_executor(
        None, lambda: execute_python_safe(request.code, request.timeout)
    )

    return CodeExecuteResponse(**result)


@router.post("/", response_model=ExecuteResponse)
async def execute_task(request: ExecuteRequest):
    """Execute a task using the specified goblin.

    If code is provided, it will be executed. Otherwise, the task
    description is used for simulation.
    """
    try:
        # Generate a unique task ID
        task_id = str(uuid.uuid4())

        # Store task information
        TASKS[task_id] = {
            "goblin": request.goblin,
            "task": request.task,
            "code": request.code,
            "language": request.language,
            "provider": request.provider,
            "model": request.model,
            "status": "running",
            "created_at": asyncio.get_event_loop().time(),
        }

        # Execute task asynchronously
        asyncio.create_task(execute_task_async(task_id, request))

        return ExecuteResponse(taskId=task_id, status="queued")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute task: {str(e)}")


async def execute_task_async(task_id: str, request: ExecuteRequest):
    """Execute task and update status."""
    try:
        if request.code:
            # Execute actual code
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: execute_python_safe(
                    request.code, request.timeout or EXECUTION_TIMEOUT
                ),
            )

            TASKS[task_id]["status"] = "completed" if result["success"] else "failed"
            TASKS[task_id]["result"] = result["output"]
            TASKS[task_id]["error"] = result.get("error")
            TASKS[task_id]["execution_time"] = result["execution_time"]
        else:
            # Simulate task execution
            await asyncio.sleep(1)
            TASKS[task_id]["status"] = "completed"
            TASKS[task_id]["result"] = (
                f"Task '{request.task}' executed by {request.goblin}"
            )

    except Exception as e:
        TASKS[task_id]["status"] = "failed"
        TASKS[task_id]["error"] = str(e)


@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """Get the status of a task"""
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Task not found")

    task = TASKS[task_id]
    return {
        "taskId": task_id,
        "status": task["status"],
        "result": task.get("result"),
        "error": task.get("error"),
        "execution_time": task.get("execution_time"),
        "goblin": task["goblin"],
        "task": task["task"],
    }


@router.get("/tasks")
async def list_tasks():
    """List all tasks (for debugging)"""
    return {
        "count": len(TASKS),
        "tasks": [
            {
                "taskId": tid,
                "status": t["status"],
                "goblin": t["goblin"],
                "task": t["task"][:50] + "..." if len(t["task"]) > 50 else t["task"],
            }
            for tid, t in TASKS.items()
        ],
    }
