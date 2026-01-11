"""
Provider dispatcher that routes requests to appropriate provider implementations.
"""

import os
from typing import Dict, Any
from .base import BaseProvider
from .openai import OpenAIProvider
from .anthropic import AnthropicProvider
from .ollama import OllamaProvider
from .llama_cpp import LlamaCPPProvider
from .kamatera_ollama import KamateraOllamaProvider
from .kamatera_llamacpp import KamateraLlamaCppProvider
from .groq import GroqProvider
from .gemini import GeminiProvider
from .generic import GenericProvider
from .mock_provider import MockProvider

# Load environment variables
try:
    from dotenv import load_dotenv

    # Load from multiple potential locations
    load_dotenv()  # .env
    load_dotenv(".env.local")  # .env.local
except ImportError:
    pass


class ProviderDispatcher:
    """Routes provider requests to appropriate provider implementations."""

    def __init__(self):
        self._providers: Dict[str, BaseProvider] = {}
        self._provider_configs = self._load_provider_configs()

    def _load_provider_configs(self) -> Dict[str, Dict[str, Any]]:
        """Load provider configurations from TOML file."""
        try:
            import toml

            config_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "config", "providers.toml"
            )
            with open(config_path, "r") as f:
                config = toml.load(f)
                return config.get("providers", {})
        except Exception as e:
            print(f"Warning: Could not load provider config: {e}")
            return self._get_basic_providers()

    def _get_basic_providers(self) -> Dict[str, Dict[str, Any]]:
        """Get basic provider configurations for development/testing."""
        return {
            "openai": {
                "endpoint": "https://api.openai.com",
                "api_key_env": "OPENAI_API_KEY",
                "invoke_path": "/v1/chat/completions",
            },
            "anthropic": {
                "endpoint": "https://api.anthropic.com",
                "api_key_env": "ANTHROPIC_API_KEY",
                "invoke_path": "/v1/messages",
            },
            "ollama": {
                "endpoint": "http://localhost:11434",
                "invoke_path": "/api/generate",
            },
            # GCP Ollama Server (replaces Kamatera)
            "ollama_gcp": {
                "endpoint": os.getenv("OLLAMA_GCP_URL", "http://localhost:11434"),
                "invoke_path": "/api/generate",
                "api_key_env": "LOCAL_LLM_API_KEY",
                "default_model": "qwen2.5:latest",
            },
            # GCP LlamaCPP Server (replaces Kamatera)
            "llamacpp_gcp": {
                "endpoint": os.getenv("LLAMACPP_GCP_URL", "http://localhost:8000"),
                "invoke_path": "/v1/chat/completions",
                "api_key_env": "LOCAL_LLM_API_KEY",
                "default_model": "qwen2.5-7b-instruct",
            },
            # Legacy Kamatera endpoints (deprecated - use GCP instead)
            "ollama_kamatera": {
                "endpoint": os.getenv(
                    "KAMATERA_SERVER2_URL", "http://192.175.23.150:8002"
                ),
                "invoke_path": "/api/generate",
                "api_key_env": "LOCAL_LLM_API_KEY",
            },
            "llamacpp_kamatera": {
                "endpoint": os.getenv(
                    "KAMATERA_SERVER1_URL", "http://45.61.51.220:8000"
                ),
                "invoke_path": "/v1/chat/completions",
                "api_key_env": "LOCAL_LLM_API_KEY",
                "default_model": "qwen2.5:latest",
            },
            "groq": {
                "endpoint": "https://api.groq.com",
                "api_key_env": "GROQ_API_KEY",
                "invoke_path": "/v1/chat/completions",
            },
            "gemini": {
                "endpoint": "https://generativelanguage.googleapis.com",
                "api_key_env": "GOOGLE_API_KEY",
            },
        }

    def _get_provider_config(self, provider_id: str) -> Dict[str, Any]:
        """Get provider configuration."""
        return self._provider_configs.get(provider_id, {})

    def _create_provider(
        self, provider_id: str, config: Dict[str, Any]
    ) -> BaseProvider:
        """Create provider instance based on provider ID."""
        endpoint = config.get("endpoint", "")

        # Route based on provider ID or endpoint patterns
        if provider_id == "openai" or "openai.com" in endpoint:
            return OpenAIProvider.from_config(config)
        elif provider_id == "anthropic" or "anthropic.com" in endpoint:
            return AnthropicProvider.from_config(config)
        elif provider_id == "ollama_kamatera" or "192.175.23.150:8002" in endpoint:
            return KamateraOllamaProvider.from_config(config)
        elif provider_id == "llamacpp_kamatera" or "45.61.51.220:8000" in endpoint:
            return KamateraLlamaCppProvider.from_config(config)
        elif (
            provider_id in ["ollama", "ollama_gcp"]
            or "localhost:11434" in endpoint
            or "45.61.51.220:8002" in endpoint
            or "34.60.255.199:11434" in endpoint  # GCP Ollama
        ):
            return OllamaProvider.from_config(config)
        elif (
            provider_id in ["llamacpp", "llamacpp_kamatera", "llamacpp_gcp"]
            or "127.0.0.1:8080" in endpoint
            or "192.175.23.150:8000" in endpoint
            or "136.119.9.188:8000" in endpoint  # GCP LlamaCPP
            or "ngrok.io" in endpoint
        ):
            return LlamaCPPProvider.from_config(config)
        elif provider_id == "groq" or "groq.com" in endpoint:
            return GroqProvider.from_config(config)
        elif (
            provider_id in ["gemini", "google"]
            or "generativelanguage.googleapis.com" in endpoint
        ):
            return GeminiProvider.from_config(config)
        elif provider_id == "mock":
            return MockProvider({"default_model": "mock-gpt"})
        elif provider_id in [
            "deepseek",
            "together",
            "replicate",
            "huggingface",
            "cohere",
        ]:
            # These providers use OpenAI-compatible APIs, so use OpenAI provider
            return OpenAIProvider.from_config(config)
        else:
            # Generic provider for custom endpoints
            return GenericProvider.from_config(config)

    def get_provider(self, provider_id: str) -> BaseProvider:
        """Get or create a provider instance."""
        if provider_id not in self._providers:
            config = self._get_provider_config(provider_id)
            self._providers[provider_id] = self._create_provider(provider_id, config)
        return self._providers[provider_id]

    async def _auto_select_provider(self) -> str:
        """Auto-select the best available provider based on configuration."""
        # Priority order: OpenAI -> Anthropic -> Groq -> Google -> GCP LLMs -> Local -> Legacy Kamatera
        priority_providers = [
            ("openai", "OPENAI_API_KEY"),
            ("anthropic", "ANTHROPIC_API_KEY"),
            ("groq", "GROQ_API_KEY"),
            ("google", "GOOGLE_API_KEY"),
            ("ollama_gcp", "OLLAMA_GCP_URL"),
            ("llamacpp_gcp", "LLAMACPP_GCP_URL"),
            ("ollama", None),  # Local Ollama, no key required
            ("llamacpp_kamatera", "LOCAL_LLM_API_KEY"),  # Legacy
            ("ollama_kamatera", "LOCAL_LLM_API_KEY"),  # Legacy
        ]

        for provider_id, env_var in priority_providers:
            config = self._get_provider_config(provider_id)
            if not config:
                continue

            # If no env_var required, provider is available
            if env_var is None:
                print(f"Auto-selected provider: {provider_id} (no key required)")
                return provider_id

            # Check if env var is set
            env_value = os.getenv(env_var, "")
            if config and env_value:
                print(
                    f"Auto-selected provider: {provider_id} (configured via {env_var})"
                )
                return provider_id

        # Fallback to mock for development stability if nothing else works
        print("Warning: No providers available, falling back to mock")
        return "mock"

    async def invoke_provider(
        self,
        provider_id: str,
        model: str,
        payload: Dict[str, Any],
        timeout_ms: int,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """
        Invoke a provider with the given parameters.
        """
        # Handle None provider_id - auto-select best available
        if provider_id is None:
            provider_id = await self._auto_select_provider()
            print(f"Auto-selected provider: {provider_id}")

        config = self._get_provider_config(provider_id)
        if not config:
            return {
                "ok": False,
                "error": f"unknown-provider:{provider_id}",
                "latency_ms": 0,
            }

        # If model is not provided, use the default model for this provider
        if model is None:
            model = config.get("default_model")
            # If still None, let the provider implementation decide its own default

        provider = self.get_provider(provider_id)

        # Extract prompt from payload
        prompt = ""
        if "messages" in payload:
            # OpenAI-style messages - find the LAST user message as the active prompt
            for msg in reversed(payload["messages"]):
                if msg.get("role") == "user":
                    prompt = msg.get("content", "")
                    break

        # Fallback to prompt in payload if messages not found or no user message
        if not prompt:
            prompt = payload.get("prompt", "")

        if not prompt and "messages" not in payload:
            return {"ok": False, "error": "no-prompt-provided", "latency_ms": 0}

        # Invoke the provider - NO MOCK FALLBACK
        try:
            # Remove model from payload to avoid duplicate keyword argument
            invoke_payload = payload.copy()
            invoke_payload.pop("model", None)

            result = await provider.invoke(
                prompt=prompt,
                stream=stream,
                model=model,
                timeout_ms=timeout_ms,
                **invoke_payload,
            )

            # Handle streaming vs non-streaming results
            if isinstance(result, dict):
                if result.get("ok", False):
                    if stream:
                        # For streaming, return the stream generator
                        return {
                            "ok": True,
                            "stream": result.get("stream"),
                            "latency_ms": result.get("latency_ms", 0),
                        }
                    else:
                        # For non-streaming, return the result
                        return result
                else:
                    # Return the original error - NO MOCK FALLBACK
                    return result
            else:
                # Should not happen with current implementation
                return {
                    "ok": False,
                    "error": "invalid-provider-response",
                    "latency_ms": 0,
                }

        except Exception as e:
            # Return the original error - NO MOCK FALLBACK
            return {
                "ok": False,
                "error": f"provider-invocation-error:{str(e)}",
                "latency_ms": 0,
            }


# Global dispatcher instance
dispatcher = ProviderDispatcher()


async def invoke_provider(
    pid: str, model: str, payload: Dict[str, Any], timeout_ms: int, stream: bool = False
) -> Dict[str, Any]:
    """
    Legacy function that maintains compatibility with existing code.
    Routes to the new provider dispatcher.
    """
    return await dispatcher.invoke_provider(pid, model, payload, timeout_ms, stream)
