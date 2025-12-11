"""
Provider adapters for external AI services.
"""

# Import base adapter first
from .base_adapter import AdapterBase, ProviderError

# Import adapters with error handling for optional dependencies
try:
    from .openai_adapter import OpenAIAdapter
except ImportError:
    OpenAIAdapter = None

try:
    from .anthropic_adapter import AnthropicAdapter
except ImportError:
    AnthropicAdapter = None

try:
    from .gemini_adapter import GeminiAdapter
except ImportError:
    GeminiAdapter = None

try:
    from .grok_adapter import GrokAdapter
except ImportError:
    GrokAdapter = None

try:
    from .deepseek_adapter import DeepSeekAdapter
except ImportError:
    DeepSeekAdapter = None

try:
    from .ollama_adapter import OllamaAdapter
except ImportError:
    OllamaAdapter = None

__all__ = [
    "AdapterBase",
    "ProviderError",
    "OpenAIAdapter",
    "AnthropicAdapter",
    "GeminiAdapter",
    "GrokAdapter",
    "DeepSeekAdapter",
    "OllamaAdapter",
]
from .llamacpp_adapter import LlamaCppAdapter
from .silliconflow_adapter import SilliconflowAdapter
from .moonshot_adapter import MoonshotAdapter
from .elevenlabs_adapter import ElevenLabsAdapter

__all__ = [
    "OpenAIAdapter",
    "AnthropicAdapter",
    "GeminiAdapter",
    "GrokAdapter",
    "DeepSeekAdapter",
    "OllamaAdapter",
    "LlamaCppAdapter",
    "SilliconflowAdapter",
    "MoonshotAdapter",
    "ElevenLabsAdapter",
]
