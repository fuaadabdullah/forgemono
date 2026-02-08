# Backend (FastAPI)

This folder contains a minimal FastAPI backend scaffold for Gaslight.

How to run:

```bash
cd apps/gaslight/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API:

- POST /route: expects JSON body { "npc_id": string, "mission": int, "message": string } and returns a simple RouteResponse.

Use this file as a starting point to add mission routing, NPC logic, and more advanced chat features.
