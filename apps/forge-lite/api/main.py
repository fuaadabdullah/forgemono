from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from routers import risk, market


load_dotenv()

app = FastAPI(title="Forge Lite API", version="0.1.0")

# Allow everything locally; tighten later via env.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


app.include_router(risk.router, prefix="/risk", tags=["risk"])
app.include_router(market.router, prefix="/market", tags=["market"])
