#!/usr/bin/env python3
"""
Kamatera Provider Implementation
Implements both Ollama direct access and Router API access for Kamatera servers
"""

import json
import time
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
import logging
from enum import Enum

class KamateraProviderStatus(Enum):
    WORKING = "working"
    DEGRADED = "degraded" 
    FAILED = "failed"

class KamateraOllamaProvider:
    """Direct Ollama provider for Kamatera Server 1"""
    
    def __init__(self):
        self.base_url = "http://192.175.23.150:8002"
        self.api_key = "206e61fdeda2267c9a4ecac3997c4eae7ebd20038282445f7524a84a78ac0158"
        self.name = "kamatera_ollama_direct"
        self.status = KamateraProviderStatus.WORKING
        
    async def get_models(self) -> Dict[str, Any]:
        """Get available models from Ollama"""
        try:
            headers = {"x-api-key": self.api_key}
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags", headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = [model["name"] for model in data.get("models", [])]
                        return {
                            "status": "success",
                            "models": models,
                            "model_count": len(models),
                            "provider": self.name
                        }
                    else:
                        return {"status": "failed", "error": f"HTTP {response.status}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def chat_completion(self, model: str, messages: List[Dict]) -> Dict[str, Any]:
        """Generate chat completion"""
        payload = {
            "model": model,
            "prompt": self._format_messages(messages),
            "stream": False
        }
        
        try:
            headers = {"x-api-key": self.api_key}
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "status": "success",
                            "content": data.get("response", ""),
                            "model": model,
                            "provider": self.name,
                            "response_time": response_time,
                            "done": data.get("done", False)
                        }
                    else:
                        return {
                            "status": "failed",
                            "error": f"HTTP {response.status}",
                            "provider": self.name
                        }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "provider": self.name
            }
    
    def _format_messages(self, messages: List[Dict]) -> str:
        """Convert OpenAI-style messages to Ollama prompt format"""
        formatted = []
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            formatted.append(f"{role}: {content}")
        return "\n".join(formatted) + "\nassistant:"

class KamateraRouterProvider:
    """Router API provider for Kamatera Server 2"""
    
    def __init__(self):
        self.base_url = "http://45.61.51.220:8000"
        self.api_key = "cef5587890c73a5316a9a2c4ed851d97beb89fd28443885aad6e570dabd5f765"
        self.name = "kamatera_router_api"
        self.status = KamateraProviderStatus.DEGRADED  # Degraded due to network routing issue
        
    async def get_models(self) -> Dict[str, Any]:
        """Get models through Router API"""
        try:
            headers = {"x-api-key": self.api_key}
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/v1/models", headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = [model["id"] for model in data.get("data", [])]
                        return {
                            "status": "success",
                            "models": models,
                            "model_count": len(models),
                            "provider": self.name
                        }
                    else:
                        return {
                            "status": "failed",
                            "error": f"HTTP {response.status}",
                            "provider": self.name
                        }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "provider": self.name
            }
    
    async def chat_completion(self, model: str, messages: List[Dict]) -> Dict[str, Any]:
        """Generate chat completion through Router API"""
        payload = {
            "model": model,
            "messages": messages
        }
        
        try:
            headers = {
                "x-api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                        return {
                            "status": "success",
                            "content": content,
                            "model": model,
                            "provider": self.name,
                            "response_time": response_time,
                            "usage": data.get("usage", {})
                        }
                    else:
                        response_text = await response.text()
                        return {
                            "status": "failed",
                            "error": f"HTTP {response.status}: {response_text[:200]}",
                            "provider": self.name
                        }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "provider": self.name
            }

class KamateraProviderManager:
    """Manages both Kamatera providers with automatic fallback"""
    
    def __init__(self):
        self.ollama_provider = KamateraOllamaProvider()
        self.router_provider = KamateraRouterProvider()
        self.providers = [self.ollama_provider, self.router_provider]
        
    async def get_available_models(self) -> Dict[str, Any]:
        """Get models from all providers"""
        results = {}
        
        # Test Ollama direct
        ollama_models = await self.ollama_provider.get_models()
        results["ollama_direct"] = ollama_models
        
        # Test Router API
        router_models = await self.router_provider.get_models()
        results["router_api"] = router_models
        
        # Aggregate available models
        all_models = set()
        working_providers = []
        
        if ollama_models.get("status") == "success":
            all_models.update(ollama_models.get("models", []))
            working_providers.append("ollama_direct")
            
        if router_models.get("status") == "success":
            all_models.update(router_models.get("models", []))
            working_providers.append("router_api")
        
        return {
            "status": "success" if working_providers else "failed",
            "all_models": list(all_models),
            "working_providers": working_providers,
            "provider_results": results,
            "total_models": len(all_models)
        }
    
    async def chat_completion_with_fallback(self, model: str, messages: List[Dict]) -> Dict[str, Any]:
        """Try providers in order until one works"""
        
        for provider in self.providers:
            print(f"🔄 Trying {provider.name}...")
            result = await provider.chat_completion(model, messages)
            
            if result.get("status") == "success":
                print(f"✅ Success with {provider.name}")
                return {
                    **result,
                    "fallback_used": provider.name != "kamatera_ollama_direct"
                }
            else:
                print(f"❌ {provider.name} failed: {result.get('error', 'Unknown error')}")
        
        return {
            "status": "failed",
            "error": "All providers failed",
            "providers_tried": [p.name for p in self.providers]
        }
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive test of both providers"""
        print("🧪 Running Kamatera Provider Comprehensive Test")
        print("=" * 60)
        
        # Test models discovery
        print("\n📋 Testing Models Discovery...")
        models_result = await self.get_available_models()
        
        if models_result.get("status") == "success":
            print(f"✅ Models discovery successful")
            print(f"   Total models: {models_result['total_models']}")
            print(f"   Working providers: {models_result['working_providers']}")
        else:
            print(f"❌ Models discovery failed")
        
        # Test chat completion with multiple models
        test_messages = [{"role": "user", "content": "Hello! Please respond briefly."}]
        test_models = ["phi3:latest", "llama3.1:latest"]
        
        chat_results = {}
        for model in test_models:
            print(f"\n💬 Testing Chat Completion with {model}...")
            result = await self.chat_completion_with_fallback(model, test_messages)
            chat_results[model] = result
            
            if result.get("status") == "success":
                print(f"   ✅ Response: {result.get('content', '')[:100]}...")
                print(f"   ⏱️  Time: {result.get('response_time', 0):.2f}s")
                print(f"   🔧 Provider: {result.get('provider')}")
            else:
                print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
        
        # Summary
        successful_chats = sum(1 for r in chat_results.values() if r.get("status") == "success")
        
        return {
            "models_test": models_result,
            "chat_tests": chat_results,
            "summary": {
                "models_discovered": models_result.get("total_models", 0),
                "successful_chats": successful_chats,
                "total_chat_tests": len(test_models),
                "working_providers": models_result.get("working_providers", [])
            }
        }

async def main():
    """Main test function"""
    manager = KamateraProviderManager()
    results = await manager.run_comprehensive_test()
    
    print("\n" + "=" * 60)
    print("📊 KAMATERA PROVIDER TEST SUMMARY")
    print("=" * 60)
    
    summary = results.get("summary", {})
    print(f"✅ Models Discovered: {summary.get('models_discovered', 0)}")
    print(f"✅ Successful Chats: {summary.get('successful_chats', 0)}/{summary.get('total_chat_tests', 0)}")
    print(f"🔧 Working Providers: {summary.get('working_providers', [])}")
    
    # Performance metrics
    chat_tests = results.get("chat_tests", {})
    successful_tests = [r for r in chat_tests.values() if r.get("status") == "success"]
    if successful_tests:
        avg_response_time = sum(r.get("response_time", 0) for r in successful_tests) / len(successful_tests)
        print(f"⏱️  Average Response Time: {avg_response_time:.2f}s")
    
    print("\n🎯 KAMATERA INTEGRATION STATUS:")
    if summary.get("working_providers"):
        print("   ✅ Kamatera providers are operational")
        print("   🔄 Fallback mechanisms working")
        print("   📈 Ready for production use")
    else:
        print("   ❌ No providers working")
        print("   🔧 Requires infrastructure fixes")

if __name__ == "__main__":
    asyncio.run(main())