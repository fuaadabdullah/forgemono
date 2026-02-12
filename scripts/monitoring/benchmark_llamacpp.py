#!/usr/bin/env python3
"""
LLM Benchmarking Script for llama.cpp Server

This script benchmarks latency and throughput for different model configurations
running on a llama.cpp server. It tests various thread counts and measures:
- First token latency
- Token generation speed (tokens/second)
- Total response time
- Memory usage (if available)

Usage:
    python3 benchmark_llamacpp.py --server-url http://localhost:8080 --model tinyllama --threads 1,2,4,8

Requirements:
    pip install requests psutil
"""

import argparse
import time
import requests
import json
import statistics
import psutil
from typing import Dict, List, Optional
import sys


class LlamaCppBenchmark:
    def __init__(self, server_url: str = "http://localhost:8080"):
        self.server_url = server_url.rstrip("/")
        self.completions_url = f"{self.server_url}/completion"
        self.health_url = f"{self.server_url}/health"

    def check_server_health(self) -> bool:
        """Check if the llama.cpp server is running and healthy."""
        try:
            response = requests.get(self.health_url, timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def get_server_info(self) -> Optional[Dict]:
        """Get server information and model details."""
        try:
            response = requests.get(f"{self.server_url}/props", timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None

    def benchmark_completion(
        self,
        prompt: str,
        max_tokens: int = 50,
        temperature: float = 0.7,
        threads: int = 4,
        n_runs: int = 3,
    ) -> Dict:
        """
        Benchmark a single completion request.

        Returns metrics for latency, throughput, and memory usage.
        """
        payload = {
            "prompt": prompt,
            "n_predict": max_tokens,
            "temperature": temperature,
            "threads": threads,
            "stream": False,
        }

        latencies = []
        token_counts = []
        memory_usage = []

        for run in range(n_runs):
            try:
                # Record memory before request
                if psutil:
                    mem_before = psutil.virtual_memory().percent

                start_time = time.time()

                response = requests.post(
                    self.completions_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=60,
                )

                end_time = time.time()

                if response.status_code == 200:
                    result = response.json()
                    content = result.get("content", "")
                    tokens_generated = len(content.split())  # Rough token count

                    latency = end_time - start_time
                    latencies.append(latency)
                    token_counts.append(tokens_generated)

                    # Record memory after request
                    if psutil:
                        mem_after = psutil.virtual_memory().percent
                        memory_usage.append(mem_after - mem_before)

                    print(".3f")
                else:
                    print(f"Run {run + 1}: HTTP {response.status_code}")

            except Exception as e:
                print(f"Run {run + 1}: Error - {e}")

        if not latencies:
            return {"error": "No successful runs"}

        # Calculate statistics
        avg_latency = statistics.mean(latencies)
        avg_tokens = statistics.mean(token_counts) if token_counts else 0
        tokens_per_sec = avg_tokens / avg_latency if avg_latency > 0 else 0

        result = {
            "avg_latency_seconds": round(avg_latency, 3),
            "avg_tokens_generated": round(avg_tokens, 1),
            "tokens_per_second": round(tokens_per_sec, 2),
            "runs_completed": len(latencies),
            "threads_used": threads,
        }

        if memory_usage:
            result["avg_memory_delta_percent"] = round(statistics.mean(memory_usage), 2)

        return result

    def benchmark_thread_scalability(
        self,
        prompt: str,
        thread_counts: List[int],
        max_tokens: int = 50,
        n_runs: int = 3,
    ) -> List[Dict]:
        """
        Benchmark performance across different thread counts.
        """
        results = []

        print(f"\\nBenchmarking thread scalability with prompt: '{prompt[:50]}...'")
        print("=" * 60)

        for threads in thread_counts:
            print(f"\\nTesting with {threads} threads...")
            result = self.benchmark_completion(
                prompt=prompt, max_tokens=max_tokens, threads=threads, n_runs=n_runs
            )

            if "error" not in result:
                print(f"  Avg latency: {result['avg_latency_seconds']}s")
                print(f"  Tokens/sec: {result['tokens_per_second']}")
                print(f"  Tokens generated: {result['avg_tokens_generated']}")

            results.append({"threads": threads, "metrics": result})

        return results

    def benchmark_model_comparison(
        self, models: List[str], prompt: str, threads: int = 4, max_tokens: int = 50
    ) -> List[Dict]:
        """
        Benchmark different models (requires server restart between models).
        Note: This assumes models are switched externally.
        """
        results = []

        print(f"\\nBenchmarking model comparison with {threads} threads")
        print("=" * 60)

        for model in models:
            print(f"\\nTesting model: {model}")
            print(
                "Note: Please ensure the server is running with this model before continuing..."
            )
            input("Press Enter when ready to test this model...")

            result = self.benchmark_completion(
                prompt=prompt, max_tokens=max_tokens, threads=threads, n_runs=3
            )

            results.append({"model": model, "metrics": result})

            if "error" not in result:
                print(f"  Avg latency: {result['metrics']['avg_latency_seconds']}s")
                print(f"  Tokens/sec: {result['metrics']['tokens_per_second']}")

        return results


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark llama.cpp server performance"
    )
    parser.add_argument(
        "--server-url", default="http://localhost:8080", help="llama.cpp server URL"
    )
    parser.add_argument(
        "--threads",
        type=str,
        default="1,2,4",
        help="Comma-separated thread counts to test",
    )
    parser.add_argument(
        "--models", type=str, help="Comma-separated model names to compare"
    )
    parser.add_argument(
        "--prompt",
        default="Write a short story about a robot learning to paint.",
        help="Prompt for benchmarking",
    )
    parser.add_argument(
        "--max-tokens", type=int, default=50, help="Maximum tokens to generate"
    )
    parser.add_argument(
        "--runs", type=int, default=3, help="Number of runs per configuration"
    )

    args = parser.parse_args()

    # Initialize benchmarker
    benchmarker = LlamaCppBenchmark(args.server_url)

    # Check server health
    if not benchmarker.check_server_health():
        print(f"❌ Server not healthy at {args.server_url}")
        print("Please start the llama.cpp server first.")
        sys.exit(1)

    print(f"✅ Server healthy at {args.server_url}")

    # Get server info
    server_info = benchmarker.get_server_info()
    if server_info:
        print(f"Server info: {json.dumps(server_info, indent=2)}")

    # Parse thread counts
    thread_counts = [int(t.strip()) for t in args.threads.split(",")]

    results = []

    if args.models:
        # Model comparison mode
        models = [m.strip() for m in args.models.split(",")]
        results = benchmarker.benchmark_model_comparison(
            models=models,
            prompt=args.prompt,
            threads=max(thread_counts),  # Use highest thread count
            max_tokens=args.max_tokens,
        )
    else:
        # Thread scalability mode
        results = benchmarker.benchmark_thread_scalability(
            prompt=args.prompt,
            thread_counts=thread_counts,
            max_tokens=args.max_tokens,
            n_runs=args.runs,
        )

    # Print summary
    print("\\n" + "=" * 60)
    print("BENCHMARK SUMMARY")
    print("=" * 60)

    if args.models:
        print("<10")
        for result in results:
            metrics = result["metrics"]
            if "error" not in metrics:
                print("<10")
            else:
                print("<10")
    else:
        print("<10")
        for result in results:
            metrics = result["metrics"]
            if "error" not in metrics:
                print("<10")
            else:
                print("<10")

    # Save results to JSON
    output_file = f"benchmark_results_{int(time.time())}.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\\n📊 Results saved to {output_file}")


if __name__ == "__main__":
    main()
