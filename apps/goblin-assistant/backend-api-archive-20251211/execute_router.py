from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
import uuid
import asyncio
import sys
from pathlib import Path

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from database import get_db
from models_base import Task

router = APIRouter(prefix="/execute", tags=["execute"])


class ExecuteRequest(BaseModel):
    goblin: str
    task: str
    code: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None


class ExecuteResponse(BaseModel):
    taskId: str
    status: str = "queued"


@router.post("/", response_model=ExecuteResponse)
async def execute_task(request: ExecuteRequest, db: Session = Depends(get_db)):
    """Execute a task using the specified goblin"""
    try:
        # Generate a unique task ID
        task_id = str(uuid.uuid4())

        # Create task in database
        db_task = Task(
            id=task_id,
            goblin=request.goblin,
            task=request.task,
            code=request.code,
            provider=request.provider,
            model=request.model,
            status="queued",
            user_id=None,  # TODO: Add user authentication
        )
        db.add(db_task)
        db.commit()
        db.refresh(db_task)

        # For now, simulate task execution
        # In a real implementation, this would queue the task for the goblin
        asyncio.create_task(simulate_task_execution(task_id))

        return ExecuteResponse(taskId=task_id, status="queued")

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to execute task: {str(e)}")


async def simulate_task_execution(task_id: str):
    """Simulate task execution (replace with actual goblin execution logic)"""
    await asyncio.sleep(2)  # Simulate processing time

    # Get new database session for async task
    from database import SessionLocal

    db = SessionLocal()
    try:
        # Find and update task
        db_task = db.query(Task).filter(Task.id == task_id).first()
        if db_task:
            db_task.status = "completed"
            db_task.result = f"Task executed by {db_task.goblin}: {db_task.task}"
            db.commit()
    finally:
        db.close()


@router.get("/status/{task_id}")
async def get_task_status(task_id: str, db: Session = Depends(get_db)):
    """Get the status of a task"""
    db_task = db.query(Task).filter(Task.id == task_id).first()

    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    return {
        "taskId": task_id,
        "status": db_task.status,
        "result": db_task.result,
        "goblin": db_task.goblin,
        "task": db_task.task,
    }
