# Gaslight Workspace

This folder contains a small workspace for the Gaslight project — a Unity 2D (URP) game with a Python FastAPI backend.

This workspace contains the following folders:

- `docs/` — project blueprint and reference material
- `unity/` — Unity-related files and notes
- `backend/` — minimal FastAPI backend scaffold

For full development instructions, see `docs/GASLIGHT_BLUEPRINT.md`.

Quick start (backend):

```bash
cd apps/gaslight/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
