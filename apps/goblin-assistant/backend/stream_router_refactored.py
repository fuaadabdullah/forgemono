"""
Refactored stream router using the new StreamProcessor service.

This demonstrates how the stream_router.py can be simplified by using
the new StreamProcessor service for better organization and maintainability.
"""

import logging
import time
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session

from .services.stream_processor import StreamProcessor
from .database import get_db
from .config import settings
from .auth import get_current_user, get_client_ip
from .models import User

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/stream",
    tags=["stream"],
    responses={404: {"description": "Not found"}},
)


@router.post("/chat")
async def stream_chat_completion(
    request: Request,
    session_id: str,
    messages: List[Dict[str, Any]],
    model: str,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    user_id: Optional[str] = None,
    client_ip: Optional[str] = None,
    request_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Stream chat completion endpoint using the new StreamProcessor service.
    
    This endpoint demonstrates how the complex streaming logic can be
    simplified by using the StreamProcessor service.
    """
    # Get user and client IP if not provided
    if not user_id:
        try:
            current_user = await get_current_user(request)
            user_id = current_user.id if current_user else None
        except HTTPException:
            user_id = None

    if not client_ip:
        client_ip = get_client_ip(request)

    # Create StreamProcessor instance
    stream_processor = StreamProcessor(db)

    try:
        # Process streaming request using the service
        async def stream_generator():
            async for chunk in stream_processor.process_streaming_request(
                session_id=session_id,
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                user_id=user_id,
                client_ip=client_ip,
                request_id=request_id,
            ):
                yield chunk

        return stream_generator()

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Stream chat completion error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/completion")
async def stream_completion(
    request: Request,
    prompt: str,
    model: str,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    user_id: Optional[str] = None,
    client_ip: Optional[str] = None,
    request_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Stream completion endpoint using the new StreamProcessor service.
    
    This endpoint demonstrates how the complex streaming logic can be
    simplified by using the StreamProcessor service.
    """
    # Get user and client IP if not provided
    if not user_id:
        try:
            current_user = await get_current_user(request)
            user_id = current_user.id if current_user else None
        except HTTPException:
            user_id = None

    if not client_ip:
        client_ip = get_client_ip(request)

    # Convert prompt to messages format
    messages = [{"role": "user", "content": prompt}]

    # Create StreamProcessor instance
    stream_processor = StreamProcessor(db)

    try:
        # Process streaming request using the service
        async def stream_generator():
            async for chunk in stream_processor.process_streaming_request(
                session_id=f"completion_{request_id or ''}",
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                user_id=user_id,
                client_ip=client_ip,
                request_id=request_id,
            ):
                yield chunk

        return stream_generator()

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Stream completion error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/status")
async def stream_status(
    request_id: Optional[str] = None,
    session_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Get streaming status for a request or session.
    
    This endpoint demonstrates how status can be retrieved
    using the StreamProcessor service.
    """
    # This would integrate with the StreamProcessor's metrics collection
    # For now, return a placeholder response
    return {
        "status": "active",
        "request_id": request_id,
        "session_id": session_id,
        "timestamp": int(time.time()),
    }


@router.delete("/cancel")
async def cancel_stream(
    request_id: str,
    db: Session = Depends(get_db),
):
    """
    Cancel a streaming request.
    
    This endpoint demonstrates how streaming requests can be cancelled
    using the StreamProcessor service.
    """
    # This would integrate with the StreamProcessor's cancellation logic
    # For now, return a placeholder response
    return {
        "message": "Stream cancellation requested",
        "request_id": request_id,
        "cancelled": True,
    }


# Additional utility endpoints for stream management

@router.get("/metrics")
async def get_stream_metrics(
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Get streaming metrics for monitoring and debugging.
    
    This endpoint demonstrates how metrics can be retrieved
    using the StreamProcessor service.
    """
    # This would integrate with the StreamProcessor's metrics collection
    # For now, return a placeholder response
    return {
        "session_id": session_id,
        "user_id": user_id,
        "metrics": {
            "total_requests": 0,
            "total_tokens": 0,
            "average_response_time": 0.0,
            "error_rate": 0.0,
        },
        "timestamp": int(time.time()),
    }


@router.get("/health")
async def stream_health_check():
    """
    Health check for streaming service.
    
    This endpoint demonstrates how health checks can be implemented
    using the StreamProcessor service.
    """
    # This would integrate with the StreamProcessor's health monitoring
    # For now, return a placeholder response
    return {
        "status": "healthy",
        "service": "stream_processor",
        "timestamp": int(time.time()),
        "version": "1.0.0",
    }


# Error handling middleware for streaming endpoints

@router.exception_handler(Exception)
async def stream_exception_handler(request: Request, exc: Exception):
    """Handle exceptions in streaming endpoints."""
    logger.error(f"Stream endpoint error: {exc}")
    
    return {
        "error": {
            "type": type(exc).__name__,
            "message": str(exc),
            "code": 500,
        },
        "timestamp": int(time.time()),
    }


# Rate limiting middleware for streaming endpoints

@router.middleware("http")
async def stream_rate_limit_middleware(request: Request, call_next):
    """Apply rate limiting to streaming endpoints."""
    # This would integrate with the StreamProcessor's rate limiting
    # For now, just pass through
    response = await call_next(request)
    return response


# Logging middleware for streaming endpoints

@router.middleware("http")
async def stream_logging_middleware(request: Request, call_next):
    """Log streaming requests and responses."""
    start_time = time.time()
    
    # Log request
    logger.info(f"Stream request: {request.method} {request.url}")
    
    # Process request
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(f"Stream response: {response.status_code} in {process_time:.2f}s")
    
    return response


# Dependency injection for StreamProcessor

def get_stream_processor(db: Session = Depends(get_db)) -> StreamProcessor:
    """Get StreamProcessor instance with database session."""
    return StreamProcessor(db)


# Example of using dependency injection

@router.post("/chat_with_injection")
async def stream_chat_with_injection(
    request: Request,
    session_id: str,
    messages: List[Dict[str, Any]],
    model: str,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    user_id: Optional[str] = None,
    client_ip: Optional[str] = None,
    request_id: Optional[str] = None,
    stream_processor: StreamProcessor = Depends(get_stream_processor),
):
    """
    Stream chat completion endpoint using dependency injection.
    
    This endpoint demonstrates how the StreamProcessor can be
    injected as a dependency for cleaner code.
    """
    # Get user and client IP if not provided
    if not user_id:
        try:
            current_user = await get_current_user(request)
            user_id = current_user.id if current_user else None
        except HTTPException:
            user_id = None

    if not client_ip:
        client_ip = get_client_ip(request)

    try:
        # Process streaming request using the injected service
        async def stream_generator():
            async for chunk in stream_processor.process_streaming_request(
                session_id=session_id,
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                user_id=user_id,
                client_ip=client_ip,
                request_id=request_id,
            ):
                yield chunk

        return stream_generator()

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Stream chat completion error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Configuration endpoint for streaming settings

@router.get("/config")
async def get_stream_config():
    """Get streaming configuration."""
    return {
        "streaming": {
            "enabled": settings.enable_streaming,
            "timeout_seconds": settings.streaming_timeout_seconds,
            "max_concurrent_streams": settings.max_concurrent_streams,
            "compression_enabled": settings.enable_stream_compression,
            "rate_limiting_enabled": settings.enable_stream_rate_limiting,
        },
        "version": "1.0.0",
    }


@router.put("/config")
async def update_stream_config(
    config: Dict[str, Any],
    db: Session = Depends(get_db),
):
    """Update streaming configuration."""
    # This would update the streaming configuration
    # For now, return a placeholder response
    return {
        "message": "Stream configuration updated",
        "config": config,
        "timestamp": int(time.time()),
    }