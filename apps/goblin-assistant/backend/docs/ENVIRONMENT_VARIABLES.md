# Environment Variables Documentation

This document provides comprehensive documentation for all environment variables used in the Goblin Assistant backend application.

## Table of Contents

- [Core Application](#core-application)
- [Database Configuration](#database-configuration)
- [LLM Providers](#llm-providers)
- [Authentication & Security](#authentication--security)
- [Logging & Monitoring](#logging--monitoring)
- [CORS & Networking](#cors--networking)
- [Feature Flags](#feature-flags)
- [External Services](#external-services)

## Core Application

### LOG_LEVEL

- **Type**: String
- **Default**: `INFO`
- **Required**: No
- **Description**: Sets the logging level for the application
- **Valid Values**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **Example**: `LOG_LEVEL=DEBUG`

### SKIP_RAPTOR_INIT

- **Type**: Boolean (0/1)
- **Default**: `0` (false)
- **Required**: No
- **Description**: Skip Raptor initialization during startup
- **Example**: `SKIP_RAPTOR_INIT=1`

### SKIP_PROBE_INIT

- **Type**: Boolean (0/1)
- **Default**: `0` (false)
- **Required**: No
- **Description**: Skip provider probe initialization during startup
- **Example**: `SKIP_PROBE_INIT=1`

## Database Configuration

### DATABASE_URL

- **Type**: String
- **Default**: None
- **Required**: Yes (if not using SUPABASE_URL)
- **Description**: PostgreSQL database connection URL
- **Example**: `DATABASE_URL=postgresql://user:password@localhost:5432/goblin_assistant`

### SUPABASE_URL

- **Type**: String
- **Default**: None
- **Required**: Yes (if not using DATABASE_URL)
- **Description**: Supabase database connection URL
- **Example**: `SUPABASE_URL=<https://your-project.supabase.co`>

## LLM Providers

### KAMATERA_LLM_API_KEY

- **Type**: String
- **Default**: None
- **Required**: No (but recommended for production)
- **Description**: API key for Kamatera-hosted LLM service
- **Example**: `KAMATERA_LLM_API_KEY=your-api-key-here`

### KAMATERA_LLM_URL

- **Type**: String
- **Default**: `<http://66.55.77.147:8000`>
- **Required**: No
- **Description**: Base URL for Kamatera-hosted LLM service
- **Example**: `KAMATERA_LLM_URL=<http://66.55.77.147:8000`>

### LOCAL_LLM_API_KEY

- **Type**: String
- **Default**: Empty string
- **Required**: No
- **Description**: API key for local LLM proxy service
- **Example**: `LOCAL_LLM_API_KEY=your-local-api-key`

### LOCAL_LLM_PROXY_URL

- **Type**: String
- **Default**: `<http://45.61.60.3:8002`>
- **Required**: No
- **Description**: Base URL for local LLM proxy service
- **Example**: `LOCAL_LLM_PROXY_URL=<http://localhost:8002`>

### OLLAMA_BASE_URL

- **Type**: String
- **Default**: `<http://localhost:11434`>
- **Required**: No
- **Description**: Base URL for Ollama service
- **Example**: `OLLAMA_BASE_URL=<http://localhost:11434`>

### OLLAMA_API_KEY

- **Type**: String
- **Default**: None
- **Required**: No
- **Description**: API key for Ollama service
- **Example**: `OLLAMA_API_KEY=your-ollama-key`

### USE_LOCAL_LLM

- **Type**: Boolean (true/false)
- **Default**: `false`
- **Required**: No
- **Description**: Whether to use local LLM instead of Kamatera-hosted service
- **Example**: `USE_LOCAL_LLM=true`

### OPENAI_API_KEY

- **Type**: String
- **Default**: None
- **Required**: No
- **Description**: API key for OpenAI services
- **Example**: `OPENAI_API_KEY=sk-your-openai-key`

### OPENAI_BASE_URL

- **Type**: String
- **Default**: `<https://api.openai.com`>
- **Required**: No
- **Description**: Base URL for OpenAI API
- **Example**: `OPENAI_BASE_URL=<https://api.openai.com`>

### ANTHROPIC_API_KEY

- **Type**: String
- **Default**: None
- **Required**: No
- **Description**: API key for Anthropic services
- **Example**: `ANTHROPIC_API_KEY=sk-ant-your-anthropic-key`

### ANTHROPIC_BASE_URL

- **Type**: String
- **Default**: `<https://api.anthropic.com`>
- **Required**: No
- **Description**: Base URL for Anthropic API
- **Example**: `ANTHROPIC_BASE_URL=<https://api.anthropic.com`>

### GROQ_API_KEY

- **Type**: String
- **Default**: None
- **Required**: No
- **Description**: API key for Groq services
- **Example**: `GROQ_API_KEY=gsk-your-groq-key`

### GROQ_BASE_URL

- **Type**: String
- **Default**: `<https://api.groq.com`>
- **Required**: No
- **Description**: Base URL for Groq API
- **Example**: `GROQ_BASE_URL=<https://api.groq.com`>

### DEEPSEEK_API_KEY

- **Type**: String
- **Default**: None
- **Required**: No
- **Description**: API key for DeepSeek services
- **Example**: `DEEPSEEK_API_KEY=sk-deepseek-your-key`

### DEEPSEEK_BASE_URL

- **Type**: String
- **Default**: `<https://api.deepseek.ai`>
- **Required**: No
- **Description**: Base URL for DeepSeek API
- **Example**: `DEEPSEEK_BASE_URL=<https://api.deepseek.ai`>

### GEMINI_API_KEY

- **Type**: String
- **Default**: None
- **Required**: No
- **Description**: API key for Google Gemini services
- **Example**: `GEMINI_API_KEY=your-gemini-key`

### GEMINI_BASE_URL

- **Type**: String
- **Default**: `<https://generative.googleapis.com`>
- **Required**: No
- **Description**: Base URL for Google Gemini API
- **Example**: `GEMINI_BASE_URL=<https://generative.googleapis.com`>

### GROK_API_KEY

- **Type**: String
- **Default**: None
- **Required**: No
- **Description**: API key for Grok (xAI) services
- **Example**: `GROK_API_KEY=xai-your-grok-key`

## Authentication & Security

### ROUTING_ENCRYPTION_KEY

- **Type**: String
- **Default**: None
- **Required**: Yes
- **Description**: Encryption key for routing service data
- **Example**: `ROUTING_ENCRYPTION_KEY=your-32-char-encryption-key`

### SECRET_KEY

- **Type**: String
- **Default**: None
- **Required**: No
- **Description**: Secret key for JWT tokens and other cryptographic operations
- **Example**: `SECRET_KEY=your-secret-key-here`

## Logging & Monitoring

### DATADOG_API_KEY

- **Type**: String
- **Default**: None
- **Required**: No
- **Description**: API key for Datadog monitoring
- **Example**: `DATADOG_API_KEY=your-datadog-key`

### DATADOG_APP_KEY

- **Type**: String
- **Default**: None
- **Required**: No
- **Description**: Application key for Datadog monitoring
- **Example**: `DATADOG_APP_KEY=your-datadog-app-key`

### REDIS_URL

- **Type**: String
- **Default**: `redis://localhost:6379/0`
- **Required**: No
- **Description**: Redis connection URL for caching and rate limiting
- **Example**: `REDIS_URL=redis://localhost:6379/0`

## CORS & Networking

### CORS_ORIGINS

- **Type**: String (comma-separated)
- **Default**: `*`
- **Required**: No
- **Description**: Allowed CORS origins for the API
- **Example**: `CORS_ORIGINS=<https://goblin.fuaad.ai,https://localhost:3000`>

### HOST

- **Type**: String
- **Default**: `0.0.0.0`
- **Required**: No
- **Description**: Host address to bind the server to
- **Example**: `HOST=0.0.0.0`

### PORT

- **Type**: Integer
- **Default**: `8000`
- **Required**: No
- **Description**: Port number to bind the server to
- **Example**: `PORT=8000`

## Feature Flags

### OLLAMA_ENABLED

- **Type**: Boolean (0/false/no or 1/true/yes)
- **Default**: Based on API key presence
- **Required**: No
- **Description**: Enable/disable Ollama provider
- **Example**: `OLLAMA_ENABLED=true`

### ANTHROPIC_ENABLED

- **Type**: Boolean (0/false/no or 1/true/yes)
- **Default**: Based on API key presence
- **Required**: No
- **Description**: Enable/disable Anthropic provider
- **Example**: `ANTHROPIC_ENABLED=false`

### OPENAI_ENABLED

- **Type**: Boolean (0/false/no or 1/true/yes)
- **Default**: Based on API key presence
- **Required**: No
- **Description**: Enable/disable OpenAI provider
- **Example**: `OPENAI_ENABLED=true`

### GROQ_ENABLED

- **Type**: Boolean (0/false/no or 1/true/yes)
- **Default**: Based on API key presence
- **Required**: No
- **Description**: Enable/disable Groq provider
- **Example**: `GROQ_ENABLED=true`

### DEEPSEEK_ENABLED

- **Type**: Boolean (0/false/no or 1/true/yes)
- **Default**: Based on API key presence
- **Required**: No
- **Description**: Enable/disable DeepSeek provider
- **Example**: `DEEPSEEK_ENABLED=false`

### GEMINI_ENABLED

- **Type**: Boolean (0/false/no or 1/true/yes)
- **Default**: Based on API key presence
- **Required**: No
- **Description**: Enable/disable Gemini provider
- **Example**: `GEMINI_ENABLED=true`

## External Services

### CHROMA_DB_PATH

- **Type**: String
- **Default**: Auto-generated path
- **Required**: No
- **Description**: Path to Chroma vector database
- **Example**: `CHROMA_DB_PATH=/app/data/vector/chroma`

### QDRANT_URL

- **Type**: String
- **Default**: None
- **Required**: No
- **Description**: URL for Qdrant vector database
- **Example**: `QDRANT_URL=<http://localhost:6333`>

### CHROMA_API_URL

- **Type**: String
- **Default**: None
- **Required**: No
- **Description**: URL for Chroma API server
- **Example**: `CHROMA_API_URL=<http://localhost:8001`>

### MCP_SERVER_URL

- **Type**: String
- **Default**: None
- **Required**: No
- **Description**: URL for MCP (Model Context Protocol) server
- **Example**: `MCP_SERVER_URL=<http://localhost:3001`>

## Environment File Examples

### Development (.env)

```bash
# Core
LOG_LEVEL=DEBUG
SKIP_RAPTOR_INIT=0
SKIP_PROBE_INIT=0

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/goblin_assistant

# Local LLM (Development)
USE_LOCAL_LLM=true
LOCAL_LLM_PROXY_URL=http://localhost:8002
LOCAL_LLM_API_KEY=dev-key

# Cloud Providers (Optional for development)
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# Security
ROUTING_ENCRYPTION_KEY=your-32-char-development-key-here
SECRET_KEY=your-development-secret-key

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Production (.env)
```bash

# Core
LOG_LEVEL=INFO
SKIP_RAPTOR_INIT=0
SKIP_PROBE_INIT=0

# Database
SUPABASE_URL=<https://your-project.supabase.co>

# Production LLM (Kamatera)
KAMATERA_LLM_API_KEY=your-production-kamatera-key
KAMATERA_LLM_URL=<http://66.55.77.147:8000>

# Cloud Providers
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
GROQ_API_KEY=gsk-your-groq-key

# Security
ROUTING_ENCRYPTION_KEY=your-32-char-production-key-here
SECRET_KEY=your-production-secret-key

# Monitoring
DATADOG_API_KEY=your-datadog-api-key
DATADOG_APP_KEY=your-datadog-app-key
REDIS_URL=redis://your-redis-host:6379/0

# CORS
CORS_ORIGINS=<https://goblin.fuaad.ai,https://api.goblin.fuaad.ai>

# Vector Database
CHROMA_DB_PATH=/app/data/vector/chroma
```

## Notes

- **Required vs Optional**: Variables marked as "Required: Yes" must be set for the application to function properly. Others are optional and have sensible defaults.
- **Security**: Never commit API keys or secrets to version control. Use environment variables or secure secret management systems.
- **Provider Priority**: The application prioritizes Kamatera-hosted LLMs for production, falling back to local Ollama instances for development.
- **Feature Flags**: Provider enable/disable flags override automatic detection based on API key presence.
- **Database**: Either `DATABASE_URL` or `SUPABASE_URL` must be provided, but not both.
