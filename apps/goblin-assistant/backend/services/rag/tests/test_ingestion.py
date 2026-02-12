"""
Unit tests for document ingestion.
"""

import pytest
from unittest.mock import Mock, AsyncMock

from ..ingestion import DocumentIngestor, chunk_text


class TestChunkText:
    """Test text chunking utility."""

    def test_chunk_text_splits_and_overlaps(self):
        text = "word " * 1200  # 1200 words
        chunks = chunk_text(text, chunk_size=100, overlap=10)
        assert len(chunks) > 1
        # Check that chunks respect size
        for chunk in chunks:
            assert len(chunk.split()) <= 100
        # Check overlap: first chunk ends with words that second starts with
        if len(chunks) > 1:
            first_words = chunks[0].split()
            second_words = chunks[1].split()
            overlap_words = first_words[-10:]  # last 10 of first
            assert overlap_words == second_words[:10]  # first 10 of second

    def test_chunk_text_no_overlap(self):
        text = "a b c d e f g h i j k"
        chunks = chunk_text(text, chunk_size=3, overlap=0)
        assert chunks == ["a b c", "d e f", "g h i", "j k"]

    def test_chunk_text_single_chunk(self):
        text = "short text"
        chunks = chunk_text(text, chunk_size=100, overlap=10)
        assert chunks == ["short text"]


class TestDocumentIngestor:
    """Test document ingestion logic."""

    @pytest.fixture
    def mock_service(self):
        """Mock EnhancedRAGService."""
        service = Mock()
        service.chroma_client = None  # Fallback mode
        service.sparse_retriever = Mock()
        service._select_embedder = Mock()
        service.dense_retriever = None
        service.hybrid_retriever = None
        return service

    @pytest.fixture
    def tfidf_embedder(self):
        """Mock TF-IDF embedder."""
        embedder = Mock()
        embedder.add_documents = Mock()
        embedder.encode = Mock(return_value=[[0.1, 0.2, 0.3]])
        return embedder

    @pytest.mark.asyncio
    async def test_add_documents_fallback_mode(self, mock_service, tfidf_embedder):
        """Test adding documents in fallback mode with TF-IDF."""
        mock_service._select_embedder.return_value = tfidf_embedder

        ingestor = DocumentIngestor(mock_service)
        documents = [{"content": "test document", "id": "doc1"}]

        result = await ingestor.add_documents(documents)

        assert result is True
        tfidf_embedder.add_documents.assert_called()
        mock_service.sparse_retriever.add_documents.assert_called()
        assert mock_service.dense_retriever == tfidf_embedder
        assert mock_service.hybrid_retriever is not None

    @pytest.mark.asyncio
    async def test_add_documents_full_mode(self, mock_service):
        """Test adding documents in full ChromaDB mode."""
        # Mock ChromaDB
        mock_collection = Mock()
        mock_collection.add = Mock()
        mock_service.chroma_client = Mock()
        mock_service.chroma_client.get_or_create_collection.return_value = mock_collection

        # Mock embedder
        embedder = Mock()
        embedder.encode = Mock(return_value=[0.1, 0.2, 0.3])
        mock_service._select_embedder.return_value = embedder

        ingestor = DocumentIngestor(mock_service)
        documents = [{"content": "test document", "id": "doc1"}]

        result = await ingestor.add_documents(documents)

        assert result is True
        mock_collection.add.assert_called()
        mock_service.sparse_retriever.add_documents.assert_called()
        assert mock_service.dense_retriever == mock_service
        assert mock_service.hybrid_retriever is not None
