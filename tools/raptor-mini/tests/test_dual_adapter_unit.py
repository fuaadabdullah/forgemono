from typing import Optional

import pytest
import sys
import os

# Ensure local raptor-mini package is importable for tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from raptor_adapter.base import ModelAdapter, ModelConfig, ModelResponse, ModelProvider
from raptor_adapter.dual_model_adapter import DualModelAdapter


class FakePhiAdapter(ModelAdapter):
    def __init__(
        self,
        config: ModelConfig,
        score: Optional[float] = None,
        raise_on_generate: bool = False,
    ):
        super().__init__(config)
        self._score = score
        self._raise = raise_on_generate

    async def initialize(self) -> bool:
        self._initialized = True
        return True

    async def generate(self, prompt: str, context=None, **kwargs) -> ModelResponse:
        if self._raise:
            raise Exception("Phi adapter failed on purpose")
        content = (
            f"Phi generated content. Score: {self._score}/100"
            if self._score is not None
            else "Phi generated content"
        )
        return ModelResponse(
            content=content,
            provider=ModelProvider.LOCAL_LLAMA,
            model_name=self.config.model_name,
            metadata={"score": self._score} if self._score is not None else None,
        )

    async def generate_code(self, task: str, language: str, context=None, **kwargs):
        return await self.generate(task, context)

    async def review_code(self, code: str, language: str, context=None, **kwargs):
        return await self.generate(code, context)

    async def health_check(self) -> bool:
        return True

    async def cleanup(self) -> None:
        self._initialized = False


class FakeRaptorAdapter(ModelAdapter):
    def __init__(self, config: ModelConfig, score: Optional[float] = None):
        super().__init__(config)
        self._score = score

    async def initialize(self) -> bool:
        self._initialized = True
        return True

    async def generate(self, prompt: str, context=None, **kwargs) -> ModelResponse:
        content = (
            f"Raptor generated content. Score: {self._score}/100"
            if self._score is not None
            else "Raptor generated content"
        )
        return ModelResponse(
            content=content,
            provider=ModelProvider.RAPTOR_API,
            model_name=self.config.model_name,
            metadata={"score": self._score} if self._score is not None else None,
        )

    async def generate_code(self, task: str, language: str, context=None, **kwargs):
        return await self.generate(task, context)

    async def review_code(self, code: str, language: str, context=None, **kwargs):
        return await self.generate(code, context)

    async def health_check(self) -> bool:
        return True

    async def cleanup(self) -> None:
        self._initialized = False


@pytest.mark.asyncio
async def test_phi_success_no_polish():
    phi_cfg = ModelConfig(provider=ModelProvider.LOCAL_LLAMA, model_name="phi-test")
    raptor_cfg = ModelConfig(
        provider=ModelProvider.RAPTOR_API, model_name="raptor-test"
    )
    phi_adapter = FakePhiAdapter(phi_cfg, score=85)
    raptor_adapter = FakeRaptorAdapter(raptor_cfg, score=90)
    dual = DualModelAdapter(
        ModelConfig(provider=ModelProvider.FALLBACK, model_name="dual"),
        phi_adapter,
        raptor_adapter,
        auto_polish_threshold=70.0,
    )
    await dual.initialize()
    res = await dual.generate("Test doc", context={"mode": "dual"})
    assert res.provider == ModelProvider.LOCAL_LLAMA
    assert "Phi generated content" in res.content


@pytest.mark.asyncio
async def test_phi_low_polish_to_raptor():
    phi_cfg = ModelConfig(provider=ModelProvider.LOCAL_LLAMA, model_name="phi-low")
    raptor_cfg = ModelConfig(
        provider=ModelProvider.RAPTOR_API, model_name="raptor-high"
    )
    phi_adapter = FakePhiAdapter(phi_cfg, score=45)
    raptor_adapter = FakeRaptorAdapter(raptor_cfg, score=92)
    dual = DualModelAdapter(
        ModelConfig(provider=ModelProvider.FALLBACK, model_name="dual"),
        phi_adapter,
        raptor_adapter,
        auto_polish_threshold=70.0,
    )
    await dual.initialize()
    res = await dual.generate("Test doc", context={"mode": "dual"})
    # Expect raptor returned due to polish
    assert res.provider == ModelProvider.RAPTOR_API
    assert "Raptor generated content" in res.content


@pytest.mark.asyncio
async def test_phi_failure_soft_fallback_enabled():
    phi_cfg = ModelConfig(provider=ModelProvider.LOCAL_LLAMA, model_name="phi-fail")
    raptor_cfg = ModelConfig(
        provider=ModelProvider.RAPTOR_API, model_name="raptor-fallback"
    )
    phi_adapter = FakePhiAdapter(phi_cfg, raise_on_generate=True)
    raptor_adapter = FakeRaptorAdapter(raptor_cfg, score=88)
    dual = DualModelAdapter(
        ModelConfig(provider=ModelProvider.FALLBACK, model_name="dual"),
        phi_adapter,
        raptor_adapter,
        soft_fallback=True,
    )
    await dual.initialize()
    res = await dual.generate("Test doc", context={"mode": "phi_only"})
    assert res.provider == ModelProvider.RAPTOR_API
    assert "Raptor generated content" in res.content


@pytest.mark.asyncio
async def test_phi_failure_soft_fallback_disabled_raises():
    phi_cfg = ModelConfig(provider=ModelProvider.LOCAL_LLAMA, model_name="phi-fail2")
    raptor_cfg = ModelConfig(
        provider=ModelProvider.RAPTOR_API, model_name="raptor-fallback2"
    )
    phi_adapter = FakePhiAdapter(phi_cfg, raise_on_generate=True)
    raptor_adapter = FakeRaptorAdapter(raptor_cfg, score=88)
    dual = DualModelAdapter(
        ModelConfig(provider=ModelProvider.FALLBACK, model_name="dual"),
        phi_adapter,
        raptor_adapter,
        soft_fallback=False,
    )
    await dual.initialize()
    with pytest.raises(Exception):
        await dual.generate("Test doc", context={"mode": "phi_only"})
