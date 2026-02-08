"""
Stub implementation of ProviderScorer used for routing tests.
"""

from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ProviderScorer:
    async def score_providers(
        self,
        candidates: List[Dict[str, Any]],
        capability: str,
        requirements: Optional[Dict[str, Any]] = None,
        sla_target_ms: Optional[float] = None,
        cost_budget: Optional[float] = None,
        latency_priority: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Return candidates unchanged with a default score so downstream selection can proceed.
        """
        for candidate in candidates:
            candidate.setdefault("score", 1.0)
        logger.debug(
            "ProviderScorer.score_providers called (stub) for %s with %d candidates",
            capability,
            len(candidates),
        )
        return candidates
