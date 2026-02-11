from fastapi import FastAPI

from .routes.sandbox import router as sandbox_router

app = FastAPI(title="Goblin Sandbox API", version="0.1.0")
app.include_router(sandbox_router)


@app.get("/")
async def root():
    return {"service": "goblin-sandbox", "status": "ok"}
