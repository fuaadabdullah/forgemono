"""
Provider configuration settings for monitoring
"""

from typing import List, Dict, Any


# Default provider configurations
DEFAULT_PROVIDERS = [
    {
        "name": "openai",
        "api_key": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1",
        "models": ["gpt-4", "gpt-3.5-turbo"],
        "enabled": True,
    },
    {
        "name": "anthropic",
        "api_key": "ANTHROPIC_API_KEY",
        "base_url": "https://api.anthropic.com",
        "models": ["claude-3-opus", "claude-3-sonnet"],
        "enabled": True,
    },
    {
        "name": "google",
        "api_key": "GOOGLE_API_KEY",
        "base_url": "https://generativelanguage.googleapis.com/v1",
        "models": ["gemini-pro", "gemini-ultra"],
        "enabled": True,
    },
    {
        "name": "ollama_kamatera",
        "api_key": None,
        "base_url": "http://192.175.23.150:8002",
        "models": [
            "phi3:latest",
            "gemma2:latest",
            "qwen2.5:latest",
            "codellama:latest",
            "mistral:latest",
        ],
        "enabled": True,
    },
    {
        "name": "llamacpp_kamatera",
        "api_key": None,
        "base_url": "http://45.61.51.220:8000",
        "models": [
            "qwen2.5:latest",
            "gemma2:latest",
            "codellama:latest",
            "llama3.1:latest",
        ],
        "enabled": True,
    },
    {
        "name": "siliconeflow",
        "api_key": "SILICONEFLOW_API_KEY",
        "base_url": "https://api.siliconflow.cn",
        "models": [
            "Qwen/Qwen2.5-7B-Instruct",
            "Qwen/Qwen2.5-Coder-7B-Instruct",
            "deepseek-ai/DeepSeek-V2.5",
        ],
        "enabled": True,
    },
    {
        "name": "ollama",
        "api_key": None,
        "base_url": "http://localhost:11434/v1",
        "models": ["llama2", "codellama", "mistral"],
        "enabled": False,  # Disabled by default since Kamatera is preferred
    },
]

# Default model configurations
DEFAULT_MODELS = {
    "gpt-4": {
        "provider": "openai",
        "max_tokens": 8000,
        "temperature": 0.7,
        "supports_streaming": True,
    },
    "gpt-3.5-turbo": {
        "provider": "openai",
        "max_tokens": 4000,
        "temperature": 0.7,
        "supports_streaming": True,
    },
    "claude-3-opus": {
        "provider": "anthropic",
        "max_tokens": 100000,
        "temperature": 0.7,
        "supports_streaming": True,
    },
    "phi3:latest": {
        "provider": "ollama_kamatera",
        "max_tokens": 4000,
        "temperature": 0.2,
        "supports_streaming": True,
    },
    "qwen2.5:latest": {
        "provider": "ollama_kamatera",
        "max_tokens": 4000,
        "temperature": 0.2,
        "supports_streaming": True,
    },
    "llama2": {
        "provider": "ollama",
        "max_tokens": 4000,
        "temperature": 0.8,
        "supports_streaming": True,
    },
}


def get_provider_settings() -> List[Dict[str, Any]]:
    """Get provider settings for monitoring"""
    return DEFAULT_PROVIDERS


def get_provider_config() -> Dict[str, Any]:
    """Get overall provider configuration"""
    return {
        "health_check_interval": 60,
        "timeout": 10,
        "retry_attempts": 3,
    }


def get_model_config(model_name: str) -> Dict[str, Any]:
    """Get configuration for a specific model"""
    return DEFAULT_MODELS.get(model_name, {})
