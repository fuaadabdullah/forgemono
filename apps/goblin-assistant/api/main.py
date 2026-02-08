#!/usr/bin/env python3
"""
Main FastAPI application for Goblin Assistant
Combines all the routers into a single application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import all routers
from api_router import router as api_router
from routing_router import router as routing_router
from execute_router import router as execute_router
from parse_router import router as parse_router
from raptor_router import router as raptor_router
from api_keys_router import router as api_keys_router
from settings_router import router as settings_router
from search_router import router as search_router
from stream_router import router as stream_router

# Create FastAPI app
app = FastAPI(
    title="Goblin Assistant API",
    description="AI-powered development assistant with multi-provider routing",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(api_router)
app.include_router(routing_router)
app.include_router(execute_router)
app.include_router(parse_router)
app.include_router(raptor_router)
app.include_router(api_keys_router)
app.include_router(settings_router)
app.include_router(search_router)
app.include_router(stream_router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Goblin Assistant API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "routing": "available",
            "execution": "available",
            "search": "available",
            "auth": "available"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
