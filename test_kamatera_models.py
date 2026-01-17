#!/usr/bin/env python3
"""
Kamatera Model Performance Testing Script
Purpose: Test and benchmark different models for specific use cases
"""

import asyncio
import aiohttp
import json
import time
import statistics
from typing import List, Dict, Any
import sys
import os

# Configuration
API_KEY = "206e61fdeda2267c9a4ecac3997c4eae7ebd20038282445f7524a84a78ac0158"
OLLAMA_SERVER = "http://192.175.23.150:8002"

# Test cases for different use cases
TEST_CASES = {
    "general_chat": {
        "prompt": "Hello! How are you today?",
        "model": "phi3:latest",
        "description": "General conversation test"
    },
    "coding": {
        "prompt": "Write a Python function to calculate fibonacci numbers",
        "model": "codellama:latest",
        "description": "Code generation test"
    },
    "reasoning": {
        "prompt": "If it takes 5 machines 5 minutes to make 5 widgets, how long would it take 100 machines to make 100 widgets?",
        "model": "llama3.1:latest",
        "description": "Logical reasoning test"
    },
    "fast_response": {
        "prompt": "What's 2+2?",
        "model": "qwen2.5:latest",
        "description": "Quick response test"
    }
}

class ModelTester:
    def __init__(self):
        self.results = []
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_model(self, model: str, prompt: str) -> Dict[str, Any]:
        """Test a single model with a prompt"""
        start_time = time.time()
        
        try:
            async with self.session.post(
                f"{OLLAMA_SERVER}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                },
                headers={"Authorization": f"Bearer {API_KEY}"},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                end_time = time.time()
                response_time = end_time - start_time
                
                if response.status == 200:
                    result = await response.json()
                    content = result.get("response", "")
                    tokens_per_second = len(content.split()) / response_time if response_time > 0 else 0
                    
                    return {
                        "model": model,
                        "prompt": prompt,
                        "response": content,
                        "response_time": response_time,
                        "tokens_per_second": tokens_per_second,
                        "status": "success",
                        "error": None
                    }
                else:
                    return {
                        "model": model,
                        "prompt": prompt,
                        "response": "",
                        "response_time": response_time,
                        "tokens_per_second": 0,
                        "status": "error",
                        "error": f"HTTP {response.status}"
                    }
                    
        except asyncio.TimeoutError:
            return {
                "model": model,
                "prompt": prompt,
                "response": "",
                "response_time": 30.0,
                "tokens_per_second": 0,
                "status": "timeout",
                "error": "Request timed out"
            }
        except Exception as e:
            return {
                "model": model,
                "prompt": prompt,
                "response": "",
                "response_time": time.time() - start_time,
                "tokens_per_second": 0,
                "status": "error",
                "error": str(e)
            }
    
    async def test_all_models(self):
        """Test all configured models"""
        print("🔬 Starting Kamatera Model Performance Testing")
        print("=" * 50)
        
        # Get available models from server
        try:
            async with self.session.get(f"{OLLAMA_SERVER}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    available_models = [model["name"] for model in data.get("models", [])]
                else:
                    print(f"❌ Failed to get models: {response.status}")
                    return
        except Exception as e:
            print(f"❌ Error getting models: {e}")
            return
        
        print(f"📊 Found {len(available_models)} available models:")
        for model in available_models:
            print(f"   - {model}")
        print()
        
        # Test each model with different use cases
        for test_case_name, test_case in TEST_CASES.items():
            print(f"🧪 Testing: {test_case['description']}")
            print(f"Prompt: {test_case['prompt'][:50]}...")
            
            # Filter available models
            relevant_models = [
                model for model in available_models 
                if any(keyword in model for keyword in ["phi3", "gemma2", "qwen2.5", "codellama", "mistral", "llama3.1"])
            ]
            
            if not relevant_models:
                print("   ⚠️ No relevant models found")
                continue
            
            # Test each relevant model
            test_results = []
            for model in relevant_models[:3]:  # Test top 3 models
                print(f"   Testing {model}...", end=" ", flush=True)
                result = await self.test_model(model, test_case['prompt'])
                test_results.append(result)
                
                if result['status'] == 'success':
                    print(f"✅ {result['response_time']:.2f}s ({result['tokens_per_second']:.1f} t/s)")
                else:
                    print(f"❌ {result['error']}")
            
            # Store results
            self.results.append({
                'test_case': test_case_name,
                'description': test_case['description'],
                'results': test_results
            })
            
            # Small delay between tests
            await asyncio.sleep(1)
            print()
    
    def generate_report(self):
        """Generate performance report"""
        print("\n📊 Model Performance Report")
        print("=" * 50)
        
        for test_case_data in self.results:
            print(f"\n🎯 {test_case_data['description']}")
            print("-" * 30)
            
            successful_results = [
                r for r in test_case_data['results'] 
                if r['status'] == 'success'
            ]
            
            if not successful_results:
                print("   ❌ No successful tests")
                continue
            
            # Sort by response time
            successful_results.sort(key=lambda x: x['response_time'])
            
            print(f"   {'Model':<25} {'Time (s)':<10} {'Speed (t/s)':<12} {'Quality':<10}")
            print("   " + "-" * 55)
            
            for result in successful_results:
                quality = self._assess_quality(result)
                print(f"   {result['model']:<25} {result['response_time']:<10.2f} "
                      f"{result['tokens_per_second']:<12.1f} {quality:<10}")
    
    def _assess_quality(self, result: Dict[str, Any]) -> str:
        """Assess response quality based on content"""
        content = result.get('response', '').lower()
        
        if len(content) < 10:
            return "Poor"
        elif len(content) < 50:
            return "Fair"
        elif "error" in content or "sorry" in content:
            return "Fair"
        else:
            return "Good"
    
    def save_results(self, filename="kamatera_model_test_results.json"):
        """Save test results to file"""
        with open(filename, 'w') as f:
            json.dump({
                "timestamp": time.time(),
                "server": OLLAMA_SERVER,
                "results": self.results
            }, f, indent=2)
        print(f"💾 Results saved to {filename}")
    
    async def run_comprehensive_test(self):
        """Run comprehensive model testing"""
        await self.test_all_models()
        self.generate_report()
        self.save_results()

async def main():
    """Main testing function"""
    print("🚀 Kamatera Model Performance Testing Suite")
    print("Testing models for optimal use case assignment")
    print()
    
    async with ModelTester() as tester:
        await tester.run_comprehensive_test()
    
    print("\n🎉 Testing complete!")
    print("\n📋 Recommendations:")
    print("1. Use phi3:latest for fast general chat")
    print("2. Use codellama:latest for code generation")
    print("3. Use llama3.1:latest for complex reasoning")
    print("4. Use qwen2.5:latest for balanced performance")

if __name__ == "__main__":
    asyncio.run(main())