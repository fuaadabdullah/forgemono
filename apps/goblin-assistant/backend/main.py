from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# from debugger.router import router as debugger_router
from auth.router import router as auth_router
from search_router import router as search_router
from settings_router import router as settings_router
from execute_router import router as execute_router
from api_keys_router import router as api_keys_router
from parse_router import router as parse_router
from routing_router import router as routing_router
from api_router import router as api_router
from stream_router import router as stream_router

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
# app.include_router(debugger_router)
app.include_router(auth_router)
app.include_router(search_router)
app.include_router(settings_router)
app.include_router(execute_router)
app.include_router(api_keys_router)
app.include_router(parse_router)
app.include_router(routing_router)
app.include_router(api_router)
app.include_router(stream_router)


@app.get("/")
async def root():
    return {"message": "GoblinOS Assistant Backend API"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
