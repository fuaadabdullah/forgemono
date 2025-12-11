"""
Dual Model Adapter for GoblinOS Assistant mini
Orchestrates between Phi-3 local and Raptor hosted backends
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List

from .base import (
    ModelAdapter,
    ModelConfig,
    ModelResponse,
    ModelProvider,
    ModelAdapterError,
    ModelMetrics,
    ModelCapability,
)

logger = logging.getLogger(__name__)


class DualModelAdapter(ModelAdapter):
    """Orchestrates local Phi-3 model and hosted Raptor Mini API.

    Strategy:
    - In dev mode (phi_only): always use local Phi adapter
    - In raptor_only mode: always use Raptor API adapter
    - In dual mode: use Phi adapter for fast pass; if Phi score < auto_polish threshold, send to Raptor adapter
    """

    def __init__(
        self,
        config: ModelConfig,
        phi_adapter: ModelAdapter,
        raptor_adapter: ModelAdapter,
        auto_polish_threshold: float = 70.0,
        soft_fallback: bool = False,
    ):
        super().__init__(config)
        self.phi_adapter = phi_adapter
        self.raptor_adapter = raptor_adapter
        self.auto_polish_threshold = auto_polish_threshold
        self.mode = "dual"
        self.soft_fallback = soft_fallback

    async def initialize(self) -> bool:
        """Initialize both adapters, but do so concurrently to save time."""
        tasks = [self.phi_adapter.initialize(), self.raptor_adapter.initialize()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        ok = False
        for r in results:
            if isinstance(r, Exception):
                logger.warning(f"Adapter initialize exception: {r}")
            elif r:
                ok = True

        self._initialized = ok
        return ok

    async def _analyze_with_adapter(
        self,
        adapter: ModelAdapter,
        content: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> ModelResponse:
        """Call the adapter's generate and return the result."""
        try:
            return await adapter.generate(content, context, **kwargs)
        except ModelAdapterError as e:
            # Preserve ModelAdapterError behavior
            logger.warning(f"Adapter {adapter.provider.value} failed: {e}")
            raise
        except Exception as e:
            # Wrap any other exception into a ModelAdapterError so callers can handle it
            logger.warning(f"Adapter {adapter.provider.value} exception: {e}")
            raise ModelAdapterError(str(e), adapter.provider, recoverable=True)

    async def _extract_score(self, result: ModelResponse) -> Optional[float]:
        """Try to parse a score out of the result content or metadata.
        Convention: response.metadata['score'] or content contains 'Score: N/100'"""
        # Check metadata first
        try:
            if (
                result.metadata
                and isinstance(result.metadata, dict)
                and "score" in result.metadata
            ):
                return float(result.metadata.get("score"))
        except Exception:
            pass

        # Try to find score pattern in content
        try:
            content = result.content or ""
            import re

            m = re.search(r"Score[:\s]+(\d+(?:\.\d+)?)\/?100", content)
            if m:
                return float(m.group(1))
        except Exception:
            pass

        return None

    async def generate(
        self, prompt: str, context: Optional[Dict[str, Any]] = None, **kwargs
    ) -> ModelResponse:
        """Run the fast Phi adapter first and decide whether to polish it with Raptor."""
        if not self._initialized:
            raise ModelAdapterError("Dual adapter not initialized", self.provider)

        mode = context.get("mode") if context else None
        if mode is None:
            mode = self.config.model_name or "dual"

        # phi_only mode -> call phi adapter only
        if mode == "phi_only":
            logger.debug("Mode phi_only: using Phi adapter")
            # In phi_only mode, optionally allow soft fallback to Raptor
            try:
                if not getattr(self.phi_adapter, "is_initialized", False):
                    raise ModelAdapterError(
                        "Phi adapter is not initialized in phi_only mode",
                        self.provider,
                        recoverable=False,
                    )
                return await self._analyze_with_adapter(
                    self.phi_adapter, prompt, context, **kwargs
                )
            except ModelAdapterError:
                if self.soft_fallback:
                    logger.warning(
                        "Phi adapter error and soft_fallback enabled: using Raptor adapter"
                    )
                    return await self._analyze_with_adapter(
                        self.raptor_adapter, prompt, context, **kwargs
                    )
                raise

        # raptor_only mode -> call raptor adapter only
        if mode == "raptor_only":
            logger.debug("Mode raptor_only: using Raptor adapter")
            return await self._analyze_with_adapter(
                self.raptor_adapter, prompt, context, **kwargs
            )

        # default: dual mode
        logger.debug("Mode dual: running Phi then auto-polish if needed")
        phi_result = None
        try:
            phi_result = await self._analyze_with_adapter(
                self.phi_adapter, prompt, context, **kwargs
            )
        except ModelAdapterError:
            # If Phi failed, fall back to Raptor
            logger.warning("Phi adapter failed; falling back to Raptor")
            return await self._analyze_with_adapter(
                self.raptor_adapter, prompt, context, **kwargs
            )

        # Try to extract score
        score = await self._extract_score(phi_result)
        if score is None:
            # If no score is found, assume it's a draft; we can still decide to pass or polish.
            # Prefer to polish for higher quality by default
            logger.debug("No score found in phi result; defaulting to raptor polishing")
            return await self._analyze_with_adapter(
                self.raptor_adapter, prompt, context, **kwargs
            )

        # If score is below auto_polish threshold -> polish with Raptor
        if score < self.auto_polish_threshold:
            logger.debug(
                f"Phi score {score} < auto_polish_threshold {self.auto_polish_threshold}; polishing with Raptor"
            )
            raptor_result = await self._analyze_with_adapter(
                self.raptor_adapter, prompt, context, **kwargs
            )
            return raptor_result

        # Otherwise return phi result
        logger.debug(
            f"Phi score {score} >= auto_polish_threshold {self.auto_polish_threshold}; returning phi result"
        )
        return phi_result

    async def generate_code(
        self,
        task: str,
        language: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> ModelResponse:
        # Code generation: prefer Phi for dev iteration; polish via Raptor if score low
        prompt = f"Generate {language} code for task: {task}\n\nRequirements: {context.get('requirements') if context else ''}"
        return await self.generate(prompt, context, **kwargs)

    async def review_code(
        self,
        code: str,
        language: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> ModelResponse:
        # For reviews, prefer Raptor for quality, but phi may be used in dev mode
        mode = context.get("mode") if context else None
        if mode == "phi_only":
            return await self.phi_adapter.review_code(code, language, context, **kwargs)
        elif mode == "raptor_only":
            return await self.raptor_adapter.review_code(
                code, language, context, **kwargs
            )
        else:
            # Run phi quickly and if score is low, run Raptor
            phi_result = await self.phi_adapter.review_code(
                code, language, context, **kwargs
            )
            score = await self._extract_score(phi_result)
            if score is not None and score < self.auto_polish_threshold:
                return await self.raptor_adapter.review_code(
                    code, language, context, **kwargs
                )
            return phi_result

    async def health_check(self) -> bool:
        phi_ok = await self.phi_adapter.health_check()
        raptor_ok = await self.raptor_adapter.health_check()
        return phi_ok or raptor_ok

    async def cleanup(self) -> None:
        await asyncio.gather(self.phi_adapter.cleanup(), self.raptor_adapter.cleanup())
        self._initialized = False

    def get_dual_info(self) -> Dict[str, Any]:
        return {
            "provider": "dual",
            "phi_provider": self.phi_adapter.provider.value,
            "raptor_provider": self.raptor_adapter.provider.value,
            "auto_polish_threshold": self.auto_polish_threshold,
            "initialized": self._initialized,
        }
