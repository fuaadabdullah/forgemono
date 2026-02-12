---
description: "Architecture overview for GoblinOS Assistant - a local LLM assistant"
---

# Architecture Overview — GoblinOS Assistant

This document provides a concise architecture diagram and request/response process flow for the GoblinOS Assistant.

> See `CORE_IDENTITY.md` for product-level messaging, core characteristics, and a short pitch describing GoblinOS Assistant's purpose and differentiators.

## Mermaid Diagram

```mermaid
graph LR
  subgraph Frontend
    U[User/Client] --> |HTTP| FE(React + Vite UI)
  end

  subgraph Backend
    FE --> API[FastAPI (backend/main.py)]
    API --> ROUTE[Routing Service (local_llm_routing.py)]
    ROUTE --> OLLAMA[Ollama (local LLM)]
    API --> DB[SQLite/PostgreSQL (database.py)]
    API --> RAPTOR[Raptor Service (raptor.ts)]
  end

  DB --> |persistence| API
```


## Request Flow (Quick)

1. User sends a chat message from the frontend.
2. Frontend sends the request to the FastAPI backend.
3. Routing service selects the appropriate local LLM model based on request characteristics.
4. The selected model (via Ollama) processes the request and returns a response.
5. The response is returned to the client.

## Key files & locations

- `backend/main.py` — FastAPI app, middleware & router wiring
- `backend/local_llm_routing.py` — Local LLM routing logic
- `backend/database.py` — Database configuration and models
- `src/` — Frontend code (React + Vite + TypeScript)
- `src/services/raptor.ts` — Raptor service for local LLM management

## Notes

- This is a simplified local LLM assistant architecture.
- The system currently supports routing between different local models (mistral, qwen2.5, phi3, gemma).
- No cloud providers or external APIs are currently integrated.
- No RAG, vector database, or advanced AI features are implemented.

## Current Implementation Status

- ✅ Local LLM routing with multiple models
- ✅ Basic database support (SQLite/PostgreSQL)
- ✅ Frontend UI with React/Vite
- ❌ Multi-provider orchestration (OpenAI, Anthropic, etc.)
- ❌ RAG/vector database functionality
- ❌ Enterprise features (multi-tenancy, API key management)
- ❌ Advanced monitoring and observability
- ❌ Code execution sandbox
- ❌ Web search integration
- ❌ Voice/TTS support


---
