# Groq API Reference Documentation

## Overview
Comprehensive reference documentation for the Groq API, including endpoints, parameters, and examples.

**Source**: <https://console.groq.com/docs/api-reference>
**Last Updated**: November 23, 2025

## API Endpoints

### Chat Completions

- **Endpoint**: `POST <https://api.groq.com/openai/v1/chat/completions`>
- **Description**: Creates a model response for the given chat conversation
- **Key Parameters**:
  - `messages`: Array of message objects
  - `model`: Model ID (e.g., "llama-3.3-70b-versatile")
  - `temperature`: Sampling temperature (0-2)
  - `max_tokens`: Maximum completion tokens
  - `stream`: Enable streaming responses

### Responses API (Beta)

- **Endpoint**: `POST <https://api.groq.com/openai/v1/responses`>
- **Description**: Creates a model response for given input (alternative to chat completions)
- **Key Features**:
  - Supports reasoning models
  - Structured output formats
  - Tool calling capabilities

### Audio Processing

- **Transcription**: `POST /audio/transcriptions` - Convert audio to text
- **Translation**: `POST /audio/translations` - Translate audio to English
- **Speech Generation**: `POST /audio/speech` - Generate audio from text

### Models

- **List Models**: `GET /models` - Get available models
- **Retrieve Model**: `GET /models/{model}` - Get specific model details

### Batch Processing

- **Create Batch**: `POST /batches` - Process multiple requests asynchronously
- **List Batches**: `GET /batches` - View batch jobs
- **Cancel Batch**: `POST /batches/{id}/cancel` - Cancel running batch

### File Management

- **Upload File**: `POST /files` - Upload files for batch processing
- **List Files**: `GET /files` - View uploaded files
- **Download File**: `GET /files/{id}/content` - Download file content

### Fine Tuning (Beta)

- **Create Fine Tuning**: `POST /fine_tunings` - Create custom models
- **List Fine Tunings**: `GET /fine_tunings` - View fine tuning jobs

## Authentication

- **Header**: `Authorization: Bearer $GROQ_API_KEY`
- **Base URL**: `<https://api.groq.com/openai/v1`>

## Supported Models

- **Llama Models**: llama-3.3-70b-versatile, llama-3.1-8b-instant, etc.
- **Gemma**: gemma2-9b-it
- **Mixtral**: mixtral-8x7b-32768
- **Whisper**: whisper-large-v3, whisper-large-v3-turbo (for audio)
- **TTS Models**: playai-tts (text-to-speech)

## Key Features

- **OpenAI Compatible**: Drop-in replacement for OpenAI API
- **Fast Inference**: Optimized for speed and low latency
- **Tool Calling**: Function calling capabilities
- **Streaming**: Real-time response streaming
- **Batch Processing**: Asynchronous job processing
- **Audio Processing**: Speech-to-text, text-to-speech, translation
- **Structured Outputs**: JSON schema validation
- **Reasoning Models**: Advanced reasoning capabilities

## Rate Limits & Usage

- **Free Tier**: Limited requests per hour
- **Paid Plans**: Higher limits based on subscription
- **Usage Tracking**: Detailed token and request counting
- **Queue Time**: Minimal queue times for most requests

## Error Handling

- **429**: Rate limit exceeded
- **401**: Invalid API key
- **400**: Bad request parameters
- **500**: Server errors

## SDK Support

- **Python**: `pip install groq`
- **JavaScript/TypeScript**: `npm install groq-sdk`
- **Go, Java, .NET**: Official SDKs available

## Example Usage (Python)

```python
from groq import Groq

client = Groq(api_key="your-api-key")

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": "Hello!"}],
    temperature=0.7,
    max_tokens=100
)

print(response.choices[0].message.content)
```

## Example Usage (JavaScript)

```javascript

import Groq from "groq-sdk";

const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });

const completion = await groq.chat.completions.create({
    messages: [{ role: "user", content: "Hello!" }],
    model: "llama-3.3-70b-versatile",
});
```

## Best Practices

1. **Error Handling**: Always implement proper error handling
2. **Rate Limiting**: Monitor usage and implement backoff strategies
3. **Streaming**: Use streaming for real-time applications
4. **Model Selection**: Choose appropriate models for your use case
5. **Token Limits**: Monitor token usage to avoid unexpected costs
6. **Caching**: Cache responses when appropriate

## Pricing

- **Pay-per-token**: Competitive pricing based on model and usage
- **Free Tier**: Generous free tier for testing and development
- **Volume Discounts**: Available for high-volume users

## Support

- **Documentation**: <https://console.groq.com/docs>
- **API Status**: Check service status and uptime
- **Community**: Active developer community
- **Enterprise Support**: Available for business customers

---

*This documentation was extracted from the official Groq API reference as of November 23, 2025. For the most up-to-date information, always refer to the official documentation at <https://console.groq.com/docs/api-reference*</content>>
<parameter name="filePath">/Users/fuaadabdullah/ForgeMonorepo/docs/GROQ_API_REFERENCE.md
