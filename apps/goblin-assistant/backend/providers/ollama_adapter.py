import os
import requests
import json
import asyncio
from typing import List, Dict, Any, Optional
import logging

from .base_adapter import AdapterBase
from .provider_registry import get_provider_registry

logger = logging.getLogger(__name__)


class OllamaAdapter(AdapterBase):
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        registry = get_provider_registry()
        config = registry.get_provider_config_dict("ollama")

        if not config:
            # Fallback to manual config if registry fails
            if base_url is None:
                base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            config = {
                "api_key": api_key,
                "base_url": base_url,
                "timeout": 30,
                "retries": 2,
                "cost_per_token_input": 0.0,
                "cost_per_token_output": 0.0,
                "latency_threshold_ms": 10000,
            }

        super().__init__(name="ollama", config=config)

    def get_status(self):
        try:
            response = requests.get(f"{self.base_url}/api/status")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models from the Ollama server."""
        try:
            # Try OpenAI-compatible endpoint first
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
                # Some proxies use X-API-Key instead of Authorization; include both
                headers["X-API-Key"] = self.api_key

            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: requests.get(
                    f"{self.base_url}/v1/models", headers=headers, timeout=10
                ),
            )
            response.raise_for_status()
            result = response.json()

            if "data" in result:
                # OpenAI format
                return [
                    {
                        "id": model["id"],
                        "name": model.get("id", ""),
                        "capabilities": ["chat"],
                        "context_window": model.get("context_length", 4096),
                        "pricing": {},
                    }
                    for model in result["data"]
                ]
            else:
                # Try Ollama native endpoint
                response = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: requests.get(f"{self.base_url}/api/tags", timeout=10)
                )
                response.raise_for_status()
                result = response.json()

                if "models" in result:
                    return [
                        {
                            "id": model["name"],
                            "name": model["name"],
                            "capabilities": ["chat"],
                            "context_window": model.get("context_length", 4096),
                            "pricing": {},
                        }
                        for model in result["models"]
                    ]

            # Fallback: return some default models
            return [
                {
                    "id": "llama3.2:3b",
                    "name": "Llama 3.2 3B",
                    "capabilities": ["chat"],
                    "context_window": 4096,
                    "pricing": {},
                },
                {
                    "id": "gemma:2b",
                    "name": "Gemma 2B",
                    "capabilities": ["chat"],
                    "context_window": 8192,
                    "pricing": {},
                },
            ]

        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            # Return default models on error
            return [
                {
                    "id": "llama3.2:3b",
                    "name": "Llama 3.2 3B",
                    "capabilities": ["chat"],
                    "context_window": 4096,
                    "pricing": {},
                },
            ]

    def generate_simple(self, prompt, model="llama2"):
        try:
            payload = {"prompt": prompt, "model": model, "stream": False}
            response = requests.post(
                f"{self.base_url}/api/generate", json=payload, timeout=30
            )
            response.raise_for_status()
            text = response.text.strip()
            lines = text.split("\n")
            for line in reversed(lines):
                line = line.strip()
                if line:
                    try:
                        return json.loads(line)
                    except json.JSONDecodeError:
                        continue
            return {
                "status": "error",
                "error": "No valid JSON found",
                "raw": text[:500],
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 1024,
        top_p: float = 1.0,
        stream: bool = False,
        **kwargs: Any,
    ) -> str:
        """Send chat completion request to Ollama/OpenAI-compatible API.

        Args:
            model: Model name to use
            messages: List of message dictionaries with role and content
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            top_p: Nucleus sampling parameter
            stream: Whether to stream the response
            **kwargs: Additional parameters

        Returns:
            The text content of the model's response
        """
        try:
            # Prepare headers
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            # Prepare payload for OpenAI-compatible API
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": top_p,
                "stream": stream,
                **kwargs,
            }

            # Make request
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: requests.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=60,
                ),
            )
            response.raise_for_status()

            result = response.json()

            # Handle different response formats
            if "choices" in result and len(result["choices"]) > 0:
                # OpenAI-compatible format
                return result["choices"][0]["message"]["content"]
            elif "content" in result:
                # Direct content format (like from Kamatera server)
                return result["content"]
            elif "response" in result:
                # Native Ollama format
                return result["response"]
            else:
                logger.error(f"Unexpected response format from Ollama: {result}")
                logger.error(f"Full response: {response.text}")
                raise Exception("Unexpected response format from Ollama API")

        except Exception as e:
            logger.error(f"Ollama chat request failed: {e}")
            raise

    async def generate(
        self, messages: List[Dict[str, str]], **kwargs
    ) -> Dict[str, Any]:
        """Generate completion using Ollama API.

        Args:
            messages: List of message dictionaries
            **kwargs: Additional parameters (model, temperature, max_tokens, etc.)

        Returns:
            Dict containing response data
        """
        model = kwargs.get("model", "llama2")

        # Use the existing chat method but wrap it to match the interface
        content = await self.chat(model, messages, **kwargs)

        # Ollama doesn't provide token usage info, so we estimate
        # Rough estimation: 4 chars per token
        input_chars = sum(len(msg.get("content", "")) for msg in messages)
        output_chars = len(content)
        input_tokens = input_chars // 4
        output_tokens = output_chars // 4

        # Log cost (Ollama is typically free/local)
        self._log_cost(input_tokens, output_tokens)

        return {
            "content": content,
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
            },
            "model": model,
            "finish_reason": "stop",  # Ollama doesn't provide this
        }

    async def a_generate(
        self, messages: List[Dict[str, str]], **kwargs
    ) -> Dict[str, Any]:
        """Async generate completion using Ollama API.

        Args:
            messages: List of message dictionaries
            **kwargs: Additional parameters

        Returns:
            Dict containing response data
        """
        # For Ollama, async and sync are the same
        return await self.generate(messages, **kwargs)
