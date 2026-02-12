#!/usr/bin/env python3
"""
Test TinyLlama adapter directly
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from providers.tinylama_adapter import TinyLlamaAdapter


async def test_tinylama():
    """Test TinyLlama adapter."""
    print("🧪 Testing TinyLlama Adapter\n")

    try:
        # Create adapter
        adapter = TinyLlamaAdapter()

        # Test basic functionality
        print("📦 Testing model loading...")
        await adapter._ensure_model_loaded()
        print("✅ Model loaded successfully")

        # Test chat completion
        print("\n💬 Testing chat completion...")
        messages = [{"role": "user", "content": "Hello, how are you?"}]

        result = await adapter.chat("tinylama-1.1b-chat", messages, max_tokens=50)
        print(f"✅ Chat completion successful: {len(result.get('content', ''))} chars")

        # Test async generation
        print("\n⚡ Testing async generation...")
        async_result = await adapter.a_generate(
            model="tinylama-1.1b-chat", messages=messages, max_tokens=20
        )
        print(
            f"✅ Async generation successful: {len(async_result.get('content', ''))} chars"
        )

        print("\n🎉 All TinyLlama tests passed!")

    except Exception as e:
        print(f"❌ TinyLlama test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_tinylama())
