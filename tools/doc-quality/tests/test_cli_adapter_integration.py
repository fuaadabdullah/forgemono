import sys
import os
from typing import Optional


sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "raptor-mini")),
)
import importlib.util

from raptor_adapter.base import ModelAdapter, ModelConfig, ModelResponse, ModelProvider
from raptor_adapter.dual_model_adapter import DualModelAdapter

# Import DocQualityChecker using importlib because tools/doc-quality is not a package (directory has a hyphen)
doc_quality_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "doc_quality_check.py")
)
spec = importlib.util.spec_from_file_location("doc_quality_check", doc_quality_path)
doc_quality_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(doc_quality_mod)
DocQualityChecker = doc_quality_mod.DocQualityChecker


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
            raise Exception("Phi failed for test")
        return ModelResponse(
            content=f"Phi test content. Score: {self._score}/100"
            if self._score is not None
            else "Phi test content",
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
        return ModelResponse(
            content=f"Raptor test content. Score: {self._score}/100"
            if self._score is not None
            else "Raptor test content",
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


def test_cli_analyze_content_with_adapter_engine():
    # Set up fake adapters and dual engine
    phi_cfg = ModelConfig(provider=ModelProvider.LOCAL_LLAMA, model_name="phi-test")
    raptor_cfg = ModelConfig(
        provider=ModelProvider.RAPTOR_API, model_name="raptor-test"
    )
    phi_adapter = FakePhiAdapter(phi_cfg, score=86)
    raptor_adapter = FakeRaptorAdapter(raptor_cfg, score=92)
    dual = DualModelAdapter(
        ModelConfig(provider=ModelProvider.FALLBACK, model_name="dual"),
        phi_adapter,
        raptor_adapter,
        auto_polish_threshold=70.0,
    )
    import asyncio

    asyncio.run(dual.initialize())

    checker = DocQualityChecker(api_url="http://localhost:8000", mode="dual")
    # Use our dual engine instead of initializing via _init_adapter_engine
    checker.set_adapter_engine(dual)

    result = checker.analyze_content("Sample doc content", filename="test.md")
    assert isinstance(result, dict)
    # By default, dual mode should use phi and return phi since score 86 > 70
    assert result.get("provider") == ModelProvider.LOCAL_LLAMA
    assert result.get("score") == 86


def test_cli_phi_only_soft_fallback_enabled():
    phi_cfg = ModelConfig(provider=ModelProvider.LOCAL_LLAMA, model_name="phi-fail")
    raptor_cfg = ModelConfig(
        provider=ModelProvider.RAPTOR_API, model_name="raptor-fallback"
    )
    phi_adapter = FakePhiAdapter(phi_cfg, raise_on_generate=True)
    raptor_adapter = FakeRaptorAdapter(raptor_cfg, score=80)
    dual = DualModelAdapter(
        ModelConfig(provider=ModelProvider.FALLBACK, model_name="dual"),
        phi_adapter,
        raptor_adapter,
        soft_fallback=True,
    )
    import asyncio

    asyncio.run(dual.initialize())

    checker = DocQualityChecker(api_url="http://localhost:8000", mode="phi_only")
    checker.set_adapter_engine(dual)
    result = checker.analyze_content("Sample doc content", filename="test2.md")
    assert isinstance(result, dict)
    # Because phi adapter fails and soft_fallback=True, we expect raptor adapter results
    assert result.get("provider") == ModelProvider.RAPTOR_API
    assert result.get("score") == 80
