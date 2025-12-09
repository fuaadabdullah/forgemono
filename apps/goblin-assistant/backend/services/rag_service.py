"""
RAG (Retrieval-Augmented Generation) Service
Implements a flexible pipeline: fast dense retriever → chunk filter → model with extended context.

Features:
- Dense retrieval with semantic search
- Intelligent chunk filtering and ranking
- Extended context window support (10k tokens)
- Session-based caching for hot-paths
- Fallback to large context models
"""

import os
import asyncio
import hashlib
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import chromadb
from chromadb.config import Settings
import numpy as np
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)


class RAGService:
    """RAG service with dense retriever and extended context support."""

    def __init__(
        self, chroma_path: str = "/Users/fuaadabdullah/ForgeMonorepo/chroma_db"
    ):
        """Initialize RAG service with ChromaDB and embedding model."""
        self.chroma_path = chroma_path
        self.chroma_client = chromadb.PersistentClient(path=chroma_path)

        # Initialize embedding model (fast and efficient)
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")  # Fast, 384-dim

        # Create/get collections
        self.documents_collection = self.chroma_client.get_or_create_collection(
            name="documents",
            metadata={"description": "Document chunks for RAG retrieval"},
        )

        self.sessions_collection = self.chroma_client.get_or_create_collection(
            name="sessions",
            metadata={"description": "Recent session cache for hot-paths"},
        )

        # Configuration
        self.max_retriever_tokens = 10000  # 10k token window
        self.chunk_size = 512  # tokens per chunk
        self.chunk_overlap = 50  # token overlap between chunks
        self.max_chunks = 20  # Maximum chunks to retrieve
        self.session_cache_ttl = 3600  # 1 hour for session cache

        # Token estimation (rough: ~4 chars per token)
        self.chars_per_token = 4

    async def add_documents(
        self, documents: List[Dict[str, Any]], collection_name: str = "documents"
    ) -> bool:
        """Add documents to the vector database with chunking."""
        try:
            collection = self.chroma_client.get_or_create_collection(
                name=collection_name
            )

            for doc in documents:
                doc_id = doc.get("id", hashlib.md5(doc["content"].encode()).hexdigest())
                content = doc["content"]
                metadata = doc.get("metadata", {})

                # Chunk the document
                chunks = self._chunk_text(content, self.chunk_size, self.chunk_overlap)

                # Generate embeddings for chunks
                embeddings = []
                chunk_texts = []
                chunk_metadatas = []

                for i, chunk in enumerate(chunks):
                    chunk_id = f"{doc_id}_chunk_{i}"
                    chunk_metadata = {
                        **metadata,
                        "doc_id": doc_id,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "chunk_text": chunk[:200],  # Preview for debugging
                    }

                    embeddings.append(self.embedding_model.encode(chunk).tolist())
                    chunk_texts.append(chunk)
                    chunk_metadatas.append(chunk_metadata)

                # Add to collection
                collection.add(
                    ids=[f"{doc_id}_chunk_{i}" for i in range(len(chunks))],
                    embeddings=embeddings,
                    documents=chunk_texts,
                    metadatas=chunk_metadatas,
                )

            logger.info(f"Added {len(documents)} documents to {collection_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            return False

    def _chunk_text(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """Chunk text into smaller pieces with overlap."""
        words = text.split()
        chunks = []
        i = 0

        while i < len(words):
            # Calculate chunk end
            chunk_end = min(i + chunk_size, len(words))

            # Extract chunk
            chunk_words = words[i:chunk_end]
            chunk = " ".join(chunk_words)
            chunks.append(chunk)

            # Move start position with overlap
            i += chunk_size - overlap

            # Prevent infinite loop
            if chunk_end == len(words):
                break

        return chunks

    async def retrieve_context(
        self, query: str, top_k: int = 10, filters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Retrieve relevant context using dense retrieval and filtering."""
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query).tolist()

            # Search documents collection
            results = self.documents_collection.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k * 2, self.max_chunks),  # Get more for filtering
                where=filters,
            )

            if not results["documents"]:
                return {"chunks": [], "total_tokens": 0, "filtered_count": 0}

            # Filter and rank chunks
            filtered_chunks = self._filter_and_rank_chunks(
                query,
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            )

            # Calculate total tokens
            total_tokens = sum(
                self._estimate_tokens(chunk["text"]) for chunk in filtered_chunks
            )

            # Trim to token limit if needed
            if total_tokens > self.max_retriever_tokens:
                filtered_chunks = self._trim_to_token_limit(
                    filtered_chunks, self.max_retriever_tokens
                )

            return {
                "chunks": filtered_chunks,
                "total_tokens": sum(
                    self._estimate_tokens(chunk["text"]) for chunk in filtered_chunks
                ),
                "filtered_count": len(filtered_chunks),
            }

        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return {
                "chunks": [],
                "total_tokens": 0,
                "filtered_count": 0,
                "error": str(e),
            }

    def _filter_and_rank_chunks(
        self,
        query: str,
        documents: List[str],
        metadatas: List[Dict],
        distances: List[float],
    ) -> List[Dict[str, Any]]:
        """Filter and rank retrieved chunks based on relevance."""
        chunks = []

        for doc, metadata, distance in zip(documents, metadatas, distances):
            # Calculate relevance score (lower distance = higher relevance)
            relevance_score = 1.0 / (1.0 + distance)  # Convert distance to similarity

            # Additional filtering criteria
            query_terms = set(query.lower().split())
            doc_terms = set(doc.lower().split())
            term_overlap = (
                len(query_terms.intersection(doc_terms)) / len(query_terms)
                if query_terms
                else 0
            )

            # Boost score for term overlap
            combined_score = relevance_score * (1 + term_overlap)

            chunks.append(
                {
                    "text": doc,
                    "metadata": metadata,
                    "relevance_score": combined_score,
                    "distance": distance,
                    "term_overlap": term_overlap,
                }
            )

        # Sort by combined score and return top chunks
        chunks.sort(key=lambda x: x["relevance_score"], reverse=True)
        return chunks[: self.max_chunks]

    def _trim_to_token_limit(
        self, chunks: List[Dict[str, Any]], max_tokens: int
    ) -> List[Dict[str, Any]]:
        """Trim chunks to fit within token limit, keeping highest scoring chunks."""
        total_tokens = 0
        trimmed_chunks = []

        for chunk in chunks:
            chunk_tokens = self._estimate_tokens(chunk["text"])
            if total_tokens + chunk_tokens <= max_tokens:
                trimmed_chunks.append(chunk)
                total_tokens += chunk_tokens
            else:
                break

        return trimmed_chunks

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        if not text:
            return 0
        # Rough estimation: ~4 characters per token
        return max(1, len(text) // self.chars_per_token)

    async def cache_session_context(
        self,
        session_id: str,
        context: Dict[str, Any],
        ttl_seconds: Optional[int] = None,
    ) -> bool:
        """Cache context for recent sessions to speed hot-paths."""
        try:
            ttl = ttl_seconds or self.session_cache_ttl

            # Create session cache entry
            cache_entry = {
                "session_id": session_id,
                "context": json.dumps(context),
                "created_at": datetime.now().isoformat(),
                "ttl_seconds": ttl,
                "expires_at": (datetime.now() + timedelta(seconds=ttl)).isoformat(),
            }

            # Generate embedding for session context (for potential similarity search)
            context_text = f"{context.get('query', '')} {' '.join([c.get('text', '')[:100] for c in context.get('chunks', [])])}"
            embedding = self.embedding_model.encode(context_text).tolist()

            # Store in sessions collection
            self.sessions_collection.add(
                ids=[session_id],
                embeddings=[embedding],
                documents=[context_text],
                metadatas=[cache_entry],
            )

            logger.info(f"Cached session context for {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to cache session: {e}")
            return False

    async def get_cached_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached session context if still valid."""
        try:
            results = self.sessions_collection.get(ids=[session_id])

            if not results["metadatas"]:
                return None

            metadata = results["metadatas"][0]

            # Check if expired
            expires_at = datetime.fromisoformat(metadata["expires_at"])
            if datetime.now() > expires_at:
                # Clean up expired cache
                self.sessions_collection.delete(ids=[session_id])
                return None

            # Return cached context
            return json.loads(metadata["context"])

        except Exception as e:
            logger.error(f"Failed to get cached session: {e}")
            return None

    async def generate_rag_prompt(
        self, query: str, context: Dict[str, Any], max_context_tokens: int = 8000
    ) -> str:
        """Generate RAG-enhanced prompt with retrieved context."""
        chunks = context.get("chunks", [])

        if not chunks:
            # No context available, return basic prompt
            return f"Query: {query}\n\nPlease provide a helpful response."

        # Build context from chunks
        context_parts = []
        total_tokens = 0

        for chunk in chunks:
            chunk_text = chunk["text"]
            chunk_tokens = self._estimate_tokens(chunk_text)

            if total_tokens + chunk_tokens > max_context_tokens:
                break

            context_parts.append(chunk_text)
            total_tokens += chunk_tokens

        full_context = "\n\n".join(context_parts)

        # Create RAG prompt
        rag_prompt = f"""You are a helpful AI assistant with access to relevant context information.

Context Information:
{full_context}

Query: {query}

Instructions:
- Use the provided context to inform your response
- If the context doesn't contain relevant information, say so clearly
- Be accurate and helpful
- Cite specific information from the context when relevant

Response:"""

        return rag_prompt

    async def rag_pipeline(
        self,
        query: str,
        session_id: Optional[str] = None,
        filters: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Complete RAG pipeline: retrieve → filter → generate prompt."""
        # Check session cache first (hot-path optimization)
        if session_id:
            cached_context = await self.get_cached_session(session_id)
            if cached_context:
                logger.info(f"Using cached context for session {session_id}")
                prompt = await self.generate_rag_prompt(query, cached_context)
                return {
                    "prompt": prompt,
                    "context": cached_context,
                    "cached": True,
                    "session_id": session_id,
                }

        # Perform retrieval
        context = await self.retrieve_context(query, filters=filters)

        # Cache for future use if session_id provided
        if session_id and context.get("chunks"):
            await self.cache_session_context(
                session_id,
                {
                    "query": query,
                    "chunks": context["chunks"],
                    "timestamp": datetime.now().isoformat(),
                },
            )

        # Generate RAG prompt
        prompt = await self.generate_rag_prompt(query, context)

        return {
            "prompt": prompt,
            "context": context,
            "cached": False,
            "session_id": session_id,
        }
