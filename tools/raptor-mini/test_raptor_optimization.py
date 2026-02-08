#!/usr/bin/env python3
"""
Raptor Mini API Testing & Optimization Script
Tests batch processing and file analysis with real ForgeMonorepo documentation
"""

import os
import time
import requests
from pathlib import Path
from typing import List, Dict, Any


class RaptorTester:
    """Test harness for Raptor Mini API"""

    def __init__(
        self, base_url: str = "https://thomasena-auxochromic-joziah.ngrok-free.dev"
    ):
        self.base_url = base_url
        self.session = requests.Session()

    def test_health(self) -> bool:
        """Test health endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                print("✅ Health check passed")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False

    def test_single_analysis(
        self, content: str, filename: str = "test.md"
    ) -> Dict[str, Any]:
        """Test single document analysis"""
        payload = {
            "task": "analyze_document",
            "content": content,
            "analysis_type": "quality_score",
        }

        try:
            response = self.session.post(
                f"{self.base_url}/analyze", json=payload, timeout=15
            )
            if response.status_code == 200:
                result = response.json()
                print(
                    f"✅ Single analysis: {filename} - Score: {result.get('score', 'N/A')}/100"
                )
                return result
            else:
                print(f"❌ Single analysis failed: {response.status_code}")
                return {}
        except Exception as e:
            print(f"❌ Single analysis error: {e}")
            return {}

    def test_batch_analysis(
        self, documents: List[Dict[str, str]], batch_size: int = 10
    ) -> Dict[str, Any]:
        """Test batch document analysis"""
        payload = {
            "documents": documents,
            "batch_size": batch_size,
            "analysis_type": "quality_score",
        }

        start_time = time.time()
        try:
            response = self.session.post(
                f"{self.base_url}/analyze/batch", json=payload, timeout=60
            )
            processing_time = time.time() - start_time

            if response.status_code == 200:
                result = response.json()
                print(
                    f"✅ Batch analysis completed in {result.get('processing_time', 'N/A')}s"
                )
                print(f"   Processed {result.get('total_documents', 0)} documents")
                print(
                    f"   Success rate: {result.get('successful_analyses', 0)}/{result.get('total_documents', 0)}"
                )
                print(
                    f"   Average score: {result.get('summary', {}).get('average_score', 'N/A')}"
                )
                return result
            else:
                print(f"❌ Batch analysis failed: {response.status_code}")
                print(f"   Response: {response.text[:500]}...")
                return {}
        except Exception as e:
            processing_time = time.time() - start_time
            print(f"❌ Batch analysis error after {processing_time:.2f}s: {e}")
            return {}

    def test_file_analysis(self, file_path: str) -> Dict[str, Any]:
        """Test file analysis endpoint"""
        payload = {"file_path": file_path, "analysis_type": "quality_score"}

        try:
            response = self.session.post(
                f"{self.base_url}/analyze/file", json=payload, timeout=15
            )
            if response.status_code == 200:
                result = response.json()
                if "error" not in result:
                    print(
                        f"✅ File analysis: {os.path.basename(file_path)} - Score: {result.get('score', 'N/A')}/100"
                    )
                else:
                    print(
                        f"❌ File analysis error: {result.get('error', 'Unknown error')}"
                    )
                return result
            else:
                print(f"❌ File analysis failed: {response.status_code}")
                return {}
        except Exception as e:
            print(f"❌ File analysis error: {e}")
            return {}

    def test_performance(self) -> Dict[str, Any]:
        """Test performance monitoring endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/performance", timeout=10)
            if response.status_code == 200:
                stats = response.json()
                print("✅ Performance stats retrieved:")
                print(f"   Memory usage: {stats.get('memory_usage_mb', 'N/A')} MB")
                print(f"   CPU usage: {stats.get('cpu_percent', 'N/A')}%")
                print(f"   Threads: {stats.get('threads', 'N/A')}")
                return stats
            else:
                print(f"❌ Performance stats failed: {response.status_code}")
                return {}
        except Exception as e:
            print(f"❌ Performance stats error: {e}")
            return {}

    def load_forgemono_docs(self, limit: int = 20) -> List[Dict[str, str]]:
        """Load real ForgeMonorepo documentation files"""
        docs_dir = "/Users/fuaadabdullah/ForgeMonorepo/docs"
        documents = []

        if not os.path.exists(docs_dir):
            print(f"❌ Docs directory not found: {docs_dir}")
            return documents

        # Get markdown files
        md_files = list(Path(docs_dir).glob("*.md"))[:limit]

        for file_path in md_files:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                if len(content.strip()) > 50:  # Only include substantial files
                    documents.append(
                        {
                            "content": content,
                            "filename": file_path.name,
                            "analysis_type": "quality_score",
                        }
                    )

            except Exception as e:
                print(f"⚠️  Failed to load {file_path.name}: {e}")

        print(f"📚 Loaded {len(documents)} documentation files")
        return documents


def main():
    """Main testing function"""
    print("🧪 Raptor Mini API Testing & Optimization")
    print("=" * 50)

    tester = RaptorTester()

    # Test health
    if not tester.test_health():
        print("❌ API is not healthy. Exiting.")
        return

    # Test performance baseline
    print("\n📊 Performance Baseline:")
    tester.test_performance()

    # Test single analysis with sample content
    print("\n📄 Single Document Analysis Test:")
    sample_content = """# Sample Documentation

This is a sample document for testing the Raptor Mini analysis API.

## Features

- Feature 1: Description here
- Feature 2: Another description

## Code Example

```python
def hello_world():
    print("Hello, World!")
```

This document demonstrates various markdown features."""

    tester.test_single_analysis(sample_content, "sample.md")

    # Load and test with real ForgeMonorepo docs
    print("\n📚 Batch Analysis with Real Documentation:")
    documents = tester.load_forgemono_docs(limit=15)

    if documents:
        # Test batch processing
        batch_result = tester.test_batch_analysis(documents, batch_size=5)

        if batch_result:
            # Show top 5 results
            results = batch_result.get("results", [])
            print("\n🏆 Top 5 Documentation Scores:")
            sorted_results = sorted(
                [r for r in results if "score" in r],
                key=lambda x: x["score"],
                reverse=True,
            )

            for i, result in enumerate(sorted_results[:5], 1):
                filename = result.get("filename", "unknown")
                score = result.get("score", 0)
                strength = result.get("strength", "unknown")
                print(f"   {i}. {filename}: {score}/100 - {strength}")

    # Test file analysis
    print("\n📁 File Analysis Test:")
    test_file = "/Users/fuaadabdullah/ForgeMonorepo/docs/README.md"
    if os.path.exists(test_file):
        tester.test_file_analysis(test_file)

    # Final performance check
    print("\n📊 Final Performance Check:")
    tester.test_performance()

    print("\n🎉 Testing completed!")


if __name__ == "__main__":
    main()
