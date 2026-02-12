"""Analysis adapters for different analysis methods"""

from typing import Optional
from .base import Adapter
from .copilot_proxy import CopilotProxyAdapter
from .heuristic_adapter import HeuristicAdapter

# Conditionally import LocalModelAdapter to avoid torch/NumPy issues in development
try:
    from .local_model import LocalModelAdapter

    LOCAL_MODEL_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Local model adapter not available: {e}")
    LocalModelAdapter = None
    LOCAL_MODEL_AVAILABLE = False

try:
    from .queued_local_model import QueuedLocalModelAdapter

    QUEUED_MODEL_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Queued local model adapter not available: {e}")
    QueuedLocalModelAdapter = None
    QUEUED_MODEL_AVAILABLE = False


def get_adapter(method: str) -> Optional[Adapter]:
    """Factory function to get the appropriate adapter"""
    adapters = {
        "local_llm": LocalModelAdapter,
        "copilot_proxy": CopilotProxyAdapter,
        "heuristic": HeuristicAdapter,
    }

    adapter_class = adapters.get(method)
    if adapter_class:
        return adapter_class()

    return None
