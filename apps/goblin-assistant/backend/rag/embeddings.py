"""
Embedding Service
Generate embeddings for documents and queries
"""

from typing import Optional

import structlog
from sentence_transformers import SentenceTransformer

logger = structlog.get_logger()


class EmbeddingService:
    """
    Embedding service using Sentence Transformers.

    Default model: paraphrase-multilingual-MiniLM-L12-v2 (384 dims, multilingual)
    Alternative: all-mpnet-base-v2 (768 dims, higher quality)
    """

    # Model options with dimensions
    MODELS = {
        "all-MiniLM-L6-v2": 384,  # Fast, good for most use cases
        "all-mpnet-base-v2": 768,  # Higher quality
        "paraphrase-multilingual-MiniLM-L12-v2": 384,  # Multilingual
    }

    def __init__(
        self,
        model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
        device: Optional[str] = None,
    ):
        self.model_name = model_name
        self.embedding_dim = self.MODELS.get(model_name, 384)

        logger.info("Loading embedding model", model=model_name)
        self.model = SentenceTransformer(
            model_name,
            device=device,  # Auto-detect if None
        )
        logger.info("Embedding model loaded", dim=self.embedding_dim)

    def embed_text(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text

        Returns:
            Embedding vector
        """
        embedding = self.model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return embedding.tolist()

    def embed_batch(
        self,
        texts: list[str],
        batch_size: int = 32,
        show_progress: bool = False,
    ) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of input texts
            batch_size: Batch size for encoding
            show_progress: Show progress bar

        Returns:
            List of embedding vectors
        """
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=show_progress,
        )
        return embeddings.tolist()

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return self.embedding_dim


# Singleton instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service(
    model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
) -> EmbeddingService:
    """Get or create embedding service singleton."""
    global _embedding_service
    if _embedding_service is None or _embedding_service.model_name != model_name:
        _embedding_service = EmbeddingService(model_name=model_name)
    return _embedding_service
