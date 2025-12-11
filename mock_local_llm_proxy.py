#!/usr/bin/env python3
"""
Mock Local LLM Proxy for testing backend integration
without requiring actual LLM models or disk space.
"""

import json
import os
import time
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Mock Local LLM Proxy", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    temperature: float = 0.7
    max_tokens: int = 100


class ChatCompletionResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: list
    usage: dict


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "mock-local-llm-proxy"}


# NOTE: Do not cache the API key at import time; read it dynamically so tests
# or runtime env var changes are respected without reloading the module.


def _is_authenticated(req: Request) -> bool:
    """Check Authorization header (Bearer) or X-API-Key header.

    Behavior:
    - If LOCAL_LLM_API_KEY is empty, treat proxy as "dev mode" and accept all requests.
    - Otherwise, accept only matching Authorization Bearer or X-API-Key values.
    """
    key = os.getenv("LOCAL_LLM_API_KEY", "")
    if not key:
        return True

    auth_header = req.headers.get("authorization", "")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "", 1).strip()
        if token == key:
            return True

    x_api_key = req.headers.get("x-api-key") or req.headers.get("X-API-Key")
    if x_api_key and x_api_key == key:
        return True

    return False


@app.get("/v1/models")
async def list_models():
    """List available models"""
    return {
        "object": "list",
        "data": [
            {
                "id": "llama2:7b",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "ollama",
            },
            {
                "id": "mistral:7b",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "ollama",
            },
        ],
    }


@app.get("/api/status")
async def api_status(req: Request):
    """Native Ollama-like status endpoint"""
    if not _is_authenticated(req):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return {"status": "ok", "name": "mock-local-llm-proxy", "uptime": 123}


@app.get("/api/tags")
async def api_tags(req: Request):
    """Return models in Ollama native format (key: models)
    This helps OllamaAdapter.list_models detect native responses.
    """
    if not _is_authenticated(req):
        raise HTTPException(status_code=401, detail="Invalid API key")

    return {
        "models": [
            {"name": "llama2:7b", "context_length": 4096},
            {"name": "mistral:7b", "context_length": 8192},
        ]
    }


@app.post("/api/generate")
async def api_generate(request: Request):
    """Native Ollama-style generate endpoint.

    Returns streaming-like text where the last non-empty line is a JSON object
    (this matches how the Ollama adapter parses /api/generate output).
    """
    if not _is_authenticated(request):
        raise HTTPException(status_code=401, detail="Invalid API key")

    body = await request.json()
    prompt = body.get("prompt", "")
    model = body.get("model", "llama2:7b")

    # Build a mock JSON payload as the last line in a text stream
    mock_response = {
        "response": f"(Ollama) Mock generated text for model {model}: {prompt[:200]}"
    }

    # Simulate a streaming text where the final line is the JSON we want
    text = """
    # streaming debug
    {json_line}
    """.strip().format(json_line=json.dumps(mock_response))

    return Response(content=text, media_type="text/plain")


@app.post("/v1/chat/completions")
async def chat_completion(request: ChatCompletionRequest, req: Request):
    """Mock chat completion endpoint"""
    # Check API key
    if not _is_authenticated(req):
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Get the last user message
    user_messages = [msg for msg in request.messages if msg.role == "user"]
    if not user_messages:
        raise HTTPException(status_code=400, detail="No user message found")

    user_content = user_messages[-1].content

    # Generate mock response based on input
    if "hello" in user_content.lower():
        mock_response = "Hello! I'm a mock local LLM running on your development machine. This response is generated to test the backend integration."
    elif "test" in user_content.lower():
        mock_response = "Test successful! The local LLM proxy is working correctly. This confirms that the routing system can successfully connect to local models."
    else:
        mock_response = f"I received your message: '{user_content}'. This is a mock response from the local LLM proxy. In production, this would be generated by Ollama or llama.cpp running on your Kamatera server."

    return {
        "id": f"chatcmpl-mock-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": mock_response},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": len(user_content.split()),
            "completion_tokens": len(mock_response.split()),
            "total_tokens": len(user_content.split()) + len(mock_response.split()),
        },
    }


@app.post("/v1/generate")
async def v1_generate(request: Request):
    """Raptor / v1/generate endpoint compatibility for inference_clients.fallback.

    Accepts payload {"prompt": "...", "max_tokens": 50} and returns
    JSON structure matching Raptor: {"ok": true, "result": {"response": "..."}}
    """
    if not _is_authenticated(request):
        raise HTTPException(status_code=401, detail="Invalid API key")

    payload = await request.json()
    prompt = payload.get("prompt", "")
    model = payload.get("model", "llama2:7b")
    mock_text = f"(Raptor) Mock text for model {model}: {prompt[:200]}"
    return {"ok": True, "result": {"response": mock_text}}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Mock Local LLM Proxy",
        "version": "1.0.0",
        "endpoints": [
            "GET /health",
            "GET /api/status",
            "GET /v1/models",
            "GET /api/tags",
            "POST /api/generate",
            "POST /v1/generate",
            "POST /v1/chat/completions",
        ],
        "note": "This is a mock service for testing backend integration without requiring actual LLM models",
    }


if __name__ == "__main__":
    print("🚀 Starting Mock Local LLM Proxy on http://localhost:8002")
    print("📋 Test endpoints:")
    print("  curl http://localhost:8002/health")
    print("  curl http://localhost:8002/v1/models")
    print("  curl -X POST http://localhost:8002/v1/chat/completions \\")
    print("       -H 'Content-Type: application/json' \\")
    print("       -H 'Authorization: Bearer <LOCAL_LLM_API_KEY>' \\")
    print(
        '       -d \'{"model":"llama2:7b","messages":[{"role":"user","content":"Hello!"}]}\''
    )
    print("")

    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")
