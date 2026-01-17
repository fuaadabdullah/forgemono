#!/usr/bin/env python3
"""
Test Anthropic API directly to verify if it works
"""

import os
import asyncio
import aiohttp

async def test_anthropic():
    """Test Anthropic Claude API"""
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not found")
        return False
    
    print("✅ Anthropic API key found")
    
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01"
    }
    
    data = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 100,
        "messages": [
            {"role": "user", "content": "Hello! Please respond briefly."}
        ]
    }
    
    print("🧪 Testing Anthropic API...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=headers, json=data, timeout=30) as response:
                if response.status == 200:
                    result = await response.json()
                    message = result['content'][0]['text']
                    print("✅ Anthropic API Working!")
                    print(f"Response: {message}")
                    return True
                else:
                    text = await response.text()
                    print(f"❌ Anthropic API failed: {response.status}")
                    print(f"Error: {text}")
                    return False
        except Exception as e:
            print(f"❌ Anthropic API error: {e}")
            return False

if __name__ == "__main__":
    asyncio.run(test_anthropic())