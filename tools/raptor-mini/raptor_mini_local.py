#!/usr/bin/env python3
"""
Raptor Mini Local Deployment
Equivalent to the Colab notebook but runs locally
"""

import os
import sys
import subprocess
import time
import threading
import requests
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn


# Check if required packages are installed
def check_and_install_packages():
    """Install required packages if not present"""
    required_packages = [
        "fastapi",
        "uvicorn",
        "requests",
        "python-multipart",
        "pyngrok",
        "psutil",
    ]

    print("📦 Checking and installing dependencies...")
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package} already installed")
        except ImportError:
            print(f"📥 Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

    print("✅ All dependencies ready")


# ngrok setup
def setup_ngrok():
    """Set up ngrok authentication"""
    NGROK_AUTH_TOKEN = "36cs1FkRw1Jua3GvHbyU2Smuood_3XfPCs2Jok9MHwANU8G9H"

    if NGROK_AUTH_TOKEN:
        print("🔐 Setting up ngrok authentication...")
        result = subprocess.run(
            ["ngrok", "config", "add-authtoken", NGROK_AUTH_TOKEN],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("✅ ngrok authenticated")
            return True
        else:
            print(f"❌ ngrok auth failed: {result.stderr}")
            return False
    else:
        print("❌ ngrok auth token not found!")
        return False


# FastAPI app
app = FastAPI(title="Raptor Mini", description="Lightweight document analysis API")


class AnalysisRequest(BaseModel):
    task: str
    content: str
    analysis_type: str = "quality_score"


class BatchAnalysisRequest(BaseModel):
    documents: list[
        dict
    ]  # List of {"content": str, "filename": str, "analysis_type": str}
    batch_size: int = 10
    analysis_type: str = "quality_score"


class BatchAnalysisResponse(BaseModel):
    results: list[dict]
    summary: dict
    processing_time: float
    total_documents: int
    successful_analyses: int


class FileAnalysisRequest(BaseModel):
    file_path: str
    analysis_type: str = "quality_score"


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "raptor-mini-local", "version": "1.0.0"}


@app.post("/analyze")
async def analyze_document(request: AnalysisRequest):
    """Basic document analysis using optimized function"""
    return analyze_content(request.content, request.analysis_type)


def analyze_content(content: str, analysis_type: str = "quality_score") -> dict:
    """Optimized document analysis function with memory management"""
    # Simple quality scoring
    score = 50  # Base score

    # Length bonus
    content_len = len(content)
    if content_len > 100:
        score += 20
    if content_len > 500:
        score += 15

    # Structure bonus
    if "##" in content:
        score += 10  # Has sections
    if "```" in content:
        score += 5  # Has code blocks
    if "- " in content or "* " in content:
        score += 5  # Has lists

    # Content quality
    sentences = content.split(".")
    if len(sentences) > 5:
        score += 10  # Multiple sentences

    score = min(100, score)  # Cap at 100

    # Generate feedback
    improvements = []
    if content_len < 100:
        improvements.append("Add more detailed content")
    if "##" not in content:
        improvements.append("Add section headers for better organization")
    if "```" not in content:
        improvements.append("Include code examples where relevant")

    # Determine strengths and weaknesses
    if score >= 80:
        strength = "Excellent structure and content depth"
        weakness = "Could benefit from more specific examples"
    elif score >= 60:
        strength = "Good basic structure"
        weakness = "Needs more detailed content and examples"
    else:
        strength = "Basic content provided"
        weakness = "Needs significant expansion and structure"

    return {
        "score": score,
        "strength": strength,
        "weakness": weakness,
        "improvements": improvements,
        "analysis_type": analysis_type,
        "content_length": content_len,
        "sentence_count": len(sentences),
    }


@app.post("/analyze/batch")
async def analyze_batch(request: BatchAnalysisRequest):
    """Batch process multiple documents with memory optimization"""
    import time

    start_time = time.time()

    results = []
    successful_analyses = 0
    total_docs = len(request.documents)

    # Process in batches to manage memory
    batch_size = min(request.batch_size, 50)  # Cap batch size for memory management

    for i in range(0, total_docs, batch_size):
        batch = request.documents[i : i + batch_size]

        for doc in batch:
            try:
                content = doc.get("content", "")
                filename = doc.get("filename", f"doc_{len(results) + 1}")
                analysis_type = doc.get("analysis_type", request.analysis_type)

                # Analyze content
                analysis_result = analyze_content(content, analysis_type)
                analysis_result["filename"] = filename

                results.append(analysis_result)
                successful_analyses += 1

            except Exception as e:
                results.append(
                    {
                        "filename": doc.get("filename", f"doc_{len(results) + 1}"),
                        "error": str(e),
                        "score": 0,
                        "analysis_type": request.analysis_type,
                    }
                )

        # Memory cleanup - force garbage collection between batches
        if i + batch_size < total_docs:
            import gc

            gc.collect()

    # Generate summary statistics
    scores = [
        r.get("score", 0)
        for r in results
        if "score" in r and isinstance(r["score"], (int, float))
    ]
    summary = {
        "average_score": round(sum(scores) / len(scores), 1) if scores else 0,
        "max_score": max(scores) if scores else 0,
        "min_score": min(scores) if scores else 0,
        "high_quality_docs": len([s for s in scores if s >= 80]),
        "medium_quality_docs": len([s for s in scores if 60 <= s < 80]),
        "low_quality_docs": len([s for s in scores if s < 60]),
    }

    processing_time = time.time() - start_time

    return BatchAnalysisResponse(
        results=results,
        summary=summary,
        processing_time=round(processing_time, 2),
        total_documents=total_docs,
        successful_analyses=successful_analyses,
    )


@app.post("/analyze/file")
async def analyze_file(request: FileAnalysisRequest):
    """Analyze a file directly from the filesystem"""
    try:
        # Security check - only allow files within the workspace
        workspace_root = "/Users/fuaadabdullah/ForgeMonorepo"
        abs_path = os.path.abspath(request.file_path)

        if not abs_path.startswith(workspace_root):
            return {"error": "Access denied: File must be within workspace", "score": 0}

        if not os.path.exists(abs_path):
            return {"error": f"File not found: {request.file_path}", "score": 0}

        # Read file content
        with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # Analyze content
        result = analyze_content(content, request.analysis_type)
        result["file_path"] = request.file_path
        result["file_size"] = len(content)

        return result

    except Exception as e:
        return {
            "error": f"Failed to analyze file: {str(e)}",
            "file_path": request.file_path,
            "score": 0,
            "analysis_type": request.analysis_type,
        }


@app.get("/performance")
async def get_performance_stats():
    """Get performance and memory usage statistics"""
    import psutil
    import os

    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()

    return {
        "memory_usage_mb": round(memory_info.rss / 1024 / 1024, 2),
        "memory_percent": round(process.memory_percent(), 2),
        "cpu_percent": round(process.cpu_percent(interval=1), 2),
        "threads": process.num_threads(),
        "uptime_seconds": round(time.time() - process.create_time(), 2),
    }


def run_server():
    """Run the FastAPI server"""
    uvicorn.run(app, host="0.0.0.0", port=8000)


def start_ngrok_tunnel():
    """Start ngrok tunnel using pyngrok"""
    print("🌐 Starting ngrok tunnel...")

    try:
        from pyngrok import ngrok

        # Set auth token
        ngrok.set_auth_token("36cs1FkRw1Jua3GvHbyU2Smuood_3XfPCs2Jok9MHwANU8G9H")

        # Start tunnel
        print("🔄 Launching ngrok tunnel on port 8000...")
        tunnel = ngrok.connect(8000)
        public_url = tunnel.public_url

        print("✅ ngrok tunnel established!")
        print(f"🔗 Public URL: {public_url}")
        print(f"📋 Copy this URL: {public_url}")

        # Update .env file
        update_env_file(public_url)

        # Test the API
        test_api_endpoints(public_url)

        return public_url

    except Exception as e:
        print(f"❌ ngrok tunnel failed: {e}")
        return None


def update_env_file(ngrok_url):
    """Update the .env file with the new ngrok URL"""
    env_file = ".env"

    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            content = f.read()

        # Replace the RAPTOR_MINI_URL
        import re

        new_content = re.sub(
            r"RAPTOR_MINI_URL=.*", f"RAPTOR_MINI_URL={ngrok_url}", content
        )

        with open(env_file, "w") as f:
            f.write(new_content)

        print(f"✅ Updated {env_file} with new ngrok URL")
    else:
        # Create new .env file
        with open(env_file, "w") as f:
            f.write(f"# Raptor Mini Configuration\nRAPTOR_MINI_URL={ngrok_url}\n")
        print(f"✅ Created {env_file} with ngrok URL")


def test_api_endpoints(public_url):
    """Test the API endpoints"""
    print("\n🧪 Testing API endpoints...")

    # Test health endpoint
    try:
        health_response = requests.get(f"{public_url}/health", timeout=10)
        if health_response.status_code == 200:
            print("✅ Health endpoint working")
            print(f"   Response: {health_response.json()}")
        else:
            print(f"❌ Health endpoint failed: {health_response.status_code}")
    except Exception as e:
        print(f"❌ Health test failed: {e}")

    # Test analyze endpoint
    try:
        test_payload = {
            "task": "analyze_document",
            "content": "This is a test document for quality analysis. It has multiple sentences and some structure.",
            "analysis_type": "quality_score",
        }
        analyze_response = requests.post(
            f"{public_url}/analyze", json=test_payload, timeout=10
        )
        if analyze_response.status_code == 200:
            print("✅ Analyze endpoint working")
            result = analyze_response.json()
            print(f"   Score: {result.get('score', 'N/A')}/100")
            print(f"   Strength: {result.get('strength', 'N/A')}")
        else:
            print(f"❌ Analyze endpoint failed: {analyze_response.status_code}")
    except Exception as e:
        print(f"❌ Analyze test failed: {e}")


def main():
    """Main deployment function"""
    print("🚀 Raptor Mini Local Deployment Starting...")
    print("=" * 50)

    # Check and install packages
    check_and_install_packages()

    # Setup ngrok
    if not setup_ngrok():
        print("❌ ngrok setup failed. Please check your token.")
        return

    # Start the server in a thread
    print("📡 Starting Raptor Mini server...")
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Wait for server to start
    time.sleep(2)
    print("✅ Server started on port 8000")

    # Start ngrok tunnel
    public_url = start_ngrok_tunnel()

    if public_url:
        print("\n🎉 Raptor Mini is ready!")
        print(f"🔗 Your API URL: {public_url}")
        print("📝 .env file has been updated")
        print("\n🔄 The tunnel will stay active as long as this script runs!")
        print("🛑 Press Ctrl+C to stop the server")  # Keep the script running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
            subprocess.run(["pkill", "-f", "ngrok"], capture_output=True)
            print("✅ Cleanup complete")
    else:
        print("❌ Failed to establish ngrok tunnel")


if __name__ == "__main__":
    main()
