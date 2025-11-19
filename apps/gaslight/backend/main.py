from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class RouteRequest(BaseModel):
    npc_id: str
    mission: int
    message: str

class RouteResponse(BaseModel):
    npc_response: str
    goblin_hint: str
    mission_status: str
    next_step: int


@app.post('/route', response_model=RouteResponse)
def route_message(req: RouteRequest):
    """A minimal route that returns placeholder NPC and goblin replies.

    Replace this with the backend routing logic tied to mission and NPC.
    """
    return RouteResponse(
        npc_response=f"NPC({req.npc_id}) responds to: {req.message}",
        goblin_hint='Goblin side-comment...',
        mission_status='in_progress',
        next_step=req.mission + 1,
    )
