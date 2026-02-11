#!/usr/bin/env python3
"""
Mock Llama.cpp Server for testing
Provides basic OpenAI-compatible API endpoints
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
import time

app = FastAPI(title="Mock Llama.cpp Server", version="1.0.0")

# CORS middleware
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
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 100
    stream: Optional[bool] = False


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "server": "mock-llama-cpp"}


@app.get("/v1/models")
async def list_models():
    """List available models"""
    return {
        "object": "list",
        "data": [
            {
                "id": "mock-model",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "mock-provider",
            }
        ],
    }


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """Chat completions endpoint"""
    # Simple mock response
    user_message = ""
    for msg in request.messages:
        if msg.role == "user":
            user_message = msg.content
            break

    mock_response = f"This is a mock response to: '{user_message}'. The goblin-llamacpp-server is working!"

    return ChatCompletionResponse(
        id=f"chatcmpl-{int(time.time())}",
        created=int(time.time()),
        model=request.model,
        choices=[
            {
                "index": 0,
                "message": {"role": "assistant", "content": mock_response},
                "finish_reason": "stop",
            }
        ],
        usage={
            "prompt_tokens": len(user_message.split()),
            "completion_tokens": len(mock_response.split()),
            "total_tokens": len(user_message.split()) + len(mock_response.split()),
        },
    )


@app.get("/props")
async def props():
    """Server properties"""
    return {"model": {"path": "/mock/model.gguf"}, "cpu": {"threads": 4}}


if __name__ == "__main__":
    print("Starting Mock Llama.cpp Server on port 8080...")
    uvicorn.run(app, host="0.0.0.0", port=8080)
