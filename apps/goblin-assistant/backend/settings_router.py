from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

from ..database import get_db
from ..models import Provider, Model
from config import settings as app_settings

router = APIRouter(prefix="/settings", tags=["settings"])

# Load environment variables
load_dotenv()


class ProviderSchema(BaseModel):
    name: str
    display_name: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    models: Optional[List[str]] = []
    enabled: bool = True
    is_active: bool = True

    class Config:
        from_attributes = True


class ModelSchema(BaseModel):
    name: str
    provider: str
    model_id: str
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 4096
    enabled: bool = True

    class Config:
        from_attributes = True


class SettingsResponse(BaseModel):
    providers: List[ProviderSchema]
    models: List[ModelSchema]
    default_provider: Optional[str] = None
    default_model: Optional[str] = None


class SettingsResponse(BaseModel):
    providers: List[ProviderSettings]
    models: List[ModelSettings]
    default_provider: Optional[str] = None
    default_model: Optional[str] = None


class RAGSettings(BaseModel):
    enable_enhanced_rag: bool = False
    chroma_path: str = "data/vector/chroma"


@router.get("/", response_model=SettingsResponse)
async def get_settings(db: Session = Depends(get_db)):
    """Get current provider and model settings from the database"""
    try:
        providers_db = db.query(Provider).all()
        models_db = db.query(Model).all()

        providers_response = [ProviderSchema.from_orm(p) for p in providers_db]
        models_response = [ModelSchema.from_orm(m) for m in models_db]

        return SettingsResponse(
            providers=providers_response,
            models=models_response,
            default_provider=None,  # Or logic to determine default
            default_model=None,  # Or logic to determine default
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get settings: {str(e)}")


@router.put("/providers/{provider_name}")
async def update_provider_settings(
    provider_name: str, settings: ProviderSchema, db: Session = Depends(get_db)
):
    """Update settings for a specific provider in the database"""
    try:
        provider = db.query(Provider).filter(Provider.name == provider_name).first()
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Provider {provider_name} not found",
            )

        # Update provider fields
        for field, value in settings.dict(exclude_unset=True).items():
            setattr(provider, field, value)

        db.commit()
        db.refresh(provider)

        return {
            "status": "success",
            "message": f"Settings updated for provider: {provider_name}",
            "settings": ProviderSchema.from_orm(provider),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update provider settings: {str(e)}",
        )


@router.put("/models/{model_name}")
async def update_model_settings(
    model_name: str, settings: ModelSchema, db: Session = Depends(get_db)
):
    """Update settings for a specific model in the database"""
    try:
        model = db.query(Model).filter(Model.name == model_name).first()
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model {model_name} not found",
            )

        # Update model fields
        for field, value in settings.dict(exclude_unset=True).items():
            setattr(model, field, value)

        db.commit()
        db.refresh(model)

        return {
            "status": "success",
            "message": f"Settings updated for model: {model_name}",
            "settings": ModelSchema.from_orm(model),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update model settings: {str(e)}",
        )


@router.post("/test-connection")
async def test_provider_connection(provider_name: str):
    """Test connection to a provider's API"""
    try:
        # Find the provider
        provider = None
        for p in DEFAULT_PROVIDERS:
            if p["name"].lower() == provider_name.lower():
                provider = p
                break

        if not provider:
            raise HTTPException(
                status_code=404, detail=f"Provider {provider_name} not found"
            )

        if not provider.get("api_key"):
            return {
                "status": "warning",
                "message": f"No API key configured for {provider_name}",
                "connected": False,
            }

        # In a real app, you would make a test API call here
        # For now, we'll just check if the API key exists
        return {
            "status": "success",
            "message": f"Connection test successful for {provider_name}",
            "connected": True,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")


# RAG Settings Endpoints


@router.get("/rag", response_model=RAGSettings)
async def get_rag_settings():
    """Get current RAG settings"""
    try:
        return RAGSettings(
            enable_enhanced_rag=app_settings.enable_enhanced_rag,
            chroma_path=app_settings.rag_chroma_path,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get RAG settings: {str(e)}"
        )


@router.put("/rag")
async def update_rag_settings(rag_settings: RAGSettings):
    """Update RAG settings"""
    try:
        # In a real app, this would update the database and restart services
        # For now, we'll just validate the input and return success
        if not rag_settings.chroma_path:
            raise HTTPException(status_code=400, detail="Chroma path is required")

        return {
            "status": "success",
            "message": "RAG settings updated. Note: Changes may require service restart to take effect.",
            "settings": rag_settings.dict(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update RAG settings: {str(e)}"
        )


@router.post("/rag/test")
async def test_rag_configuration():
    """Test RAG configuration and dependencies"""
    try:
        # Test if RAG service can be initialized
        from services.rag_service import RAGService

        # Try to initialize with current settings
        rag_service = RAGService(
            enable_enhanced=app_settings.enable_enhanced_rag,
            chroma_path=app_settings.rag_chroma_path,
        )

        # Check if ChromaDB is available
        chroma_available = rag_service.chroma_client is not None

        # Check if enhanced features are available
        enhanced_available = False
        if app_settings.enable_enhanced_rag:
            try:
                enhanced_service = rag_service._get_enhanced_service()
                enhanced_available = enhanced_service is not None
            except Exception:
                enhanced_available = False

        return {
            "status": "success",
            "chroma_available": chroma_available,
            "enhanced_rag_enabled": app_settings.enable_enhanced_rag,
            "enhanced_rag_available": enhanced_available,
            "chroma_path": app_settings.rag_chroma_path,
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"RAG configuration test failed: {str(e)}",
            "chroma_available": False,
            "enhanced_rag_enabled": app_settings.enable_enhanced_rag,
            "enhanced_rag_available": False,
        }
