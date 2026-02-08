# Moonshot AI API Documentation

## Basic Information

**Public Service Address**: `<https://api.moonshot.ai`>

Moonshot offers API services based on HTTP, and for most APIs, they are compatible with the OpenAI SDK.

## Authentication

Replace `$MOONSHOT_API_KEY` with the API Key created on the platform.

## Models

Available models:

- `kimi-k2-0905-preview`
- `kimi-k2-0711-preview`
- `kimi-k2-turbo-preview` (recommended)
- `kimi-k2-thinking-turbo`
- `kimi-k2-thinking`
- `moonshot-v1-8k`
- `moonshot-v1-32k`
- `moonshot-v1-128k`
- `moonshot-v1-auto`
- `kimi-latest`
- `moonshot-v1-8k-vision-preview`
- `moonshot-v1-32k-vision-preview`
- `moonshot-v1-128k-vision-preview`

## Basic Usage

### Single-turn Chat

```python
from openai import OpenAI

client = OpenAI(
    api_key = "$MOONSHOT_API_KEY",
    base_url = "https://api.moonshot.ai/v1",
)

completion = client.chat.completions.create(
    model = "kimi-k2-turbo-preview",
    messages = [
        {"role": "system", "content": "You are Kimi, an AI assistant provided by Moonshot AI."},
        {"role": "user", "content": "Hello, my name is Li Lei. What is 1+1?"}
    ],
    temperature = 0.6,
)

print(completion.choices[0].message.content)
```

### Multi-turn Chat

```python

history = [
    {"role": "system", "content": "You are Kimi, an AI assistant provided by Moonshot AI."}
]

def chat(query, history):
    history.append({"role": "user", "content": query})
    completion = client.chat.completions.create(
        model="kimi-k2-turbo-preview",
        messages=history,
        temperature=0.6,
    )
    result = completion.choices[0].message.content
    history.append({"role": "assistant", "content": result})
    return result
```

## Advanced Features

### Tool Use / Function Calling

The Kimi model supports function calling to link external tools:

```python
completion = client.chat.completions.create(
    model = "kimi-k2-turbo-preview",
    messages = [
        {"role": "user", "content": "Determine whether 3214567 is a prime number through programming."}
    ],
    tools = [{
        "type": "function",
        "function": {
            "name": "CodeRunner",
            "description": "A code executor that supports running Python and JavaScript code",
            "parameters": {
                "properties": {
                    "language": {
                        "type": "string",
                        "enum": ["python", "javascript"]
                    },
                    "code": {
                        "type": "string",
                        "description": "The code is written here"
                    }
                },
                "type": "object"
            }
        }
    }],
    temperature = 0.6,
)
```

**Tool Configuration Requirements:**
- Maximum 128 functions in tools
- Function name must match regex: `^[a-zA-Z_][a-zA-Z0-9-_]{0,63}$`
- Must include `type`, `name`, `description`, and `parameters`
- Parameters root must be an object (JSON schema subset)

### Partial Mode (JSON Mode)

Force JSON output by starting assistant response with `{`:

```python

completion = client.chat.completions.create(
    model="kimi-k2-turbo-preview",
    messages=[
        {
            "role": "system",
            "content": "Extract the name, size, price, and color from the product description and output them in a JSON object.",
        },
        {
            "role": "user",
            "content": "The DaMi SmartHome Mini is a compact smart home assistant...",
        },
        {
            "role": "assistant",
            "content": "{",
            "partial": True
        },
    ],
    temperature=0.6,
)

print('{' + completion.choices[0].message.content)
```

### Role-Playing

Use Partial Mode with `name` field for consistent character role-playing:

```python
completion = client.chat.completions.create(
    model="kimi-k2-turbo-preview",
    messages=[
        {
            "role": "system",
            "content": "You are now playing the role of Dr. Kelsier...",
        },
        {
            "role": "user",
            "content": "What do you think of Thucydides and Amiya?",
        },
        {
            "role": "assistant",
            "name": "Dr. Kelsier",
            "content": "",
            "partial": True,
        },
    ],
    temperature=0.6,
    max_tokens=65536,
)
```

**Tips for Character Consistency:**
1. Provide clear character descriptions
2. Include personality, background, traits, and quirks
3. Add speech style and backstory details
4. Guide behavior in various situations
5. Periodically reinforce character settings in long conversations

### Vision Models

Vision models support image input via base64 encoding:

```python

import base64

with open("your_image_path", 'rb') as f:
    img_base = base64.b64encode(f.read()).decode('utf-8')

response = client.chat.completions.create(
    model="moonshot-v1-8k-vision-preview",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{img_base}"
                    }
                },
                {
                    "type": "text",
                    "text": "Please describe this image."
                }
            ]
        }
    ]
)
```

## API Endpoints

### Chat Completion
```
POST <https://api.moonshot.ai/v1/chat/completions>
```

### List Models
```
GET <https://api.moonshot.ai/v1/models>
```

## Parameters

### Required Parameters

- `messages`: List of conversation messages
- `model`: Model ID (e.g., `kimi-k2-turbo-preview`)

### Optional Parameters

- `max_tokens`: Maximum tokens to generate
- `temperature`: Sampling temperature (0-1, default: 0.6 for kimi-k2, 1.0 for kimi-k2-thinking, 0.0 for moonshot-v1)
- `top_p`: Nucleus sampling (default: 1.0)
- `n`: Number of results (default: 1, max: 5)
- `presence_penalty`: Presence penalty (-2.0 to 2.0, default: 0)
- `frequency_penalty`: Frequency penalty (-2.0 to 2.0, default: 0)
- `response_format`: JSON mode `{"type": "json_object"}` or `{"type": "text"}`
- `stop`: Stop words (max 5 strings, 32 bytes each)
- `stream`: Enable streaming responses (default: false)

## Error Codes

### Common Errors

- **400 content_filter**: Content rejected due to high risk
- **400 invalid_request_error**: Invalid request format or missing parameters
- **401 invalid_authentication_error**: Invalid API key
- **429 exceeded_current_quota_error**: Insufficient account balance
- **429 rate_limit_reached_error**: Rate limit exceeded (concurrency, RPM, TPM, TPD)
- **403 permission_denied_error**: API not accessible
- **404 resource_not_found_error**: Model not found or permission denied
- **429 engine_overloaded_error**: Too many concurrent requests
- **500 server_error**: Internal error

## SDK Requirements

- Python: >= 3.7.1
- Node.js: >= 18
- OpenAI SDK: >= 1.0.0

```bash
pip install --upgrade 'openai>=1.0'
```

## Integrations

Compatible with Agent platforms:
- Coze
- Bisheng
- Dify
- LangChain

## Notes

- Context window increases linearly with conversation length
- Optimize by retaining only recent conversation rounds when necessary
- Use RAG frameworks for extensive character background information
- Function names should be easily understandable English words
- Maximum 128 functions in tools array
