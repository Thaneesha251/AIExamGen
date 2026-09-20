from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

try:
    from app.api.deps import get_db, get_current_user, require_admin_or_faculty
    from app.services.answer_key_service import AnswerKeyService
    from app.db.models import User
    from app.schemas.answer_key import (
        AnswerKeyCreate,
        AnswerKeyUpdate,
        AnswerKeyResponse,
        AnswerKeyValidationResult,
        AIDraftAnswerKeyRequest
    )
except ImportError:
    from backend.app.api.deps import get_db, get_current_user, require_admin_or_faculty
    from backend.app.services.answer_key_service import AnswerKeyService
    from backend.app.db.models import User
    from backend.app.schemas.answer_key import (
        AnswerKeyCreate,
        AnswerKeyUpdate,
        AnswerKeyResponse,
        AnswerKeyValidationResult,
        AIDraftAnswerKeyRequest
    )

router = APIRouter(tags=["Answer Keys"])

@router.post("/question-papers/versions/{version_id}/answer-key/generate", response_model=None)
def generate_initial_answer_key(
    version_id: str,
    user: User = Depends(require_admin_or_faculty),
    db: Session = Depends(get_db)
):
    service = AnswerKeyService(db)
    ak = service.generate_initial_answer_key(version_id, user)
    val_res = service.validate_answer_key_by_id(ak.id)
    return {
        "success": True,
        "data": AnswerKeyResponse.model_validate(ak),
        "validation": val_res.model_dump()
    }

@router.get("/question-papers/versions/{version_id}/answer-key", response_model=None)
def get_answer_key_for_version(
    version_id: str,
    user: User = Depends(require_admin_or_faculty),
    db: Session = Depends(get_db)
):
    service = AnswerKeyService(db)
    ak = service.get_latest_answer_key(version_id)
    val_res = service.validate_answer_key_by_id(ak.id)
    return {
        "success": True,
        "data": AnswerKeyResponse.model_validate(ak),
        "validation": val_res.model_dump()
    }

@router.get("/answer-keys/{key_id}", response_model=None)
def get_answer_key_by_id(
    key_id: str,
    user: User = Depends(require_admin_or_faculty),
    db: Session = Depends(get_db)
):
    service = AnswerKeyService(db)
    ak = service.get_answer_key_by_id(key_id)
    val_res = service.validate_answer_key_by_id(key_id)
    return {
        "success": True,
        "data": AnswerKeyResponse.model_validate(ak),
        "validation": val_res.model_dump()
    }

@router.put("/answer-keys/{key_id}", response_model=None)
def update_answer_key(
    key_id: str,
    req: AnswerKeyUpdate,
    user: User = Depends(require_admin_or_faculty),
    db: Session = Depends(get_db)
):
    service = AnswerKeyService(db)
    ak = service.update_answer_key(key_id, req, user)
    val_res = service.validate_answer_key_by_id(ak.id)
    return {
        "success": True,
        "data": AnswerKeyResponse.model_validate(ak),
        "validation": val_res.model_dump()
    }

@router.post("/answer-keys/{key_id}/validate", response_model=None)
def validate_answer_key(
    key_id: str,
    user: User = Depends(require_admin_or_faculty),
    db: Session = Depends(get_db)
):
    service = AnswerKeyService(db)
    val_res = service.validate_answer_key_by_id(key_id)
    return {
        "success": True,
        "data": val_res.model_dump()
    }
