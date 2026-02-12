"""
Stub implementation of ProviderSelector for routing unit tests.
"""

from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ProviderSelector:
    async def select_best_provider(
        self, scored_providers: List[Dict[str, Any]], requirements: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Select the top-scoring provider. Falls back to the first entry.
        """
        if not scored_providers:
            raise ValueError("No providers to select from")
        # Assume providers are pre-sorted by score
        selection = scored_providers[0]
        logger.debug(
            "ProviderSelector.select_best_provider called (stub); returning %s",
            selection.get("name", selection),
        )
        return selection
