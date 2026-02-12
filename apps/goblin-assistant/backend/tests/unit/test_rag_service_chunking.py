import pytest
from unittest.mock import Mock

from services import rag_service as rag_module
from services.token_accounting import TokenAccountingService


@pytest.mark.asyncio
async def test_add_documents_no_duplicate_metadata(monkeypatch):
    class _Embedding:
        def __init__(self, value):
            self._value = value

        def tolist(self):
            return self._value

    service = rag_module.RAGService.__new__(rag_module.RAGService)
    service.enable_enhanced = False
    service.chroma_client = Mock()
    mock_collection = Mock()
    service.chroma_client.get_or_create_collection.return_value = mock_collection
    service.embedding_model = Mock()
    service.embedding_model.encode.return_value = _Embedding([0.1, 0.2, 0.3])
    service.chunk_size = 3
    service.chunk_overlap = 0
    service.token_accountant = TokenAccountingService(force_fallback=True)

    monkeypatch.setattr(rag_module, "CHROMADB_AVAILABLE", True)

    documents = [{"content": "one two three four five", "id": "doc1"}]
    result = await service.add_documents(documents)

    assert result is True
    mock_collection.add.assert_called_once()

    _, kwargs = mock_collection.add.call_args
    ids = kwargs["ids"]
    metadatas = kwargs["metadatas"]
    docs = kwargs["documents"]

    assert len(ids) == len(docs)
    assert len(metadatas) == len(docs)
