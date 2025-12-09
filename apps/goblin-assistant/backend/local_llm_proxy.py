#!/usr/bin/env python3
"""
Local LLM Proxy Service
FastAPI proxy that enforces x-api-key authentication and routes requests
to local Ollama and llama.cpp servers on Kamatera VPS.

This runs as a separate service from the main Goblin Assistant backend,
providing secure access to local LLMs with API key validation.
"""

import os
import httpx
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

# Add RAG service import
try:
    from services.rag_service import RAGService

    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    logging.warning(
        "RAG service not available - install chromadb and sentence-transformers"
    )

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Local LLM Proxy", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
# Read API key (empty string disables auth for local dev/testing)
API_KEY = os.getenv("LOCAL_LLM_API_KEY", "")
# Allow overriding base URLs
OLLAMA_URL = os.getenv(
    "OLLAMA_BASE_URL", os.getenv("LOCAL_LLM_PROXY_OLLAMA_URL", "http://localhost:11434")
)
LLAMACPP_URL = os.getenv("LLAMACPP_URL", "http://localhost:8080")

# HTTP client with timeout
client = httpx.AsyncClient(timeout=300.0)  # 5 minute timeout for LLM requests


class ChatRequest(BaseModel):
    model: str
    messages: list
    stream: Optional[bool] = False
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


def _is_authorized(request: Request) -> bool:
    """Return True if request contains the valid API key header or bearer token.

    Behavior:
    - If API_KEY is empty, treat service as dev mode and accept all requests.
    - Otherwise, accept either 'x-api-key' header or 'Authorization: Bearer <token>'.
    """
    if not API_KEY:
        return True
    # check x-api-key
    x_key = request.headers.get("x-api-key") or request.headers.get("X-API-Key")
    if x_key and x_key == API_KEY:
        return True
    # check bearer token
    auth = request.headers.get("authorization", "")
    if auth and auth.startswith("Bearer "):
        token = auth.replace("Bearer ", "", 1).strip()
        if token == API_KEY:
            return True
    return False


def require_auth(request: Request) -> None:
    if not _is_authorized(request):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests"""
    logger.info(f"{request.method} {request.url}")
    response = await call_next(request)
    return response


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "local-llm-proxy"}


@app.get("/models")
async def list_models(request: Request):
    """List available models from both Ollama and llama.cpp (legacy endpoint)."""
    require_auth(request)

    models = {"ollama": [], "llamacpp": []}

    try:
        # Get Ollama models
        ollama_response = await client.get(f"{OLLAMA_URL}/api/tags")
        if ollama_response.status_code == 200:
            ollama_data = ollama_response.json()
            models["ollama"] = [
                model["name"] for model in ollama_data.get("models", [])
            ]
    except Exception as e:
        logger.error(f"Ollama models error: {e}")

    try:
        # llama.cpp doesn't have a standard models endpoint, so we'll return configured models
        models["llamacpp"] = ["active-model"]  # Update based on your active model
    except Exception as e:
        logger.error(f"llama.cpp models error: {e}")

    return {"models": models}


@app.get("/api/status")
async def api_status(request: Request):
    """Native API status endpoint for Ollama compatibility"""
    # no auth required for basic status
    return {"status": "ok", "name": "local-llm-proxy", "uptime": 0}


@app.get("/api/tags")
async def api_tags(request: Request):
    """Ollama tags endpoint to list models in native format"""
    require_auth(request)
    models = []
    try:
        ollama_response = await client.get(f"{OLLAMA_URL}/api/tags")
        if ollama_response.status_code == 200:
            ollama_data = ollama_response.json()
            models = ollama_data.get("models", [])
    except Exception as e:
        logger.error(f"api_tags failed: {e}")
    return {"models": models}


@app.get("/v1/models")
async def openai_list_models(request: Request):
    """OpenAI-compatible list models endpoint.

    Produces a JSON response with `object: list` and `data: [ {id, object, ...} ]`.
    """
    require_auth(request)
    # Reuse existing discovery and map to OpenAI-like response
    models = {"ollama": [], "llamacpp": []}
    try:
        ollama_response = await client.get(f"{OLLAMA_URL}/api/tags")
        if ollama_response.status_code == 200:
            ollama_data = ollama_response.json()
            models["ollama"] = [m["name"] for m in ollama_data.get("models", [])]
    except Exception:
        pass

    # Build OpenAI-like list
    data = []
    for m in models.get("ollama", []):
        data.append({"id": m, "object": "model", "created": None, "owned_by": "ollama"})
    for m in models.get("llamacpp", []):
        data.append(
            {"id": m, "object": "model", "created": None, "owned_by": "llamacpp"}
        )

    return {"object": "list", "data": data}


@app.post("/api/chat")
async def ollama_chat(request: Request):
    """Direct proxy to Ollama /api/chat endpoint (native)."""
    require_auth(request)

    try:
        body = await request.json()

        # Forward to Ollama
        headers = {"Content-Type": "application/json"}
        response = await client.post(
            f"{OLLAMA_URL}/api/chat", json=body, headers=headers
        )

        if response.status_code != 200:
            logger.error(f"Ollama chat failed: {response.status_code} {response.text}")
            raise HTTPException(
                status_code=response.status_code, detail="Ollama chat failed"
            )

        return Response(
            content=response.content, media_type=response.headers.get("content-type")
        )

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Ollama request timeout")
    except Exception as e:
        logger.error(f"Ollama chat error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/chat/completions")
async def chat_completions(request: Request):
    """Route chat completions to appropriate local LLM with fallback support"""
    require_auth(request)

    try:
        body = await request.json()
        model = body.get("model", "").lower()

        # Check for fallback mode
        is_fallback = body.get("fallback_mode", False)
        cheap_fallback_model = "goblin-simple-llama-1b"

        # If fallback mode requested, use cheap model
        if is_fallback or model == cheap_fallback_model:
            logger.info(
                f"Using cheap fallback model for request (fallback_mode: {is_fallback})"
            )
            # Override model to cheap fallback
            body["model"] = cheap_fallback_model
            model = cheap_fallback_model

            # Reduce parameters for faster response
            body["max_tokens"] = min(body.get("max_tokens", 512), 256)
            body["temperature"] = max(
                body.get("temperature", 0.7), 0.8
            )  # Slightly more random for variety

            # Add fallback notice to system message
            messages = body.get("messages", [])
            if messages and messages[0].get("role") == "system":
                messages[0]["content"] = (
                    "You are a basic AI assistant in fallback mode. Keep responses brief. "
                    + messages[0]["content"]
                )
            else:
                messages.insert(
                    0,
                    {
                        "role": "system",
                        "content": "You are a basic AI assistant in fallback mode due to high load. Keep responses brief and to the point.",
                    },
                )
            body["messages"] = messages

        # Route based on model name
        if any(
            keyword in model
            for keyword in ["phi3", "gemma", "qwen", "deepseek", cheap_fallback_model]
        ):
            # Ollama models (prefer OpenAI-compatible endpoint if available)
            # Try the OpenAI-compatible v1/chat/completions first, fall back to /api/chat
            target_url = f"{OLLAMA_URL}/v1/chat/completions"
        elif any(keyword in model for keyword in ["llama", "gguf", "active"]):
            # llama.cpp models - convert to llama.cpp format
            target_url = f"{LLAMACPP_URL}/completion"
            # Convert OpenAI format to llama.cpp format
            body = convert_openai_to_llamacpp(body)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown model: {model}")

        # Forward the request
        headers = {"Content-Type": "application/json"}
        # Include Auth if present
        if API_KEY:
            headers["x-api-key"] = API_KEY
        response = await client.post(target_url, json=body, headers=headers)

        if response.status_code != 200:
            logger.error(f"LLM request failed: {response.status_code} {response.text}")
            raise HTTPException(
                status_code=response.status_code, detail="LLM request failed"
            )

        return Response(
            content=response.content, media_type=response.headers.get("content-type")
        )

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="LLM request timeout")
    except Exception as e:
        logger.error(f"Chat completion error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


def convert_openai_to_llamacpp(openai_body: Dict[str, Any]) -> Dict[str, Any]:
    """Convert OpenAI chat format to llama.cpp completion format"""
    messages = openai_body.get("messages", [])
    if not messages:
        raise HTTPException(status_code=400, detail="No messages provided")

    # Extract the last user message as prompt
    prompt = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            prompt = msg.get("content", "")
            break

    if not prompt:
        raise HTTPException(status_code=400, detail="No user message found")

    # Build llama.cpp format
    llamacpp_body = {
        "prompt": prompt,
        "n_predict": openai_body.get("max_tokens", 512),
        "temperature": openai_body.get("temperature", 0.7),
        "stop": ["\n\n", "###"],  # Common stop sequences
        "stream": openai_body.get("stream", False),
    }

    return llamacpp_body


@app.post("/api/generate")
async def api_generate(request: Request):
    """Native Ollama generate endpoint that may return streaming/cumulative output.

    We'll call the Ollama `/api/generate` endpoint directly and forward the result.
    """
    require_auth(request)
    body = await request.json()

    try:
        response = await client.post(
            f"{OLLAMA_URL}/api/generate",
            json=body,
            headers={"Content-Type": "application/json"},
        )
        return Response(
            content=response.content, media_type=response.headers.get("content-type")
        )
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Ollama generate timed out")
    except Exception as e:
        logger.error(f"api_generate error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/v1/generate")
async def v1_generate(request: Request):
    """Raptor (Raptor Mini) compatible /v1/generate endpoint.
    Returns `{ok: True, result: {response: ...}}` format.
    """
    require_auth(request)
    body = await request.json()
    # Try to call raptor endpoint directly (assumed to expose /v1/generate)
    try:
        response = await client.post(
            f"{LLAMACPP_URL}/v1/generate",
            json=body,
            headers={"Content-Type": "application/json"},
        )
        return Response(
            content=response.content, media_type=response.headers.get("content-type")
        )
    except Exception:
        # Fallback: return an emulated response if the raptor service is not available
        prompt = body.get("prompt", "")
        mock_text = f"(Local Raptor) Mock response for prompt: {prompt[:200]}"
        return {"ok": True, "result": {"response": mock_text}}


@app.post("/v1/chat/completions")
async def openai_chat_completions(request: Request):
    """OpenAI-compatible chat completions endpoint — forwards to Ollama or llama.cpp depending on model.
    This is a convenience wrapper for clients using OpenAI-compatible API shape.
    """
    require_auth(request)
    body = await request.json()
    # Reuse chat_completions logic by forwarding the request internally to /chat/completions
    # We simply re-POST the OpenAI-style body to our existing endpoint which does routing
    model = body.get("model", "").lower()
    # Determine where to forward
    if any(keyword in model for keyword in ["phi3", "gemma", "qwen", "deepseek"]):
        target = f"{OLLAMA_URL}/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        if API_KEY:
            headers["x-api-key"] = API_KEY
        response = await client.post(target, json=body, headers=headers)
        return Response(
            content=response.content, media_type=response.headers.get("content-type")
        )
    elif any(keyword in model for keyword in ["llama", "gguf", "active"]):
        # Convert to llama.cpp format and call the local llama.cpp endpoint
        llamabody = convert_openai_to_llamacpp(body)
        target = f"{LLAMACPP_URL}/completion"
        response = await client.post(
            target, json=llamabody, headers={"Content-Type": "application/json"}
        )
        return Response(
            content=response.content, media_type=response.headers.get("content-type")
        )
    else:
        # default to Ollama for unknown models
        target = f"{OLLAMA_URL}/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        if API_KEY:
            headers["x-api-key"] = API_KEY
        response = await client.post(target, json=body, headers=headers)
        return Response(
            content=response.content, media_type=response.headers.get("content-type")
        )


# RAG Endpoints
class DocumentRequest(BaseModel):
    content: str
    id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    collection: Optional[str] = "documents"


class RAGQueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    top_k: Optional[int] = 10
    filters: Optional[Dict[str, Any]] = None
    collection: Optional[str] = "documents"


@app.post("/rag/documents")
async def add_documents(request: Request, doc_request: DocumentRequest):
    """Add documents to the RAG vector database."""
    require_auth(request)

    if not RAG_AVAILABLE:
        raise HTTPException(status_code=503, detail="RAG service not available")

    try:
        rag_service = RAGService()
        documents = [
            {
                "content": doc_request.content,
                "id": doc_request.id,
                "metadata": doc_request.metadata or {},
            }
        ]

        success = await rag_service.add_documents(documents, doc_request.collection)

        if success:
            return {
                "status": "success",
                "message": f"Added document to {doc_request.collection}",
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to add document")

    except Exception as e:
        logger.error(f"RAG document addition failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/rag/query")
async def rag_query(request: Request, query_request: RAGQueryRequest):
    """Perform RAG query with dense retrieval and context generation."""
    require_auth(request)

    if not RAG_AVAILABLE:
        raise HTTPException(status_code=503, detail="RAG service not available")

    try:
        rag_service = RAGService()

        # Run complete RAG pipeline
        result = await rag_service.rag_pipeline(
            query=query_request.query,
            session_id=query_request.session_id,
            filters=query_request.filters,
        )

        return result

    except Exception as e:
        logger.error(f"RAG query failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/rag/health")
async def rag_health(request: Request):
    """Check RAG service health."""
    require_auth(request)

    if not RAG_AVAILABLE:
        return {"status": "unavailable", "message": "RAG dependencies not installed"}

    try:
        rag_service = RAGService()
        # Simple health check - try to get collection count
        collections = rag_service.chroma_client.list_collections()
        return {"status": "healthy", "collections": len(collections), "service": "rag"}
    except Exception as e:
        logger.error(f"RAG health check failed: {e}")
        return {"status": "error", "message": str(e)}


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await client.aclose()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")
