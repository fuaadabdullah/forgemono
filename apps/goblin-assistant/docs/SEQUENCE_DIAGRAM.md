---
description: "Sequence diagram for request routing in GoblinOS Assistant"
---

# Request Routing Sequence

This diagram shows the simplified request routing sequence from the user to the local LLM and back.

```mermaid
sequenceDiagram
  participant Client
  participant Frontend
  participant API
  participant Router as LocalLLMRouting
  participant Ollama

  Client->>Frontend: Send chat message
  Frontend->>API: POST /chat
  API->>Router: Route request (select model based on characteristics)
  Router->>Ollama: Invoke local model
  Ollama-->>API: Response
  API-->>Frontend: Return message
  Frontend-->>Client: Render response
```

Notes:

- This shows the current simplified architecture with local LLM routing only.
- No cloud providers, RAG, or complex verification are currently implemented.
- The routing service selects between local models (mistral, qwen2.5, phi3, gemma) based on request characteristics.

