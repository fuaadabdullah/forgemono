import os
import importlib.util
import asyncio
from typing import Optional

import pytest

sys_path_idx = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "raptor-mini")
)
import sys

sys.path.insert(0, sys_path_idx)

from raptor_adapter.base import ModelAdapter, ModelConfig, ModelResponse, ModelProvider
from raptor_adapter.dual_model_adapter import DualModelAdapter

# Import DOC checker via importlib like previous test
doc_quality_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "doc_quality_check.py")
)
spec = importlib.util.spec_from_file_location("doc_quality_check", doc_quality_path)
doc_quality_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(doc_quality_mod)
DocQualityChecker = doc_quality_mod.DocQualityChecker


class SimplePhi(ModelAdapter):
    async def initialize(self) -> bool:
        self._initialized = True
        return True

    async def generate(self, prompt: str, context=None, **kwargs) -> ModelResponse:
        return ModelResponse(
            content="Phi content. Score: 77/100",
            provider=ModelProvider.LOCAL_LLAMA,
            model_name="phi-simple",
            metadata={"score": 77},
        )

    async def generate_code(self, task: str, language: str, context=None, **kwargs):
        return await self.generate(task)

    async def review_code(self, code: str, language: str, context=None, **kwargs):
        return await self.generate(code)

    async def health_check(self) -> bool:
        return True

    async def cleanup(self) -> None:
        self._initialized = False


class SimpleRaptor(ModelAdapter):
    async def initialize(self) -> bool:
        self._initialized = True
        return True

    async def generate(self, prompt: str, context=None, **kwargs) -> ModelResponse:
        return ModelResponse(
            content="Raptor content. Score: 90/100",
            provider=ModelProvider.RAPTOR_API,
            model_name="raptor-simple",
            metadata={"score": 90},
        )

    async def generate_code(self, task: str, language: str, context=None, **kwargs):
        return await self.generate(task)

    async def review_code(self, code: str, language: str, context=None, **kwargs):
        return await self.generate(code)

    async def health_check(self) -> bool:
        return True

    async def cleanup(self) -> None:
        self._initialized = False


def test_batch_analysis_with_dual_adapter(tmp_path):
    # Create sample doc file
    file_path = tmp_path / "sample_doc.md"
    file_path.write_text("This is a test doc to validate E2E behavior")

    phi_cfg = ModelConfig(provider=ModelProvider.LOCAL_LLAMA, model_name="phi-e2e")
    raptor_cfg = ModelConfig(provider=ModelProvider.RAPTOR_API, model_name="raptor-e2e")
    phi_adapter = SimplePhi(phi_cfg)
    raptor_adapter = SimpleRaptor(raptor_cfg)
    dual = DualModelAdapter(
        ModelConfig(provider=ModelProvider.FALLBACK, model_name="dual"),
        phi_adapter,
        raptor_adapter,
        auto_polish_threshold=70,
    )
    asyncio.run(dual.initialize())

    checker = DocQualityChecker(api_url="http://localhost:8000", mode="dual")
    checker.set_adapter_engine(dual)

    results = checker.batch_analyze([str(file_path)])
    assert isinstance(results, list)
    assert len(results) == 1
    res = results[0]
    assert res.get("filename") == "sample_doc.md"
    assert res.get("score") == 77
    assert res.get("provider") == ModelProvider.LOCAL_LLAMA
