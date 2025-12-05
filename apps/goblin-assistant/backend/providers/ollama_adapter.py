import os
import requests
import json
import asyncio
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class OllamaAdapter:
    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key
        if base_url is None:
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.base_url = base_url

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

    def generate(self, prompt, model="llama2"):
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
