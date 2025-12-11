#!/usr/bin/env python3
"""
Raptor Mini API Usage Examples
Demonstrates how to use the optimized Raptor Mini API for document analysis
"""

import requests
import os
from pathlib import Path
from typing import List, Dict, Any


class RaptorMiniClient:
    """Client for interacting with Raptor Mini API"""

    def __init__(
        self, base_url: str = "https://thomasena-auxochromic-joziah.ngrok-free.dev"
    ):
        self.base_url = base_url
        self.session = requests.Session()

    def health_check(self) -> bool:
        """Check if API is healthy"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def analyze_document(
        self, content: str, filename: str = "document.md"
    ) -> Dict[str, Any]:
        """Analyze a single document"""
        payload = {
            "task": "analyze_document",
            "content": content,
            "analysis_type": "quality_score",
        }

        response = self.session.post(
            f"{self.base_url}/analyze", json=payload, timeout=15
        )
        if response.status_code == 200:
            result = response.json()
            result["filename"] = filename
            return result
        else:
            return {"error": f"API error: {response.status_code}", "filename": filename}

    def analyze_batch(
        self, documents: List[Dict[str, str]], batch_size: int = 10
    ) -> Dict[str, Any]:
        """Analyze multiple documents in batch"""
        payload = {
            "documents": documents,
            "batch_size": batch_size,
            "analysis_type": "quality_score",
        }

        response = self.session.post(
            f"{self.base_url}/analyze/batch", json=payload, timeout=60
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Batch API error: {response.status_code}"}

    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a file directly"""
        payload = {"file_path": file_path, "analysis_type": "quality_score"}

        response = self.session.post(
            f"{self.base_url}/analyze/file", json=payload, timeout=15
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"File API error: {response.status_code}"}

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        response = self.session.get(f"{self.base_url}/performance", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Performance API error: {response.status_code}"}


def demo_single_analysis():
    """Demo single document analysis"""
    print("📄 Single Document Analysis Demo")
    print("-" * 40)

    client = RaptorMiniClient()

    # Sample high-quality document
    content = """# AI Development Best Practices

This comprehensive guide covers advanced AI development techniques with detailed explanations and practical examples.

## Core Principles

1. Data quality is paramount for model performance
2. Model validation prevents overfitting issues
3. Continuous monitoring improves long-term results

## Implementation

```python
def train_model(data, epochs=100):
    model = Sequential()
    model.add(Dense(64, activation='relu'))
    return model
```

## Key Considerations

- Scalability requirements
- Performance metrics
- Error handling strategies

This document provides excellent structure and depth."""

    result = client.analyze_document(content, "ai_guide.md")

    if "error" not in result:
        print("✅ Analysis complete!")
        print(f"   Score: {result['score']}/100")
        print(f"   Strength: {result['strength']}")
        print(f"   Content Length: {result['content_length']} chars")
        print(f"   Sentences: {result['sentence_count']}")
    else:
        print(f"❌ Error: {result['error']}")


def demo_batch_analysis():
    """Demo batch document analysis with ForgeMonorepo docs"""
    print("\n📚 Batch Analysis Demo (ForgeMonorepo Docs)")
    print("-" * 50)

    client = RaptorMiniClient()

    # Load some real documentation files
    docs_dir = Path("/Users/fuaadabdullah/ForgeMonorepo/docs")
    documents = []

    # Get a few key documentation files
    target_files = [
        "WORKSPACE_OVERVIEW.md",
        "README.md",
        "TECH_STACK.md",
        "SECRETS_HANDLING.md",
    ]

    for filename in target_files:
        file_path = docs_dir / filename
        if file_path.exists():
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                if len(content) > 200:  # Only substantial files
                    documents.append(
                        {
                            "content": content,
                            "filename": filename,
                            "analysis_type": "quality_score",
                        }
                    )
            except Exception as e:
                print(f"⚠️  Failed to load {filename}: {e}")

    if not documents:
        print("❌ No documentation files found to analyze")
        return

    print(f"📖 Loaded {len(documents)} documentation files")

    # Analyze in batch
    batch_result = client.analyze_batch(documents, batch_size=5)

    if "error" not in batch_result:
        print("✅ Batch analysis complete!")
        print(f"   Processing time: {batch_result['processing_time']}s")
        print(f"   Documents processed: {batch_result['total_documents']}")
        print(
            f"   Success rate: {batch_result['successful_analyses']}/{batch_result['total_documents']}"
        )

        summary = batch_result["summary"]
        print(f"   Average score: {summary['average_score']}/100")
        print(f"   High quality docs: {summary['high_quality_docs']}")
        print(f"   Medium quality docs: {summary['medium_quality_docs']}")
        print(f"   Low quality docs: {summary['low_quality_docs']}")

        # Show top 3 performing docs
        results = batch_result["results"]
        valid_results = [
            r for r in results if "score" in r and isinstance(r["score"], (int, float))
        ]
        sorted_results = sorted(valid_results, key=lambda x: x["score"], reverse=True)

        print("\n🏆 Top 3 Documentation Files:")
        for i, result in enumerate(sorted_results[:3], 1):
            print(
                f"   {i}. {result['filename']}: {result['score']}/100 - {result['strength']}"
            )
    else:
        print(f"❌ Batch error: {batch_result['error']}")


def demo_file_analysis():
    """Demo direct file analysis"""
    print("\n📁 File Analysis Demo")
    print("-" * 30)

    client = RaptorMiniClient()

    # Analyze a specific file
    file_path = "/Users/fuaadabdullah/ForgeMonorepo/docs/WORKSPACE_OVERVIEW.md"

    if os.path.exists(file_path):
        result = client.analyze_file(file_path)

        if "error" not in result:
            print("✅ File analysis complete!")
            print(f"   File: {result.get('file_path', 'unknown')}")
            print(f"   Score: {result['score']}/100")
            print(f"   Strength: {result['strength']}")
            print(f"   File size: {result.get('file_size', 'unknown')} chars")
        else:
            print(f"❌ File error: {result['error']}")
    else:
        print(f"❌ File not found: {file_path}")


def demo_performance_monitoring():
    """Demo performance monitoring"""
    print("\n📊 Performance Monitoring Demo")
    print("-" * 35)

    client = RaptorMiniClient()

    stats = client.get_performance_stats()

    if "error" not in stats:
        print("✅ Performance stats retrieved:")
        print(f"   Memory usage: {stats.get('memory_usage_mb', 'N/A')} MB")
        print(f"   Memory percent: {stats.get('memory_percent', 'N/A')}%")
        print(f"   CPU usage: {stats.get('cpu_percent', 'N/A')}%")
        print(f"   Threads: {stats.get('threads', 'N/A')}")
        print(f"   Uptime: {stats.get('uptime_seconds', 'N/A')} seconds")
    else:
        print(f"❌ Performance error: {stats['error']}")


def main():
    """Main demo function"""
    print("🚀 Raptor Mini API Usage Demo")
    print("=" * 50)
    print("Optimized document analysis API with batch processing")
    print()

    client = RaptorMiniClient()

    # Health check
    if not client.health_check():
        print("❌ Raptor Mini API is not accessible")
        print("   Make sure the server is running:")
        print("   cd /Users/fuaadabdullah/ForgeMonorepo")
        print(
            "   /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant/backend/venv/bin/python tools/raptor-mini/raptor_mini_local.py"
        )
        return

    print("✅ Raptor Mini API is running!")

    # Run demos
    demo_single_analysis()
    demo_batch_analysis()
    demo_file_analysis()
    demo_performance_monitoring()

    print("\n🎉 Demo completed!")
    print("\n💡 API Endpoints:")
    print("   • Single analysis: POST /analyze")
    print("   • Batch analysis: POST /analyze/batch")
    print("   • File analysis: POST /analyze/file")
    print("   • Performance: GET /performance")
    print("   • Health check: GET /health")


if __name__ == "__main__":
    main()
