# app/doc_processor.py
"""
Document processing with chunking and summarization for large documents.
Splits big docs, summarizes chunks, then synthesizes results to reduce max_tokens per call.
"""

import re
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class DocumentChunk:
    """Represents a chunk of document text with metadata."""

    text: str
    start_pos: int
    end_pos: int
    chunk_id: int
    word_count: int


@dataclass
class ChunkSummary:
    """Summary of a document chunk."""

    chunk_id: int
    summary: str
    key_points: List[str]
    relevance_score: float


class DocumentProcessor:
    """Processes large documents using chunking and summarization."""

    def __init__(
        self,
        max_chunk_words: int = 1000,
        overlap_words: int = 100,
        min_chunk_words: int = 200,
    ):
        self.max_chunk_words = max_chunk_words
        self.overlap_words = overlap_words
        self.min_chunk_words = min_chunk_words

    def split_into_chunks(self, text: str) -> List[DocumentChunk]:
        """Split document into overlapping chunks."""
        words = text.split()
        chunks = []
        start_idx = 0
        chunk_id = 0

        while start_idx < len(words):
            # Calculate end index for this chunk
            end_idx = min(start_idx + self.max_chunk_words, len(words))

            # If we're near the end and chunk would be too small, extend it
            if (len(words) - start_idx) < self.min_chunk_words and start_idx > 0:
                end_idx = len(words)

            # Extract chunk text
            chunk_words = words[start_idx:end_idx]
            chunk_text = " ".join(chunk_words)

            # Calculate character positions
            start_pos = len(" ".join(words[:start_idx]))
            if start_pos > 0:
                start_pos += 1  # Account for space
            end_pos = start_pos + len(chunk_text)

            chunk = DocumentChunk(
                text=chunk_text,
                start_pos=start_pos,
                end_pos=end_pos,
                chunk_id=chunk_id,
                word_count=len(chunk_words),
            )
            chunks.append(chunk)

            # Move start position with overlap (unless we're at the end)
            if end_idx < len(words):
                start_idx = end_idx - self.overlap_words
            else:
                break

            chunk_id += 1

        return chunks

    def summarize_chunk(self, chunk: DocumentChunk, model_call) -> ChunkSummary:
        """Summarize a single chunk using the model."""
        prompt = f"""
        Summarize the following text in 2-3 sentences, focusing on key technical concepts,
        implementation details, and important information. Also extract 3-5 key points.

        Text:
        {chunk.text}

        Format your response as:
        SUMMARY: [your summary]
        KEY_POINTS: [point 1], [point 2], [point 3], ...
        """

        try:
            response = model_call(
                {
                    "prompt": prompt,
                    "max_tokens": 300,  # Smaller token limit for summaries
                    "temperature": 0.3,
                }
            )

            # Parse the response
            response_text = response.get("choices", [{}])[0].get("text", "").strip()

            # Extract summary and key points
            summary_match = re.search(
                r"SUMMARY:\s*(.*?)(?:\n|$)", response_text, re.IGNORECASE | re.DOTALL
            )
            keypoints_match = re.search(
                r"KEY_POINTS:\s*(.*?)(?:\n|$)", response_text, re.IGNORECASE | re.DOTALL
            )

            summary = (
                summary_match.group(1).strip()
                if summary_match
                else response_text[:200] + "..."
            )
            keypoints_text = keypoints_match.group(1).strip() if keypoints_match else ""

            # Parse key points
            key_points = [pt.strip() for pt in keypoints_text.split(",") if pt.strip()]
            if not key_points:
                key_points = ["Key technical concepts discussed"]

            return ChunkSummary(
                chunk_id=chunk.chunk_id,
                summary=summary,
                key_points=key_points[:5],  # Limit to 5 points
                relevance_score=1.0,  # Could be calculated based on content
            )

        except Exception:
            # Fallback summary
            return ChunkSummary(
                chunk_id=chunk.chunk_id,
                summary=f"Chunk {chunk.chunk_id}: {chunk.text[:100]}...",
                key_points=["Content analysis failed"],
                relevance_score=0.5,
            )

    def synthesize_summaries(self, summaries: List[ChunkSummary], model_call) -> str:
        """Synthesize all chunk summaries into a final coherent summary."""
        if len(summaries) == 1:
            return summaries[0].summary

        # Combine all summaries and key points
        combined_text = "\n\n".join(
            [
                f"Section {summary.chunk_id}: {summary.summary}\nKey points: {', '.join(summary.key_points)}"
                for summary in summaries
            ]
        )

        prompt = f"""
        Synthesize the following section summaries into a single coherent summary of the entire document.
        Maintain technical accuracy and preserve important implementation details.

        Section Summaries:
        {combined_text}

        Provide a comprehensive but concise summary in 4-6 sentences:
        """

        try:
            response = model_call(
                {
                    "prompt": prompt,
                    "max_tokens": 500,  # Larger limit for synthesis
                    "temperature": 0.2,
                }
            )

            return response.get("choices", [{}])[0].get("text", "").strip()

        except Exception:
            # Fallback: combine summaries
            return " ".join([summary.summary for summary in summaries])

    def process_document(self, text: str, model_call) -> Dict[str, Any]:
        """Process a document with chunking and summarization."""
        # Check if document needs chunking
        word_count = len(text.split())

        if word_count <= self.max_chunk_words:
            # Small document, process directly
            return {
                "method": "direct",
                "word_count": word_count,
                "chunks": 1,
                "summary": self._direct_summarize(text, model_call),
            }

        # Large document, use chunking approach
        chunks = self.split_into_chunks(text)

        # Summarize each chunk
        summaries = []
        for chunk in chunks:
            summary = self.summarize_chunk(chunk, model_call)
            summaries.append(summary)

        # Synthesize final summary
        final_summary = self.synthesize_summaries(summaries, model_call)

        return {
            "method": "chunked",
            "word_count": word_count,
            "chunks": len(chunks),
            "chunk_summaries": [
                {
                    "chunk_id": summary.chunk_id,
                    "summary": summary.summary,
                    "key_points": summary.key_points,
                    "relevance_score": summary.relevance_score,
                }
                for summary in summaries
            ],
            "summary": final_summary,
        }

    def _direct_summarize(self, text: str, model_call) -> str:
        """Direct summarization for small documents."""
        prompt = f"""
        Summarize the following technical document in 3-5 sentences,
        focusing on key concepts, implementation details, and important information:

        {text}
        """

        try:
            response = model_call(
                {"prompt": prompt, "max_tokens": 400, "temperature": 0.3}
            )

            return response.get("choices", [{}])[0].get("text", "").strip()

        except Exception as e:
            return f"Summary unavailable: {str(e)}"
