"""
Provider Registry for unified provider management.

Loads providers from config and provides get_available_providers() for routing.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from importlib import import_module

from .base import ProviderBase, HealthStatus

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """Registry for managing provider instances implementing ProviderBase."""

    def __init__(self, config_file: Optional[str] = None):
        """Initialize provider registry.

        Args:
            config_file: Path to provider configuration JSON file
        """
        self.providers: Dict[str, ProviderBase] = {}
        self.config_file = config_file or os.path.join(
            os.path.dirname(__file__), "providers_config.json"
        )
        self._load_providers()

    def _load_providers(self):
        """Load and initialize providers from configuration."""
        config = self._load_config()

        # Default provider configurations
        default_configs = {
            "openai": {
                "module": "providers.openai",
                "class": "OpenAIProvider",
                "enabled": bool(os.getenv("OPENAI_API_KEY")),
                "config": {
                    "api_key": os.getenv("OPENAI_API_KEY"),
                    "base_url": "https://api.openai.com/v1",
                    "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
                    "cost_per_token_input": 0.0015,
                    "cost_per_token_output": 0.002,
                },
            },
            "anthropic": {
                "module": "providers.anthropic",
                "class": "AnthropicProvider",
                "enabled": bool(os.getenv("ANTHROPIC_API_KEY")),
                "config": {
                    "api_key": os.getenv("ANTHROPIC_API_KEY"),
                    "base_url": "https://api.anthropic.com",
                    "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
                    "cost_per_token_input": 0.008,
                    "cost_per_token_output": 0.024,
                },
            },
            "ollama": {
                "module": "providers.ollama",
                "class": "OllamaProvider",
                "enabled": True,  # Local provider, always enabled if available
                "config": {
                    "base_url": "http://localhost:11434",
                    "models": ["llama2", "codellama", "mistral"],
                    "cost_per_token_input": 0.0,
                    "cost_per_token_output": 0.0,
                },
            },
            "llamacpp": {
                "module": "providers.llamacpp",
                "class": "LlamaCppProvider",
                "enabled": True,  # Local provider, always enabled if available
                "config": {
                    "models": ["local-model"],
                    "cost_per_token_input": 0.0,
                    "cost_per_token_output": 0.0,
                },
            },
            "groq": {
                "module": "providers.groq",
                "class": "GroqProvider",
                "enabled": bool(os.getenv("GROQ_API_KEY")),
                "config": {
                    "api_key": os.getenv("GROQ_API_KEY"),
                    "base_url": "https://api.groq.com/openai/v1",
                    "models": ["llama2-70b", "mixtral-8x7b"],
                    "cost_per_token_input": 0.0001,
                    "cost_per_token_output": 0.0001,
                },
            },
            "deepseek": {
                "module": "providers.deepseek",
                "class": "DeepSeekProvider",
                "enabled": bool(os.getenv("DEEPSEEK_API_KEY")),
                "config": {
                    "api_key": os.getenv("DEEPSEEK_API_KEY"),
                    "base_url": "https://api.deepseek.com",
                    "models": ["deepseek-chat"],
                    "cost_per_token_input": 0.0001,
                    "cost_per_token_output": 0.0002,
                },
            },
        }

        # Merge with config file settings
        if config:
            for provider_id, provider_config in config.items():
                if provider_id in default_configs:
                    default_configs[provider_id].update(provider_config)
                else:
                    default_configs[provider_id] = provider_config

        # Initialize enabled providers
        for provider_id, config in default_configs.items():
            if config.get("enabled", False):
                try:
                    self._initialize_provider(provider_id, config)
                except Exception as e:
                    logger.warning(f"Failed to initialize provider {provider_id}: {e}")

    def _load_config(self) -> Optional[Dict[str, Any]]:
        """Load provider configuration from file."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load provider config: {e}")
        return None

    def _initialize_provider(self, provider_id: str, config: Dict[str, Any]):
        """Initialize a single provider instance."""
        try:
            module_name = config["module"]
            class_name = config["class"]

            module = import_module(module_name)
            provider_class = getattr(module, class_name)

            # Initialize provider with config
            provider_config = config.get("config", {})
            provider = provider_class(**provider_config)

            self.providers[provider_id] = provider
            logger.info(f"Initialized provider {provider_id}")

        except ImportError as e:
            logger.warning(f"Provider module {module_name} not available: {e}")
        except AttributeError as e:
            logger.warning(
                f"Provider class {class_name} not found in {module_name}: {e}"
            )
        except Exception as e:
            logger.warning(f"Failed to initialize provider {provider_id}: {e}")

    def get_available_providers(self) -> List[ProviderBase]:
        """Get all available (healthy) providers.

        Returns:
            List of ProviderBase instances that are currently healthy
        """
        available = []
        for provider in self.providers.values():
            try:
                if provider.health_check() == HealthStatus.HEALTHY:
                    available.append(provider)
            except Exception as e:
                logger.warning(f"Health check failed for {provider.provider_id}: {e}")

        return available

    def get_provider(self, provider_id: str) -> Optional[ProviderBase]:
        """Get a specific provider by ID.

        Args:
            provider_id: Provider identifier

        Returns:
            ProviderBase instance or None if not found
        """
        return self.providers.get(provider_id)

    def get_providers_by_capability(self, capability: str) -> List[ProviderBase]:
        """Get providers that support a specific capability.

        Args:
            capability: Capability to filter by (e.g., "vision", "streaming")

        Returns:
            List of providers supporting the capability
        """
        providers = []
        for provider in self.get_available_providers():
            caps = provider.capabilities
            if caps.get("supports_" + capability, False) or capability in caps.get(
                "capabilities", []
            ):
                providers.append(provider)
        return providers

    def get_providers_for_model(self, model: str) -> List[ProviderBase]:
        """Get providers that support a specific model.

        Args:
            model: Model name to find providers for

        Returns:
            List of providers that support the model
        """
        providers = []
        for provider in self.get_available_providers():
            if model in provider.capabilities.get("models", []):
                providers.append(provider)
        return providers

    def reload_providers(self):
        """Reload all providers from configuration."""
        self.providers.clear()
        self._load_providers()
        logger.info("Reloaded all providers")


# Global registry instance
_registry: Optional[ProviderRegistry] = None


def get_provider_registry() -> ProviderRegistry:
    """Get the global provider registry instance."""
    global _registry
    if _registry is None:
        _registry = ProviderRegistry()
    return _registry
