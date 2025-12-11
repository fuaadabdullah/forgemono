#!/usr/bin/env python3
"""Smoke test for DualModelAdapter imports and minimal behavior"""

import sys
import os
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))
from raptor_adapter import (
    LocalModelAdapter,
    RaptorApiAdapter,
    DualModelAdapter,
    ModelConfig,
    ModelProvider,
)


class FakeFailAdapter(LocalModelAdapter):
    async def initialize(self) -> bool:
        return False

    async def generate(self, content: str, context=None, **kwargs):
        raise Exception("intentional fail")


class FakeSuccessAdapter(RaptorApiAdapter):
    async def initialize(self) -> bool:
        self._initialized = True
        return True

    async def generate(self, content: str, context=None, **kwargs):
        class R:
            content = "Fake success content. Score: 85/100"
            provider = "raptor_fake"
            model_name = "raptor_fake"
            metadata = {"score": 85}

        return R()


async def main():
    phi_cfg = ModelConfig(
        provider=ModelProvider.LOCAL_LLAMA, model_name="/tmp/nonexistent_model"
    )
    raptor_cfg = ModelConfig(
        provider=ModelProvider.RAPTOR_API,
        model_name="raptor-mini",
        base_url="http://localhost:8000",
    )

    # Use fakes to exercise soft_fallback behavior
    phi_adapter = FakeFailAdapter(phi_cfg)
    raptor_adapter = FakeSuccessAdapter(raptor_cfg)
    dual = DualModelAdapter(
        ModelConfig(provider=ModelProvider.FALLBACK, model_name="dual"),
        phi_adapter,
        raptor_adapter,
        soft_fallback=True,
    )

    print("DualModelAdapter created. Initializing adapters with soft_fallback=True...")
    await dual.initialize()
    print("Health check before generate:", await dual.health_check())
    result = await dual.generate(
        "A test document to analyze", context={"mode": "phi_only"}
    )
    print(
        "Generated content provider:",
        getattr(
            result,
            "provider",
            result.get("provider") if isinstance(result, dict) else None,
        ),
    )
    print("Generated content summary:", getattr(result, "content", None))
    await dual.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
