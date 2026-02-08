"""
Fly.io Chat Backend - Lightweight LLM Service

Provides always-on chat capabilities using small quantized models.
Designed to run on Fly.io's shared-cpu-2x (2GB RAM) instances.

Models:
- TinyLlama-1.1B (default) - fits in 2GB with int4 quantization
- Phi-2 (2.7B) - optional, needs 4GB
- SmolLM (135M-1.7B) - ultra-lightweight option

Fallback chain:
1. Local llama.cpp inference (TinyLlama int4)
2. OpenAI API (if configured)
3. Error response
"""

import os
import asyncio
import logging
import time
from pathlib import Path
from typing import Optional, AsyncGenerator, Dict, Any, List
from contextlib import asynccontextmanager
from dataclasses import dataclass

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import httpx

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Configuration
MODEL_ID = os.getenv("MODEL_ID", "TinyLlama/TinyLlama-1.1B-Chat-v1.0")
QUANTIZATION = os.getenv("QUANTIZATION", "int4")
MAX_CONTEXT = int(os.getenv("MAX_CONTEXT", "2048"))
MODEL_DIR = Path(os.getenv("MODEL_DIR", "/app/models"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GOBLIN_API_KEY = os.getenv("GOBLIN_API_KEY", "")


@dataclass
class InferenceStats:
    """Track inference statistics."""

    total_requests: int = 0
    total_tokens: int = 0
    avg_latency_ms: float = 0.0
    errors: int = 0
    local_requests: int = 0
    fallback_requests: int = 0


stats = InferenceStats()


# Optional llama-cpp-python for local inference
try:
    from llama_cpp import Llama

    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    logger.warning("llama-cpp-python not installed. Local inference disabled.")


class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role: system, user, or assistant")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., description="Chat messages")
    max_tokens: int = Field(256, ge=1, le=2048)
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    stream: bool = Field(False)
    model: Optional[str] = Field(None, description="Model override")


class ChatResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]


class HealthResponse(BaseModel):
    status: str
    model: str
    engine: str
    stats: Dict[str, Any]


# Global model instance
_llm: Optional["Llama"] = None


def get_model_path() -> Optional[Path]:
    """Get path to the quantized model file."""
    # Check for GGUF model
    gguf_patterns = [
        f"*{QUANTIZATION}*.gguf",
        "*.gguf",
        "*Q4_K_M.gguf",
        "model.gguf",
    ]

    for pattern in gguf_patterns:
        matches = list(MODEL_DIR.glob(pattern))
        if matches:
            return matches[0]

    return None


def load_model() -> Optional["Llama"]:
    """Load the local LLM model."""
    global _llm

    if not LLAMA_CPP_AVAILABLE:
        return None

    model_path = get_model_path()
    if not model_path or not model_path.exists():
        logger.warning(f"No model found in {MODEL_DIR}")
        return None

    try:
        logger.info(f"Loading model from {model_path}")
        _llm = Llama(
            model_path=str(model_path),
            n_ctx=MAX_CONTEXT,
            n_threads=2,  # Match Fly.io CPU count
            n_gpu_layers=0,  # CPU only on Fly.io
            verbose=False,
        )
        logger.info("Model loaded successfully")
        return _llm
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Goblin Chat Backend...")
    load_model()
    yield
    # Shutdown
    logger.info("Shutting down...")


app = FastAPI(
    title="Goblin Chat Backend",
    description="Lightweight LLM inference service for Fly.io",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def verify_api_key(authorization: Optional[str] = Header(None)) -> bool:
    """Verify API key if configured."""
    if not GOBLIN_API_KEY:
        return True  # No auth configured

    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    token = authorization.replace("Bearer ", "")
    if token != GOBLIN_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return True


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    engine = "llama-cpp" if _llm else "fallback-openai" if OPENAI_API_KEY else "none"
    return HealthResponse(
        status="healthy" if (_llm or OPENAI_API_KEY) else "degraded",
        model=MODEL_ID,
        engine=engine,
        stats={
            "total_requests": stats.total_requests,
            "total_tokens": stats.total_tokens,
            "avg_latency_ms": round(stats.avg_latency_ms, 2),
            "errors": stats.errors,
            "local_requests": stats.local_requests,
            "fallback_requests": stats.fallback_requests,
        },
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Goblin Chat Backend",
        "version": "1.0.0",
        "model": MODEL_ID,
        "endpoints": {
            "chat": "/v1/chat/completions",
            "health": "/health",
        },
    }


async def generate_local(
    messages: List[ChatMessage],
    max_tokens: int,
    temperature: float,
) -> Optional[str]:
    """Generate response using local llama.cpp model."""
    if not _llm:
        return None

    try:
        # Format messages for TinyLlama chat template
        prompt = format_chat_prompt(messages)

        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: _llm(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=["</s>", "<|user|>", "<|assistant|>"],
            ),
        )

        return response["choices"][0]["text"].strip()
    except Exception as e:
        logger.error(f"Local inference error: {e}")
        return None


def format_chat_prompt(messages: List[ChatMessage]) -> str:
    """Format messages for TinyLlama chat template."""
    prompt_parts = []

    for msg in messages:
        if msg.role == "system":
            prompt_parts.append(f"<|system|>\n{msg.content}</s>")
        elif msg.role == "user":
            prompt_parts.append(f"<|user|>\n{msg.content}</s>")
        elif msg.role == "assistant":
            prompt_parts.append(f"<|assistant|>\n{msg.content}</s>")

    # Add assistant prompt for generation
    prompt_parts.append("<|assistant|>\n")

    return "\n".join(prompt_parts)


async def generate_openai_fallback(
    messages: List[ChatMessage],
    max_tokens: int,
    temperature: float,
) -> Optional[str]:
    """Fallback to OpenAI API."""
    if not OPENAI_API_KEY:
        return None

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {"role": m.role, "content": m.content} for m in messages
                    ],
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"OpenAI fallback error: {e}")
        return None


@app.post("/v1/chat/completions", response_model=ChatResponse)
async def chat_completion(
    request: ChatRequest,
    _: bool = Depends(verify_api_key),
):
    """OpenAI-compatible chat completion endpoint."""
    start_time = time.time()
    stats.total_requests += 1

    # Try local inference first
    content = await generate_local(
        request.messages,
        request.max_tokens,
        request.temperature,
    )

    if content:
        stats.local_requests += 1
    else:
        # Fallback to OpenAI
        content = await generate_openai_fallback(
            request.messages,
            request.max_tokens,
            request.temperature,
        )
        if content:
            stats.fallback_requests += 1

    if not content:
        stats.errors += 1
        raise HTTPException(status_code=503, detail="No inference backend available")

    # Update stats
    latency_ms = (time.time() - start_time) * 1000
    stats.avg_latency_ms = (
        stats.avg_latency_ms * (stats.total_requests - 1) + latency_ms
    ) / stats.total_requests

    # Estimate token count
    tokens = len(content.split()) + sum(
        len(m.content.split()) for m in request.messages
    )
    stats.total_tokens += tokens

    return ChatResponse(
        id=f"chatcmpl-{int(time.time())}",
        created=int(time.time()),
        model=request.model or MODEL_ID,
        choices=[
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content,
                },
                "finish_reason": "stop",
            }
        ],
        usage={
            "prompt_tokens": sum(len(m.content.split()) for m in request.messages),
            "completion_tokens": len(content.split()),
            "total_tokens": tokens,
        },
    )


@app.get("/v1/models")
async def list_models():
    """List available models."""
    return {
        "object": "list",
        "data": [
            {
                "id": MODEL_ID,
                "object": "model",
                "owned_by": "goblin",
                "permission": [],
            }
        ],
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
