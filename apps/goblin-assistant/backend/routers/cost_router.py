# apps/goblin-assistant/backend/routers/cost_router.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Dict, Any

from ..database import get_db
from ..models import Task

router = APIRouter()

@router.get("/cost-summary", response_model=Dict[str, Any], tags=["cost"])
async def get_cost_summary(
    user_id: str = Query(None),
    db: Session = Depends(get_db)
):
    """Get overall cost summary"""
    query = db.query(Task).filter(Task.status == "completed")
    if user_id:
        query = query.filter(Task.user_id == user_id)

    tasks = query.all()

    if not tasks:
        return {
            "total_cost": 0.0,
            "cost_by_provider": {},
            "cost_by_model": {},
        }

    total_cost = sum(task.cost for task in tasks)

    # Group costs by provider and model from task data
    cost_by_provider = {}
    cost_by_model = {}

    for task in tasks:
        # Use provider and model from task data
        # Assuming Task model has 'provider' and 'model' attributes now,
        # which it currently doesn't, so this needs to be addressed during
        # Task model update or by joining with other tables if applicable.
        # For now, using mock 'unknown'
        provider = "unknown" # task.provider if hasattr(task, 'provider') else "unknown"
        model = "unknown" # task.model if hasattr(task, 'model') else "unknown"

        cost_by_provider[provider] = cost_by_provider.get(provider, 0.0) + task.cost
        cost_by_model[model] = cost_by_model.get(model, 0.0) + task.cost

    return {
        "total_cost": round(total_cost, 4),
        "cost_by_provider": {k: round(v, 4) for k, v in cost_by_provider.items()},
        "cost_by_model": {k: round(v, 4) for k, v in cost_by_model.items()},
    }
