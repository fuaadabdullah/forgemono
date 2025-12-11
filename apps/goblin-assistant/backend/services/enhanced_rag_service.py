"""
Enhanced RAG (Retrieval-Augmented Generation) Service
Implements advanced RAG with multiple embedding models, hybrid search, reranking, and query expansion.

Features:
- Multiple embedding models for different content types (general, code, multilingual, medical)
- Hybrid search combining dense retrieval (ChromaDB) with sparse retrieval (BM25)
- CrossEncoder reranking for improved result quality
- Query expansion with synonyms, related terms, and acronym expansion
- Extended context window support (10k tokens)
- Session-based caching for hot-paths
"""

import hashlib
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Lazy imports for optional dependencies
try:
    import chromadb

    CHROMADB_AVAILABLE = True
except (ImportError, Exception) as e:
    chromadb = None
    CHROMADB_AVAILABLE = False
    logger.warning(f"ChromaDB not available: {e}")

try:
    import numpy as np
    from sentence_transformers import SentenceTransformer, CrossEncoder
    from rank_bm25 import BM25Okapi
    import nltk
    from nltk.corpus import wordnet

    # Download required NLTK data
    try:
        nltk.data.find("corpora/wordnet")
    except LookupError:
        nltk.download("wordnet", quiet=True)

    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        nltk.download("punkt", quiet=True)

    # Check if we have both sentence-transformers AND ChromaDB for full mode
    if CHROMADB_AVAILABLE:
        ENHANCED_RAG_AVAILABLE = True
        logger.info("Full enhanced RAG available (sentence-transformers + ChromaDB)")
    else:
        ENHANCED_RAG_AVAILABLE = "fallback"
        logger.info("Using TF-IDF fallback for enhanced RAG (ChromaDB not available)")
except ImportError:
    # Fallback imports for when torch/sentence-transformers are not available
    try:
        import numpy as np
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        import re

        ENHANCED_RAG_AVAILABLE = "fallback"
        logger.info("Using TF-IDF fallback for enhanced RAG (torch not available)")
    except ImportError:
        ENHANCED_RAG_AVAILABLE = False
        logger.warning(
            "Enhanced RAG dependencies not available. Enhanced features will be disabled."
        )


class HybridRetriever:
    """Hybrid retriever combining dense and sparse retrieval with fusion."""

    def __init__(
        self,
        dense_retriever,
        sparse_retriever,
        fusion_algorithm: str = "reciprocal_rank_fusion",
    ):
        self.dense_retriever = dense_retriever
        self.sparse_retriever = sparse_retriever
        self.fusion_algorithm = fusion_algorithm

    def retrieve(self, query: str, top_k: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """Retrieve documents using hybrid search."""
        # Get results from both retrievers
        dense_results = self.dense_retriever.retrieve(query, top_k=top_k, **kwargs)
        sparse_results = self.sparse_retriever.retrieve(query, top_k=top_k, **kwargs)

        if self.fusion_algorithm == "reciprocal_rank_fusion":
            return self._reciprocal_rank_fusion(dense_results, sparse_results, top_k)
        else:
            # Simple concatenation and reranking
            combined = dense_results + sparse_results
            return sorted(combined, key=lambda x: x.get("score", 0), reverse=True)[
                :top_k
            ]

    def _reciprocal_rank_fusion(
        self, dense_results: List[Dict], sparse_results: List[Dict], k: int = 60
    ) -> List[Dict]:
        """Combine results using Reciprocal Rank Fusion."""
        # Create score dictionaries
        dense_scores = {
            doc.get("id", f"dense_{rank}"): 1.0 / (rank + k)
            for rank, doc in enumerate(dense_results)
        }
        sparse_scores = {
            doc.get("id", f"sparse_{rank}"): 1.0 / (rank + k)
            for rank, doc in enumerate(sparse_results)
        }

        # Combine scores
        all_ids = set(dense_scores.keys()) | set(sparse_scores.keys())
        fused_scores = {}

        for doc_id in all_ids:
            dense_score = dense_scores.get(doc_id, 0)
            sparse_score = sparse_scores.get(doc_id, 0)
            fused_scores[doc_id] = dense_score + sparse_score

        # Sort by fused scores
        sorted_ids = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)

        # Reconstruct results
        fused_results = []
        for doc_id, score in sorted_ids[
            : len(dense_results)
        ]:  # Return similar number of results
            # Find original document
            doc = None
            for d in dense_results:
                if d.get("id") == doc_id:
                    doc = d
                    break
            if not doc:
                for d in sparse_results:
                    if d.get("id") == doc_id:
                        doc = d
                        break

            if doc:
                doc_copy = doc.copy()
                doc_copy["hybrid_score"] = score
                fused_results.append(doc_copy)

        return fused_results


class BM25Retriever:
    """Sparse retriever using BM25 algorithm."""

    def __init__(self):
        self.documents = []
        self.bm25 = None
        self.doc_ids = []

    def add_documents(self, documents: List[Dict[str, Any]]):
        """Add documents to the BM25 index."""
        try:
            self.documents = documents
            self.doc_ids = [doc.get("id", i) for i, doc in enumerate(documents)]

            # Tokenize documents for BM25
            tokenized_docs = [self._tokenize(doc.get("text", "")) for doc in documents]
            self.bm25 = BM25Okapi(tokenized_docs)
        except NameError:
            # BM25Okapi not available, store documents for basic retrieval
            logger.warning("BM25Okapi not available, using basic text matching")
            self.documents = documents
            self.doc_ids = [doc.get("id", i) for i, doc in enumerate(documents)]
            self.bm25 = None

    def retrieve(self, query: str, top_k: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """Retrieve documents using BM25."""
        if not self.bm25:
            # Fallback to simple text matching
            return self._simple_text_retrieval(query, top_k)

        try:
            tokenized_query = self._tokenize(query)
            scores = self.bm25.get_scores(tokenized_query)

            # Get top-k results
            top_indices = np.argsort(scores)[::-1][:top_k]

            results = []
            for idx in top_indices:
                if scores[idx] > 0:  # Only include relevant results
                    doc = self.documents[idx].copy()
                    doc["id"] = self.doc_ids[idx]
                    doc["score"] = float(scores[idx])
                    doc["retrieval_type"] = "sparse"
                    results.append(doc)

            return results
        except NameError:
            # numpy not available, fallback to simple text matching
            return self._simple_text_retrieval(query, top_k)

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization for BM25."""
        # Convert to lowercase and split on whitespace and punctuation
        return re.findall(r"\b\w+\b", text.lower())

    def _simple_text_retrieval(
        self, query: str, top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Fallback retrieval using simple text matching when BM25 is not available."""
        query_lower = query.lower()
        results = []

        for i, doc in enumerate(self.documents):
            text = doc.get("text", "").lower()
            # Simple scoring based on word overlap
            query_words = set(self._tokenize(query_lower))
            text_words = set(self._tokenize(text))
            overlap = len(query_words.intersection(text_words))

            if overlap > 0:
                score = overlap / len(query_words)  # Normalized score
                doc_copy = doc.copy()
                doc_copy["id"] = self.doc_ids[i]
                doc_copy["score"] = score
                doc_copy["retrieval_type"] = "simple_text"
                results.append(doc_copy)

        # Sort by score and return top-k
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]


class TfidfEmbedder:
    """Fallback embedder using TF-IDF vectorization when sentence-transformers is not available."""

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=1000,  # Limit vocabulary size
            stop_words="english",
            ngram_range=(1, 2),  # Include bigrams
            min_df=1,
            max_df=1.0,  # Allow all documents
        )
        self.documents = []
        self.doc_ids = []
        self.tfidf_matrix = None
        self.is_fitted = False

    def add_documents(self, documents: List[Dict[str, Any]]):
        """Add documents to the TF-IDF index."""
        self.documents = documents
        self.doc_ids = [doc.get("id", i) for i, doc in enumerate(documents)]

        # Extract text content
        texts = [doc.get("text", doc.get("content", "")) for doc in documents]

        # Fit and transform
        self.tfidf_matrix = self.vectorizer.fit_transform(texts)
        self.is_fitted = True

    def encode(self, texts: List[str]) -> np.ndarray:
        """Encode texts to TF-IDF vectors."""
        if not self.is_fitted:
            raise ValueError("TF-IDF embedder must be fitted with documents first")

        if isinstance(texts, str):
            texts = [texts]

        # Transform query using existing vocabulary
        vectors = self.vectorizer.transform(texts)
        return vectors.toarray()

    def retrieve(self, query: str, top_k: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """Retrieve documents using TF-IDF similarity."""
        if not self.is_fitted or self.tfidf_matrix is None:
            return []

        # Encode query
        query_vector = self.encode([query])

        # Calculate cosine similarities
        similarities = cosine_similarity(query_vector, self.tfidf_matrix)[0]

        # Get top-k results
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            if similarities[idx] > 0:  # Only include relevant results
                doc = self.documents[idx].copy()
                doc["id"] = self.doc_ids[idx]
                doc["score"] = float(similarities[idx])
                doc["retrieval_type"] = "tfidf"
                results.append(doc)

        return results


class QueryExpansion:
    """Query expansion using various strategies."""

    def __init__(self, llm_backend=None):
        self.llm = llm_backend

    async def expand_query(self, query: str, strategies: List[str] = None) -> List[str]:
        """Expand query using multiple strategies."""
        if strategies is None:
            strategies = ["synonyms", "related_terms"]

        expanded_queries = [query]  # Always include original

        for strategy in strategies:
            if strategy == "synonyms":
                expanded_queries.extend(self._expand_synonyms(query))
            elif strategy == "related_terms":
                expanded_queries.extend(await self._expand_related_terms(query))
            elif strategy == "acronyms":
                expanded_queries.extend(self._expand_acronyms(query))

        # Remove duplicates and limit
        expanded_queries = list(set(expanded_queries))[:5]  # Max 5 expanded queries
        return expanded_queries

    def _expand_synonyms(self, query: str) -> List[str]:
        """Expand query with synonyms using WordNet."""
        try:
            words = query.split()
            expanded = []

            for word in words:
                synonyms = []
                for syn in wordnet.synsets(word):
                    for lemma in syn.lemmas():
                        synonym = lemma.name().replace("_", " ")
                        if synonym != word and synonym not in synonyms:
                            synonyms.append(synonym)

                # Create variations with synonyms
                for synonym in synonyms[:3]:  # Limit synonyms per word
                    new_query = query.replace(word, synonym)
                    if new_query != query:
                        expanded.append(new_query)

            return expanded
        except NameError:
            # WordNet not available, return empty list
            logger.warning("WordNet not available for synonym expansion")
            return []

    async def _expand_related_terms(self, query: str) -> List[str]:
        """Expand query with related terms using LLM if available."""
        if not self.llm:
            return []

        try:
            prompt = f"""Given the query: "{query}"

Generate 2-3 related search terms or phrases that could help find relevant information.
Focus on technical terms, related concepts, or alternative phrasings.

Return only the terms/phrases, one per line, no explanations."""

            response = await self.llm.generate(prompt, max_tokens=100)
            terms = [line.strip() for line in response.split("\n") if line.strip()]
            return terms[:3]
        except Exception as e:
            logger.warning(f"Failed to expand query with LLM: {e}")
            return []

    def _expand_acronyms(self, query: str) -> List[str]:
        """Expand common acronyms in the query."""
        acronym_map = {
            "api": "application programming interface",
            "llm": "large language model",
            "rag": "retrieval augmented generation",
            "ml": "machine learning",
            "ai": "artificial intelligence",
            "nlp": "natural language processing",
            "db": "database",
            "sql": "structured query language",
            "http": "hypertext transfer protocol",
            "json": "javascript object notation",
            "xml": "extensible markup language",
        }

        words = query.lower().split()
        expanded = []

        for acronym, expansion in acronym_map.items():
            if acronym in words:
                new_query = query.replace(acronym, expansion)
                expanded.append(new_query)

        return expanded


class EnhancedRAGService:
    """Enhanced RAG service with multiple embedding models, hybrid search, and reranking."""

    def __init__(self, chroma_path: str = "data/vector/chroma"):
        """Initialize enhanced RAG service."""
        if not ENHANCED_RAG_AVAILABLE:
            logger.error(
                "Enhanced RAG dependencies not available. Cannot initialize enhanced service."
            )
            self.chroma_client = None
            self.embedders = {}
            self.embedding_model = None
            self.reranker = None
            self.query_expander = None
            self.dense_retriever = None
            self.sparse_retriever = None
            self.hybrid_retriever = None
            self.documents_collection = None
            self.sessions_collection = None
            return

        # Check if we're using fallback mode or if ChromaDB is not available
        if ENHANCED_RAG_AVAILABLE == "fallback" or not CHROMADB_AVAILABLE:
            # Use TF-IDF fallback embedder
            self.embedders = {
                "general": TfidfEmbedder(),
                "code": TfidfEmbedder(),
                "multilingual": TfidfEmbedder(),
                "medical": TfidfEmbedder(),
            }
            self.embedding_model = self.embedders["general"]
            self.reranker = None  # No reranking in fallback mode
            self.chroma_client = None  # No ChromaDB in fallback mode
            self.documents_collection = None
            self.sessions_collection = None
            logger.info(
                "Using TF-IDF fallback for enhanced RAG features (ChromaDB not available)"
            )
        else:
            # Full enhanced RAG with sentence-transformers and ChromaDB
            self.chroma_path = chroma_path
            self.chroma_client = chromadb.PersistentClient(path=chroma_path)

            # Multiple embedding models for different content types
            self.embedders = {
                "general": SentenceTransformer(
                    "all-MiniLM-L6-v2"
                ),  # Fast, general purpose
                "code": SentenceTransformer("microsoft/codebert-base"),  # Code-specific
                "multilingual": SentenceTransformer(
                    "paraphrase-multilingual-MiniLM-L12-v2"
                ),  # Multilingual
                "medical": SentenceTransformer(
                    "medical-bert-uncased"
                ),  # Medical domain
            }

            # Default to general embedder
            self.embedding_model = self.embedders["general"]

            # Reranking model
            self.reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

            # Create/get collections
            self.documents_collection = self.chroma_client.get_or_create_collection(
                name="enhanced_documents",
                metadata={
                    "description": "Enhanced document chunks with multiple embeddings"
                },
            )

            self.sessions_collection = self.chroma_client.get_or_create_collection(
                name="enhanced_sessions",
                metadata={
                    "description": "Enhanced session cache with multi-modal support"
                },
            )

        # Query expansion (works in both modes)
        self.query_expander = QueryExpansion()

        # Hybrid search components
        self.dense_retriever = None  # Will be initialized with documents
        self.sparse_retriever = BM25Retriever()
        self.hybrid_retriever = None

        # Configuration
        self.max_retriever_tokens = 10000  # 10k token window
        self.chunk_size = 512  # tokens per chunk
        self.chunk_overlap = 50  # token overlap
        self.max_chunks = 20  # Maximum chunks to retrieve initially
        self.rerank_top_k = 10  # Number of docs to rerank
        self.session_cache_ttl = 3600  # 1 hour

        # Token estimation
        self.chars_per_token = 4

    def _select_embedder(self, content_type: str = "general"):
        """Select appropriate embedding model based on content type."""
        return self.embedders.get(content_type, self.embedders["general"])

    async def add_documents(
        self,
        documents: List[Dict[str, Any]],
        collection_name: str = "enhanced_documents",
        content_type: str = "general",
    ) -> bool:
        """Add documents with multiple embedding support."""
        try:
            # Handle fallback mode (no ChromaDB)
            if ENHANCED_RAG_AVAILABLE == "fallback":
                embedder = self._select_embedder(content_type)
                if isinstance(embedder, TfidfEmbedder):
                    # For TF-IDF, add documents directly to the embedder
                    embedder.add_documents(documents)
                    # Update sparse retriever for hybrid search
                    sparse_docs = [
                        {
                            "id": doc.get("id", i),
                            "text": doc.get("content", doc.get("text", "")),
                        }
                        for i, doc in enumerate(documents)
                    ]
                    self.sparse_retriever.add_documents(sparse_docs)
                    # Initialize hybrid retriever
                    self.dense_retriever = embedder
                    self.hybrid_retriever = HybridRetriever(
                        self.dense_retriever, self.sparse_retriever
                    )
                    logger.info(
                        f"Added {len(documents)} documents with TF-IDF embeddings to {collection_name}"
                    )
                    return True
                else:
                    logger.error("Unsupported embedder type in fallback mode")
                    return False

            # Full mode with ChromaDB
            collection = self.chroma_client.get_or_create_collection(
                name=collection_name
            )

            # Select appropriate embedder
            embedder = self._select_embedder(content_type)

            all_chunks = []
            all_embeddings = []
            all_metadatas = []
            all_ids = []

            for doc in documents:
                doc_id = doc.get("id", hashlib.md5(doc["content"].encode()).hexdigest())
                content = doc["content"]
                metadata = doc.get("metadata", {})

                # Chunk the document
                chunks = self._chunk_text(content, self.chunk_size, self.chunk_overlap)

                for i, chunk in enumerate(chunks):
                    chunk_id = f"{doc_id}_chunk_{i}"
                    chunk_metadata = {
                        **metadata,
                        "doc_id": doc_id,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "content_type": content_type,
                        "chunk_text": chunk[:200],
                    }

                    all_chunks.append(chunk)
                    all_metadatas.append(chunk_metadata)
                    all_ids.append(chunk_id)

            # Handle different embedder types
            if ENHANCED_RAG_AVAILABLE == "fallback" and isinstance(
                embedder, TfidfEmbedder
            ):
                # For TF-IDF, we need to fit on all chunks first
                embedder.add_documents(
                    [
                        {"text": chunk, "id": chunk_id}
                        for chunk, chunk_id in zip(all_chunks, all_ids)
                    ]
                )

                # Then encode each chunk
                for chunk in all_chunks:
                    embedding = embedder.encode([chunk]).tolist()[0]
                    all_embeddings.append(embedding)
            else:
                # Standard sentence-transformers encoding
                for chunk in all_chunks:
                    embedding = embedder.encode(chunk).tolist()
                    all_embeddings.append(embedding)

            # Add to collection
            collection.add(
                ids=all_ids,
                embeddings=all_embeddings,
                documents=all_chunks,
                metadatas=all_metadatas,
            )

            # Update sparse retriever for hybrid search
            sparse_docs = [
                {"id": chunk_id, "text": chunk}
                for chunk_id, chunk in zip(all_ids, all_chunks)
            ]
            self.sparse_retriever.add_documents(sparse_docs)

            # Initialize hybrid retriever
            self.dense_retriever = self
            self.hybrid_retriever = HybridRetriever(
                self.dense_retriever, self.sparse_retriever
            )

            logger.info(
                f"Added {len(documents)} documents with {content_type} embeddings to {collection_name}"
            )
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
            chunk_end = min(i + chunk_size, len(words))
            chunk_words = words[i:chunk_end]
            chunk = " ".join(chunk_words)
            chunks.append(chunk)

            i += chunk_size - overlap
            if chunk_end == len(words):
                break

        return chunks

    def retrieve(self, query: str, top_k: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """Dense retrieval method for hybrid search compatibility."""
        try:
            # Handle fallback mode
            if ENHANCED_RAG_AVAILABLE == "fallback":
                embedder = self.embedders.get("general")
                if isinstance(embedder, TfidfEmbedder):
                    return embedder.retrieve(query, top_k=top_k)
                else:
                    return []

            # Full mode with ChromaDB
            # Generate query embedding (use general embedder for queries)
            query_embedding = self.embedders["general"].encode(query).tolist()

            # Search collection
            results = self.documents_collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
            )

            if not results["documents"]:
                return []

            # Format results
            formatted_results = []
            for i, (doc, metadata, distance) in enumerate(
                zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0],
                )
            ):
                formatted_results.append(
                    {
                        "id": results["ids"][0][i],
                        "text": doc,
                        "metadata": metadata,
                        "score": 1.0
                        / (1.0 + distance),  # Convert distance to similarity
                        "distance": distance,
                        "retrieval_type": "dense",
                    }
                )

            return formatted_results

        except Exception as e:
            logger.error(f"Dense retrieval failed: {e}")
            return []

    async def retrieve_context(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict] = None,
        use_hybrid: bool = True,
        use_reranking: bool = True,
        expand_query: bool = True,
    ) -> Dict[str, Any]:
        """Enhanced retrieval with hybrid search, reranking, and query expansion."""
        try:
            # Query expansion
            if expand_query:
                expanded_queries = await self.query_expander.expand_query(query)
                logger.info(f"Expanded query to {len(expanded_queries)} variations")
            else:
                expanded_queries = [query]

            all_results = []

            # Retrieve using multiple query variations
            for q in expanded_queries:
                if use_hybrid and self.hybrid_retriever:
                    # Hybrid search
                    results = self.hybrid_retriever.retrieve(
                        q, top_k=top_k, filters=filters
                    )
                else:
                    # Dense-only search
                    results = self.retrieve(q, top_k=top_k)

                all_results.extend(results)

            # Remove duplicates and sort by score
            seen_ids = set()
            unique_results = []
            for result in all_results:
                doc_id = result.get("id")
                if doc_id not in seen_ids:
                    unique_results.append(result)
                    seen_ids.add(doc_id)

            unique_results.sort(key=lambda x: x.get("score", 0), reverse=True)
            candidates = unique_results[: self.rerank_top_k]

            # Reranking
            if use_reranking and len(candidates) > 1:
                reranked_results = self._rerank_results(query, candidates)
            else:
                reranked_results = candidates

            # Filter and rank final results
            filtered_chunks = self._filter_and_rank_chunks(query, reranked_results)

            # Trim to token limit
            total_tokens = sum(
                self._estimate_tokens(chunk["text"]) for chunk in filtered_chunks
            )
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
                "query_expansions": len(expanded_queries),
                "hybrid_search": use_hybrid,
                "reranking": use_reranking,
            }

        except Exception as e:
            logger.error(f"Enhanced retrieval failed: {e}")
            return {
                "chunks": [],
                "total_tokens": 0,
                "filtered_count": 0,
                "error": str(e),
            }

    def _rerank_results(
        self, query: str, candidates: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Rerank candidates using CrossEncoder."""
        try:
            # Prepare pairs for reranking
            pairs = [[query, doc["text"]] for doc in candidates]

            # Get reranking scores
            scores = self.reranker.predict(pairs)

            # Update scores
            for doc, score in zip(candidates, scores):
                doc["rerank_score"] = float(score)

            # Sort by reranking score
            candidates.sort(key=lambda x: x["rerank_score"], reverse=True)

            return candidates

        except Exception as e:
            logger.warning(f"Reranking failed: {e}")
            return candidates

    def _filter_and_rank_chunks(
        self, query: str, documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Filter and rank chunks based on relevance."""
        chunks = []

        for doc in documents:
            # Calculate relevance score
            base_score = doc.get("rerank_score", doc.get("score", 0))

            # Additional term overlap scoring
            query_terms = set(query.lower().split())
            doc_terms = set(doc.get("text", "").lower().split())
            term_overlap = (
                len(query_terms.intersection(doc_terms)) / len(query_terms)
                if query_terms
                else 0
            )

            # Boost score for term overlap
            combined_score = base_score * (1 + term_overlap)

            chunks.append(
                {
                    "text": doc.get("text", ""),
                    "metadata": doc.get("metadata", {}),
                    "relevance_score": combined_score,
                    "term_overlap": term_overlap,
                    "retrieval_type": doc.get("retrieval_type", "unknown"),
                    "rerank_score": doc.get("rerank_score"),
                }
            )

        # Sort by combined score
        chunks.sort(key=lambda x: x["relevance_score"], reverse=True)
        return chunks[: self.max_chunks]

    def _trim_to_token_limit(
        self, chunks: List[Dict[str, Any]], max_tokens: int
    ) -> List[Dict[str, Any]]:
        """Trim chunks to fit within token limit."""
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
        return max(1, len(text) // self.chars_per_token)

    async def cache_session_context(
        self,
        session_id: str,
        context: Dict[str, Any],
        ttl_seconds: Optional[int] = None,
    ) -> bool:
        """Cache context for recent sessions."""
        try:
            ttl = ttl_seconds or self.session_cache_ttl

            cache_entry = {
                "session_id": session_id,
                "context": json.dumps(context),
                "created_at": datetime.now().isoformat(),
                "ttl_seconds": ttl,
                "expires_at": (datetime.now() + timedelta(seconds=ttl)).isoformat(),
            }

            # Create embedding for session context
            context_text = f"{context.get('query', '')} {' '.join([c.get('text', '')[:100] for c in context.get('chunks', [])])}"
            embedding = self.embedders["general"].encode(context_text).tolist()

            self.sessions_collection.add(
                ids=[session_id],
                embeddings=[embedding],
                documents=[context_text],
                metadatas=[cache_entry],
            )

            logger.info(f"Cached enhanced session context for {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to cache session: {e}")
            return False

    async def get_cached_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached session context."""
        try:
            results = self.sessions_collection.get(ids=[session_id])

            if not results["metadatas"]:
                return None

            metadata = results["metadatas"][0]

            # Check expiration
            expires_at = datetime.fromisoformat(metadata["expires_at"])
            if datetime.now() > expires_at:
                self.sessions_collection.delete(ids=[session_id])
                return None

            return json.loads(metadata["context"])

        except Exception as e:
            logger.error(f"Failed to get cached session: {e}")
            return None

    async def generate_rag_prompt(
        self, query: str, context: Dict[str, Any], max_context_tokens: int = 8000
    ) -> str:
        """Generate enhanced RAG prompt with retrieved context."""
        chunks = context.get("chunks", [])

        if not chunks:
            return f"Query: {query}\n\nPlease provide a helpful response."

        # Build context with metadata
        context_parts = []
        total_tokens = 0

        for chunk in chunks:
            chunk_text = chunk["text"]
            chunk_tokens = self._estimate_tokens(chunk_text)

            if total_tokens + chunk_tokens > max_context_tokens:
                break

            # Add metadata info
            metadata = chunk.get("metadata", {})
            source_info = ""
            if metadata.get("source"):
                source_info = f" [Source: {metadata['source']}]"
            if metadata.get("content_type"):
                source_info += f" [Type: {metadata['content_type']}]"

            context_parts.append(f"{chunk_text}{source_info}")
            total_tokens += chunk_tokens

        full_context = "\n\n".join(context_parts)

        # Enhanced RAG prompt
        rag_prompt = f"""You are an advanced AI assistant with access to comprehensive context information retrieved using state-of-the-art RAG techniques.

Context Information (Retrieved via Hybrid Search + Reranking):
{full_context}

Query: {query}

Instructions:
- Use the provided context to inform your response with specific details
- If the context doesn't contain relevant information, clearly state this
- Be accurate, helpful, and cite specific information from the context
- Consider the source types and content domains when formulating your response
- If multiple perspectives exist in the context, acknowledge them

Response:"""

        return rag_prompt

    async def enhanced_rag_pipeline(
        self,
        query: str,
        session_id: Optional[str] = None,
        filters: Optional[Dict] = None,
        use_hybrid: bool = True,
        use_reranking: bool = True,
        expand_query: bool = True,
    ) -> Dict[str, Any]:
        """Complete enhanced RAG pipeline with all advanced features."""
        # Check session cache first
        if session_id:
            try:
                cached_context = await self.get_cached_session(session_id)
                if cached_context:
                    logger.info(f"Using cached context for session {session_id}")
                    prompt = await self.generate_rag_prompt(query, cached_context)
                    return {
                        "prompt": prompt,
                        "context": cached_context,
                        "cached": True,
                        "session_id": session_id,
                        "features_used": ["session_cache"],
                    }
            except Exception as e:
                logger.warning(f"Session cache not available: {e}")

        # Perform enhanced retrieval
        context = await self.retrieve_context(
            query,
            filters=filters,
            use_hybrid=use_hybrid,
            use_reranking=use_reranking,
            expand_query=expand_query,
        )

        # Cache for future use
        if session_id and context.get("chunks"):
            try:
                await self.cache_session_context(
                    session_id,
                    {
                        "query": query,
                        "chunks": context["chunks"],
                        "timestamp": datetime.now().isoformat(),
                        "features_used": {
                            "hybrid_search": use_hybrid,
                            "reranking": use_reranking,
                            "query_expansion": expand_query,
                        },
                    },
                )
            except Exception as e:
                logger.warning(f"Session cache not available: {e}")

        # Generate enhanced RAG prompt
        prompt = await self.generate_rag_prompt(query, context)

        features_used = []
        if use_hybrid:
            features_used.append("hybrid_search")
        if use_reranking:
            features_used.append("reranking")
        if expand_query:
            features_used.append("query_expansion")

        return {
            "prompt": prompt,
            "context": context,
            "cached": False,
            "session_id": session_id,
            "features_used": features_used,
        }

    def _filter_and_rank_chunks(
        self, query: str, chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Filter and rank chunks based on relevance."""
        if not chunks:
            return []

        # For fallback mode, chunks already have scores from TF-IDF
        if ENHANCED_RAG_AVAILABLE == "fallback":
            return chunks

        # For full mode, apply additional filtering
        filtered_chunks = []
        for chunk in chunks:
            # Additional relevance scoring
            text = chunk.get("text", "")
            score = chunk.get("score", 0)

            # Boost score for exact query term matches
            query_terms = set(query.lower().split())
            chunk_terms = set(text.lower().split())
            term_overlap = (
                len(query_terms.intersection(chunk_terms)) / len(query_terms)
                if query_terms
                else 0
            )

            # Combined score
            combined_score = score * (1 + term_overlap)
            chunk["relevance_score"] = combined_score
            filtered_chunks.append(chunk)

        # Sort by score
        filtered_chunks.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        return filtered_chunks[: self.max_chunks]

    def _trim_to_token_limit(
        self, chunks: List[Dict[str, Any]], max_tokens: int
    ) -> List[Dict[str, Any]]:
        """Trim chunks to fit within token limit."""
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

    def _rerank_results(
        self, query: str, chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Rerank results using CrossEncoder (fallback: no reranking)."""
        if ENHANCED_RAG_AVAILABLE == "fallback" or not self.reranker:
            return chunks  # No reranking in fallback mode

        try:
            # Prepare pairs for reranking
            pairs = [[query, chunk["text"]] for chunk in chunks]
            scores = self.reranker.predict(pairs)

            # Update scores
            for chunk, score in zip(chunks, scores):
                chunk["score"] = float(score)
                chunk["reranked"] = True

            # Sort by reranked score
            chunks.sort(key=lambda x: x.get("score", 0), reverse=True)
            return chunks

        except Exception as e:
            logger.warning(f"Reranking failed: {e}")
            return chunks
