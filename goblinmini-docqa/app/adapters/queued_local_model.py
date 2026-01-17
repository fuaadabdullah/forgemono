# app/adapters/queued_local_model.py
from typing import Any, Dict, List
from ..inference_queue import InferenceQueue
from ..doc_processor import DocumentProcessor


class QueuedLocalModelAdapter:
    """Local model adapter that uses an inference queue for concurrency control."""

    def __init__(self, inference_queue: InferenceQueue):
        self.inference_queue = inference_queue
        self.doc_processor = DocumentProcessor()
        self.name = "queued_local_phi3"

    def health_check(self, timeout: float = 3.0) -> bool:
        # For queued adapter, we can't easily do a health check without consuming queue capacity
        # Return True if queue is running (basic check)
        return hasattr(self.inference_queue, "running") and self.inference_queue.running

    def generate(self, prompt: str, max_tokens: int = 512, **kwargs) -> Any:
        """Submit inference job to queue and wait for result."""
        # Package the request with all parameters
        payload = {"prompt": prompt, "max_tokens": max_tokens, **kwargs}
        # Submit to queue with reasonable timeout
        import asyncio

        try:
            # This will be called from async context, so we can await
            return asyncio.create_task(
                self.inference_queue.submit(payload, timeout=30.0)
            )
        except RuntimeError as e:
            if "backpressure" in str(e):
                raise RuntimeError(
                    "Inference queue full - too many concurrent requests"
                )
            raise

    async def agenerate(self, prompt: str, max_tokens: int = 512, **kwargs) -> Any:
        """Async version for direct queue submission."""
        payload = {"prompt": prompt, "max_tokens": max_tokens, **kwargs}
        return await self.inference_queue.submit(payload, timeout=30.0)

    def analyze_content(self, content: str, filename: str = None) -> Dict[str, Any]:
        """Analyze document content with chunking for large documents."""
        # Use document processor for intelligent chunking and summarization
        result = self.doc_processor.process_document(content, self.generate)

        return {
            "filename": filename,
            "processing_method": result["method"],
            "word_count": result["word_count"],
            "chunks_processed": result["chunks"],
            "summary": result["summary"],
            "chunk_details": result.get("chunk_summaries", []),
            "quality_score": self._calculate_quality_score(result),
            "recommendations": self._generate_recommendations(result),
        }

    def _calculate_quality_score(self, processing_result: Dict[str, Any]) -> float:
        """Calculate a quality score based on processing results."""
        base_score = 0.8  # Base quality score

        # Bonus for chunked processing (indicates large/complex document)
        if processing_result["method"] == "chunked":
            base_score += 0.1

        # Penalty for very short documents
        if processing_result["word_count"] < 100:
            base_score -= 0.2

        return max(0.0, min(1.0, base_score))

    def _generate_recommendations(self, processing_result: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on document analysis."""
        recommendations = []

        if processing_result["method"] == "chunked":
            recommendations.append(
                "Large document processed with chunking - consider breaking into smaller files"
            )

        if processing_result["word_count"] > 5000:
            recommendations.append(
                "Very large document - consider using specialized documentation tools"
            )

        if processing_result["chunks"] > 10:
            recommendations.append(
                "Document has many sections - consider adding a table of contents"
            )

        return (
            recommendations
            if recommendations
            else ["Document structure appears appropriate"]
        )

    def metadata(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": "queued_local",
            "queue_size": self.inference_queue.queue.maxsize,
            "max_workers": self.inference_queue.semaphore._value,
            "running": self.inference_queue.running,
            "chunking_enabled": True,
            "max_chunk_words": self.doc_processor.max_chunk_words,
        }

    def shutdown(self):
        """Shutdown the inference queue."""
        # Note: This doesn't actually stop the queue, just marks it as not running
        # In a real implementation, you'd want proper cleanup
        self.inference_queue.running = False
