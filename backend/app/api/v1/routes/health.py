from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any
try:
    from app.core.config import settings
    from app.db.session import get_db
except ImportError:
    from backend.app.core.config import settings
    from backend.app.db.session import get_db

router = APIRouter()

@router.get("/health", response_model=Dict[str, Any])
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint verifying backend & database connectivity."""
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "success": True,
        "status": "healthy" if db_status == "healthy" else "degraded",
        "service": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "database": db_status,
        "ai_provider": settings.AI_PROVIDER,
        "ocr_provider": settings.OCR_PROVIDER
    }

@router.get("/version", response_model=Dict[str, Any])
def version_info():
    """Returns application version information."""
    return {
        "success": True,
        "version": "1.0.0",
        "app_name": settings.APP_NAME,
        "api_version": "v1"
    }
