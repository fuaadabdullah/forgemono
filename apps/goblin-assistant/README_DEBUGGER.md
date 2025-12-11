# GoblinOS Assistant Debugger

This module provides AI-powered debugging assistance for the GoblinOS Assistant demo, featuring intelligent model routing between Raptor (for quick tasks) and fallback LLMs (for complex reasoning).

## Features

- **Smart Model Routing**: Automatically routes debug tasks to the most appropriate AI model
- **Low-Latency Responses**: Raptor handles quick, routine debugging tasks
- **Fallback Support**: Complex tasks route to more capable LLMs
- **Structured Responses**: Consistent API responses with model metadata

## Supported Tasks

### Raptor Tasks (Fast Path)

- `summarize_trace` - Summarize error stack traces
- `quick_fix` - Suggest simple code fixes
- `unit_test_hint` - Generate unit test suggestions
- `infer_function_name` - Suggest function names from code

### Fallback Tasks (Complex Reasoning)

- `refactor_suggestion` - Complex code refactoring
- `architecture_review` - System design feedback
- All other custom tasks

## API Usage

### Endpoint

```http
POST /debugger/suggest
```

### Request Format

```json

{
  "task": "quick_fix",
  "context": {
    "error": "ValueError: division by zero",
    "code": "result = 10 / 0",
    "language": "python"
  }
}
```

### Response Format

```json
{
  "model": "raptor",
  "suggestion": "Add a check to ensure divisor is not zero before division",
  "confidence": 0.85,
  "task": "quick_fix",
  "timestamp": "2025-11-25",
  "raw": { ... }
}
```

## Configuration

Set these environment variables in `.env.local`:

```bash

# Raptor model (for quick tasks)
RAPTOR_URL=<https://your-raptor-endpoint/api>
RAPTOR_API_KEY=your-raptor-key

# Fallback model (for complex tasks)
FALLBACK_MODEL_URL=<https://your-llm-endpoint/api>
FALLBACK_MODEL_KEY=your-llm-key
```

## Local Development

1. Install dependencies:

   ```bash
   pip install fastapi uvicorn httpx
   ```

2. Set environment variables in `.env.local`

3. Run the server:

   ```bash

   uvicorn apps.goblin_assistant.backend.main:app --reload --port 8000
   ```

4. Test the endpoint:

   ```bash
   python apps/goblin-assistant/test_debugger.py
   ```

## Testing

Run the integration tests:

```bash

python -m pytest apps/goblin-assistant/tests/test_model_router.py -v
```

Run the end-to-end test:

```bash
python apps/goblin-assistant/test_debugger.py
```

## Architecture

```mermaid

graph TD
    A[FastAPI App] --> B[Debugger Router]
    B --> C[ModelRouter]
    C --> D[Raptor]
    C --> E[Fallback LLM]
```

## Security Notes

- Never commit API keys to version control
- Use environment variables for all secrets
- Consider rate limiting for production deployment
- Log model usage for monitoring (anonymized)

## Future Enhancements

- Add confidence thresholds for automatic acceptance
- Implement caching for repeated queries
- Add telemetry for model performance tracking
- Support for custom model routing rules
