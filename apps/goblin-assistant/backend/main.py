from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from debugger.router import router as debugger_router

app = FastAPI(
    title="GoblinOS Assistant Backend",
    description="Backend API for GoblinOS Assistant with debug capabilities",
    version="1.0.0",
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(debugger_router)


@app.get("/")
async def root():
    return {"message": "GoblinOS Assistant Backend API"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
