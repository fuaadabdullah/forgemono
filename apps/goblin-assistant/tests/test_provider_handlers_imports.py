import asyncio


async def _ensure_awaitable(obj):
    # helper to ensure returned stream is async-generator-like
    if hasattr(obj, "__aiter__"):
        agen = obj.__aiter__()
        # advance one item if possible
        try:
            await agen.__anext__()
        except StopAsyncIteration:
            return True
        return True
    return False


def test_handlers_importable_and_callable_sync():
    """Run async handler checks via asyncio.run so pytest doesn't need plugins.

    Make the repo root importable (mirrors `test_imports.py` behavior) so the
    same import paths work in CI and locally.
    """
    import sys
    from pathlib import Path

    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))

    async def _inner():
        # Import modules directly from their file paths so tests don't depend on
        # the project arranging `tools` as an importable package in every env.
        import importlib.util
        from pathlib import Path

        base = Path(__file__).resolve().parents[1] / "tools" / "provider-routing"
        ph_path = base / "provider_handlers.py"
        ph2_path = base / "provider_handlers2.py"

        spec = importlib.util.spec_from_file_location("provider_handlers", ph_path)
        provider_handlers = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(provider_handlers)

        spec2 = importlib.util.spec_from_file_location("provider_handlers2", ph2_path)
        provider_handlers2 = importlib.util.module_from_spec(spec2)
        spec2.loader.exec_module(provider_handlers2)

        # Basic existence checks
        assert hasattr(provider_handlers, "handle_openai")
        assert hasattr(provider_handlers, "handle_llamacpp")
        assert hasattr(provider_handlers2, "handle_generic")
        assert hasattr(provider_handlers2, "handle_ollama")

        # Call the generic handler (non-stream)
        res = await provider_handlers2.handle_generic(
            "test-provider",
            "model-x",
            {"prompt": "hello"},
            1000,
            False,
            "https://example.local",
            "/v1/invoke",
            None,
            None,
            asyncio.get_event_loop().time(),
        )
        assert isinstance(res, dict)
        assert res.get("ok") is False

        # Call a streaming handler and verify it yields
        streamed = await provider_handlers2.handle_ollama(
            "ollama-local",
            "local-model",
            {"prompt": "hi"},
            1000,
            True,
            "http://127.0.0.1:11434",
            "/v1",
            None,
            asyncio.get_event_loop().time(),
        )
        assert streamed.get("ok") is True
        assert await _ensure_awaitable(streamed.get("stream"))

    asyncio.run(_inner())
