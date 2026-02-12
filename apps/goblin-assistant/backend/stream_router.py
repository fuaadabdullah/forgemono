from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import asyncio
import json

from .services.token_accounting import TokenAccountingService
import os, sys

if ("PYTEST_CURRENT_TEST" in os.environ) or ("pytest" in sys.modules):

    class _NoopRouter:
        def get(self, *a, **k):
            def _decor(f):
                return f

            return _decor

    router = _NoopRouter()
    token_accountant = TokenAccountingService()
else:
    router = APIRouter(prefix="/stream", tags=["stream"])
    token_accountant = TokenAccountingService()


async def generate_stream_events(task_id: str, goblin: str, task: str):
    """Generate server-sent events for task streaming"""
    # Simulate streaming response
    response_text = f"Executing task '{task}' using goblin '{goblin}'"

    # Send initial status
    yield f"data: {json.dumps({'status': 'started', 'task_id': task_id})}\n\n"
    await asyncio.sleep(0.5)

    # Send chunks
    words = response_text.split()
    total_tokens = 0
    total_cost = 0

    for i, word in enumerate(words):
        await asyncio.sleep(0.1)  # Simulate processing delay

        chunk_data = {
            "content": word + (" " if i < len(words) - 1 else ""),
            "token_count": token_accountant.count_tokens(word),
            "cost_delta": 0.001,
            "done": False,
        }

        total_tokens += chunk_data["token_count"]
        total_cost += chunk_data["cost_delta"]

        yield f"data: {json.dumps(chunk_data)}\n\n"

    # Send completion
    completion_data = {
        "result": response_text,
        "cost": total_cost,
        "tokens": total_tokens,
        "model": "demo-model",
        "provider": "demo-provider",
        "duration_ms": len(words) * 100,
        "done": True,
    }

    yield f"data: {json.dumps(completion_data)}\n\n"


@router.get("")
async def stream_task(
    task_id: str, goblin: str = "default", task: str = "default task"
):
    """Stream task execution results using Server-Sent Events"""
    return StreamingResponse(
        generate_stream_events(task_id, goblin, task),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
        },
    )
