---
description: "Core Identity and positioning for GoblinOS Assistant — a local LLM assistant"
---

# GoblinOS Assistant — Core Identity

GoblinOS Assistant is a local LLM assistant platform focused on simplicity, privacy, and cost-efficiency. It's designed to provide AI capabilities through locally hosted models without the complexity of multi-provider orchestration.

## 1. What GoblinOS Provides

- **Local AI Processing** — Run AI models entirely on local hardware for maximum privacy and control.

- **Multiple Model Support** — Choose from different local models optimized for various tasks (chat, coding, long context).

- **Simple Architecture** — Straightforward setup without complex cloud integrations or external dependencies.

- **Cost Control** — No API fees or usage charges since all processing happens locally.

## 2. Key Characteristics

### 2.1 Local-First Design

GoblinOS focuses exclusively on local model execution:

- **Local Models**: mistral:7b, qwen2.5:3b, phi3:3.8b, gemma:2b via Ollama
- **No Cloud Dependencies**: All processing happens locally, ensuring data privacy
- **Simple Routing**: Automatic model selection based on request characteristics (context length, intent, latency requirements)

### 2.2 Privacy-First Approach

GoblinOS is designed for users who want complete data control:

- **Local Data Processing**: All prompts and responses stay on local hardware
- **No External APIs**: No data leaves your system
- **Self-Hosted**: Complete control over the deployment environment

### 2.3 Developer-Friendly

- **Simple Setup**: Easy installation and configuration
- **React/Vite Frontend**: Modern web interface
- **FastAPI Backend**: Clean API design
- **SQLite/PostgreSQL**: Flexible database options

## 3. Current Implementation

At its core, GoblinOS Assistant is structured as:

- **Frontend**: React + Vite UI for user interaction
- **Backend**: FastAPI server handling requests and routing
- **Local LLM**: Ollama-powered models with intelligent routing
- **Database**: SQLite or PostgreSQL for data persistence

Key features:
- Local LLM routing based on request characteristics
- Basic database support for user data
- Simple web interface for chat interactions
- Raptor service for local model management

## 4. Current Capabilities

- **Chat Interface**: Basic conversational AI through local models
- **Model Routing**: Automatic selection between different local models
- **Database Integration**: User data storage and management
- **Local Model Management**: Start/stop/status monitoring of local LLMs

## 5. Target Users

- **Developers** who want to experiment with local LLMs
- **Privacy-Conscious Users** who prefer local processing
- **Small Teams** looking for simple AI assistant capabilities
- **Hobbyists** exploring local AI without cloud dependencies

## 6. Deployment Modes

- **Local Development**: Run entirely on local machine
- **Self-Hosted**: Deploy to personal servers or VPS
- **Single-User**: Designed for individual or small team use

## 7. Slogan & Short Pitches

Tagline:
> GoblinOS Assistant: Simple, private AI powered by local models.

Short pitch:
> GoblinOS Assistant is a straightforward local LLM platform that brings AI capabilities to your desktop without cloud dependencies. Choose from multiple local models optimized for different tasks, all while keeping your data completely private.

## 8. Current Status & Future Plans

### What's Implemented ✅
- Local LLM routing with multiple models
- Basic web interface
- Database support
- Model management service

### What's Not Yet Implemented ❌
- Multi-provider orchestration (OpenAI, Anthropic, etc.)
- RAG/vector database functionality
- Enterprise features (multi-tenancy, API key management)
- Advanced monitoring and observability
- Code execution sandbox
- Web search integration
- Voice/TTS support

## 9. Next Steps & Where to Learn More

- See `ARCHITECTURE_OVERVIEW.md` for the current simplified architecture.

- See `LOCAL_LLM_ROUTING.md` for details on model selection and routing logic.

- The system is currently in a basic implementation phase and can be extended with additional features as needed.

---
