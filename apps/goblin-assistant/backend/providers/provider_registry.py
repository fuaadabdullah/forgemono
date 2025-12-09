"""
Provider Registry for centralized configuration management.

Centralizes all provider configuration including hosts, costs, latency thresholds,
and other provider-specific settings.
"""

import json
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ProviderStatus(Enum):
    """Provider operational status."""

    ACTIVE = "active"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    DISABLED = "disabled"


@dataclass
class ProviderConfig:
    """Configuration for a single provider."""

    name: str
    host: str
    api_key_env: str
    base_url: Optional[str] = None
    timeout_seconds: int = 30
    max_retries: int = 2
    cost_per_token_input: float = 0.0
    cost_per_token_output: float = 0.0
    latency_threshold_ms: int = 5000  # 5 seconds
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60
    status: ProviderStatus = ProviderStatus.ACTIVE
    models: List[str] = None
    capabilities: List[str] = None

    def __post_init__(self):
        if self.models is None:
            self.models = []
        if self.capabilities is None:
            self.capabilities = ["chat"]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProviderConfig":
        """Create from dictionary."""
        data["status"] = ProviderStatus(data["status"])
        return cls(**data)


class ProviderRegistry:
    """Central registry for all provider configurations."""

    def __init__(self, config_file: Optional[str] = None):
        """Initialize the provider registry.

        Args:
            config_file: Path to JSON config file (optional)
        """
        self.providers: Dict[str, ProviderConfig] = {}
        self.config_file = config_file or os.path.join(
            os.path.dirname(__file__), "provider_config.json"
        )
        self._load_config()

    def _load_config(self):
        """Load configuration from file or use defaults."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                    for name, config_data in data.items():
                        self.providers[name] = ProviderConfig.from_dict(config_data)
                logger.info(f"Loaded provider config from {self.config_file}")
            except Exception as e:
                logger.warning(f"Failed to load config file: {e}, using defaults")
                self._load_defaults()
        else:
            logger.info("No config file found, using defaults")
            self._load_defaults()

    def _load_defaults(self):
        """Load default provider configurations."""
        defaults = {
            "openai": ProviderConfig(
                name="openai",
                host="api.openai.com",
                api_key_env="OPENAI_API_KEY",
                base_url="https://api.openai.com/v1",
                cost_per_token_input=0.0015,
                cost_per_token_output=0.002,
                latency_threshold_ms=3000,
                models=["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
                capabilities=["chat", "embeddings", "vision"],
            ),
            "anthropic": ProviderConfig(
                name="anthropic",
                host="api.anthropic.com",
                api_key_env="ANTHROPIC_API_KEY",
                base_url="https://api.anthropic.com",
                cost_per_token_input=0.008,
                cost_per_token_output=0.024,
                latency_threshold_ms=4000,
                models=["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
                capabilities=["chat", "vision"],
            ),
            "ollama": ProviderConfig(
                name="ollama",
                host="localhost:11434",
                api_key_env="OLLAMA_API_KEY",
                base_url="http://localhost:11434",
                cost_per_token_input=0.0,
                cost_per_token_output=0.0,
                latency_threshold_ms=10000,
                models=["llama2", "codellama", "mistral"],
                capabilities=["chat", "embeddings"],
            ),
            "groq": ProviderConfig(
                name="groq",
                host="api.groq.com",
                api_key_env="GROQ_API_KEY",
                base_url="https://api.groq.com/openai/v1",
                cost_per_token_input=0.0001,
                cost_per_token_output=0.0001,
                latency_threshold_ms=2000,
                models=["llama2-70b", "mixtral-8x7b"],
                capabilities=["chat"],
            ),
            "deepseek": ProviderConfig(
                name="deepseek",
                host="api.deepseek.com",
                api_key_env="DEEPSEEK_API_KEY",
                base_url="https://api.deepseek.com",
                cost_per_token_input=0.0001,
                cost_per_token_output=0.0002,
                latency_threshold_ms=3000,
                models=["deepseek-chat", "deepseek-coder"],
                capabilities=["chat"],
            ),
        }

        self.providers.update(defaults)

    def get_provider(self, name: str) -> Optional[ProviderConfig]:
        """Get provider configuration by name.

        Args:
            name: Provider name

        Returns:
            ProviderConfig or None if not found
        """
        return self.providers.get(name)

    def get_all_providers(self) -> Dict[str, ProviderConfig]:
        """Get all provider configurations.

        Returns:
            Dict of provider name -> ProviderConfig
        """
        return self.providers.copy()

    def get_active_providers(self) -> Dict[str, ProviderConfig]:
        """Get only active providers.

        Returns:
            Dict of active provider name -> ProviderConfig
        """
        return {
            name: config
            for name, config in self.providers.items()
            if config.status == ProviderStatus.ACTIVE
        }

    def update_provider_status(self, name: str, status: ProviderStatus):
        """Update provider operational status.

        Args:
            name: Provider name
            status: New status
        """
        if name in self.providers:
            self.providers[name].status = status
            logger.info(f"Updated {name} status to {status.value}")
        else:
            logger.warning(f"Provider {name} not found for status update")

    def get_provider_config_dict(self, name: str) -> Optional[Dict[str, Any]]:
        """Get provider config as dictionary for adapter initialization.

        Args:
            name: Provider name

        Returns:
            Config dict or None if provider not found
        """
        provider = self.get_provider(name)
        if not provider:
            return None

        api_key = os.getenv(provider.api_key_env)
        if not api_key:
            logger.warning(f"No API key found for {name} ({provider.api_key_env})")
            return None

        return {
            "api_key": api_key,
            "base_url": provider.base_url,
            "timeout": provider.timeout_seconds,
            "retries": provider.max_retries,
            "cost_per_token_input": provider.cost_per_token_input,
            "cost_per_token_output": provider.cost_per_token_output,
            "latency_threshold_ms": provider.latency_threshold_ms,
        }

    def save_config(self):
        """Save current configuration to file."""
        try:
            data = {name: config.to_dict() for name, config in self.providers.items()}
            with open(self.config_file, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved provider config to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def add_provider(self, config: ProviderConfig):
        """Add a new provider configuration.

        Args:
            config: ProviderConfig to add
        """
        self.providers[config.name] = config
        logger.info(f"Added provider {config.name}")

    def remove_provider(self, name: str):
        """Remove a provider configuration.

        Args:
            name: Provider name to remove
        """
        if name in self.providers:
            del self.providers[name]
            logger.info(f"Removed provider {name}")
        else:
            logger.warning(f"Provider {name} not found for removal")


# Global registry instance
_registry_instance: Optional[ProviderRegistry] = None


def get_provider_registry() -> ProviderRegistry:
    """Get the global provider registry instance."""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ProviderRegistry()
    return _registry_instance
