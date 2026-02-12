from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import re
import sys
from pathlib import Path

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from database import get_db
from models_base import SearchCollection, SearchDocument

router = APIRouter(prefix="/search", tags=["search"])


class SearchQuery(BaseModel):
    query: str
    collection_name: str = "documents"
    n_results: int = 10


class SearchResult(BaseModel):
    id: str
    document: str
    metadata: Optional[Dict[str, Any]] = None
    score: Optional[float] = None


class SearchResponse(BaseModel):
    results: List[SearchResult]
    total_results: int


def simple_text_search(
    query: str, documents: List[SearchDocument], n_results: int = 10
) -> List[Dict]:
    """Simple text-based search implementation"""
    query_lower = query.lower()
    scored_docs = []

    for doc in documents:
        text = doc.document.lower()
        score = 0

        # Simple scoring based on word matches
        query_words = query_lower.split()
        for word in query_words:
            if word in text:
                score += 1

        # Boost score for exact phrase matches
        if query_lower in text:
            score += 10

        if score > 0:
            scored_docs.append(
                {
                    "id": doc.document_id,
                    "document": doc.document,
                    "metadata": doc.document_metadata or {},
                    "score": score,
                }
            )

    # Sort by score and return top results
    scored_docs.sort(key=lambda x: x["score"], reverse=True)
    return scored_docs[:n_results]


@router.post("/query", response_model=SearchResponse)
async def search_documents(search_query: SearchQuery, db: Session = Depends(get_db)):
    """Search documents using simple text search"""
    try:
        collection_name = search_query.collection_name

        # Get or create collection
        collection = (
            db.query(SearchCollection)
            .filter(SearchCollection.name == collection_name)
            .first()
        )

        if not collection:
            return SearchResponse(results=[], total_results=0)

        # Get all documents in collection
        documents = (
            db.query(SearchDocument)
            .filter(SearchDocument.collection_id == collection.id)
            .all()
        )

        if not documents:
            return SearchResponse(results=[], total_results=0)

        # Perform search
        results = simple_text_search(
            search_query.query, documents, search_query.n_results
        )

        # Format results
        search_results = []
        for result in results:
            search_results.append(
                SearchResult(
                    id=result["id"],
                    document=result["document"],
                    metadata=result["metadata"],
                    score=result["score"],
                )
            )

        return SearchResponse(results=search_results, total_results=len(search_results))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/collections")
async def list_collections(db: Session = Depends(get_db)):
    """List all available collections"""
    try:
        collections = db.query(SearchCollection).all()
        return {"collections": [col.name for col in collections]}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list collections: {str(e)}"
        )


@router.post("/collections/{collection_name}/add")
async def add_document(
    collection_name: str,
    document: str,
    metadata: Optional[Dict[str, Any]] = None,
    id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Add a document to a collection"""
    try:
        # Get or create collection
        collection = (
            db.query(SearchCollection)
            .filter(SearchCollection.name == collection_name)
            .first()
        )

        if not collection:
            collection = SearchCollection(name=collection_name)
            db.add(collection)
            db.commit()
            db.refresh(collection)

        # Generate document ID if not provided
        doc_count = (
            db.query(SearchDocument)
            .filter(SearchDocument.collection_id == collection.id)
            .count()
        )
        doc_id = id or f"doc_{doc_count}"

        # Create document
        db_document = SearchDocument(
            collection_id=collection.id,
            document_id=doc_id,
            document=document,
            document_metadata=metadata or {},
        )
        db.add(db_document)
        db.commit()

        return {"status": "success", "document_id": doc_id}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add document: {str(e)}")


@router.get("/collections/{collection_name}/documents")
async def get_collection_documents(collection_name: str, db: Session = Depends(get_db)):
    """Get all documents in a collection"""
    try:
        collection = (
            db.query(SearchCollection)
            .filter(SearchCollection.name == collection_name)
            .first()
        )

        if not collection:
            return {"documents": []}

        documents = (
            db.query(SearchDocument)
            .filter(SearchDocument.collection_id == collection.id)
            .all()
        )

        formatted_docs = []
        for doc in documents:
            formatted_docs.append(
                {
                    "id": doc.document_id,
                    "document": doc.document,
                    "metadata": doc.document_metadata,
                }
            )

        return {"documents": formatted_docs}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get documents: {str(e)}"
        )
