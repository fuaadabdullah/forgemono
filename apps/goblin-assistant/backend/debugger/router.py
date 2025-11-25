from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any
import logging

from .model_router import ModelRouter

router = APIRouter(prefix="/debugger", tags=["debugger"])
logger = logging.getLogger(__name__)
model_router = ModelRouter()


@router.post("/suggest")
async def get_debug_suggestion(
    task: str = Body(...), context: Dict[str, Any] = Body(...)
):
    try:
        route = model_router.choose_model(task, context)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    payload = {
        "task": task,
        "context": context,
        "metadata": {"source": "goblin-assistant"},
    }
    try:
        result = await model_router.call_model(route, payload)
    except Exception:
        logger.exception("Model call failed")
        raise HTTPException(status_code=502, detail="Model call failed")

    suggestion = result.get("suggestion") or result.get("text") or ""
    return {"model": route.model_name, "suggestion": suggestion, "raw": result}
