from typing import Optional, List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

try:
    from app.api.deps import get_db, get_current_user, require_admin_or_faculty
    from app.services.syllabus_service import SyllabusService
    from app.schemas.syllabus import (
        SyllabusDocumentResponse,
        SyllabusReviewUpdate
    )
    from app.db.models import User
except ImportError:
    from backend.app.api.deps import get_db, get_current_user, require_admin_or_faculty
    from backend.app.services.syllabus_service import SyllabusService
    from backend.app.schemas.syllabus import (
        SyllabusDocumentResponse,
        SyllabusReviewUpdate
    )
    from backend.app.db.models import User

router = APIRouter(tags=["Syllabus Management"])


@router.post("/subjects/{subject_id}/syllabus/upload", response_model=None)
async def upload_syllabus_document(
    subject_id: str,
    file: UploadFile = File(...),
    user: User = Depends(require_admin_or_faculty),
    db: Session = Depends(get_db)
):
    service = SyllabusService(db)
    doc = await service.upload_syllabus(subject_id, file, user)
    return {"success": True, "data": SyllabusDocumentResponse.model_validate(doc)}


@router.get("/subjects/{subject_id}/syllabus", response_model=None)
def get_current_syllabus(
    subject_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = SyllabusService(db)
    doc = service.get_current_syllabus(subject_id, current_user)
    if not doc:
        return {"success": True, "data": None}
    return {"success": True, "data": SyllabusDocumentResponse.model_validate(doc)}


@router.get("/subjects/{subject_id}/syllabus/history", response_model=None)
def list_syllabus_history(
    subject_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = SyllabusService(db)
    items = service.list_syllabus_history(subject_id, current_user)
    return {"success": True, "data": [SyllabusDocumentResponse.model_validate(d) for d in items]}


@router.get("/syllabus/{doc_id}", response_model=None)
def get_syllabus_document(
    doc_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = SyllabusService(db)
    doc = service.get_syllabus_by_id(doc_id, current_user)
    return {"success": True, "data": SyllabusDocumentResponse.model_validate(doc)}


@router.post("/syllabus/{doc_id}/process", response_model=None)
async def process_syllabus_document(
    doc_id: str,
    user: User = Depends(require_admin_or_faculty),
    db: Session = Depends(get_db)
):
    service = SyllabusService(db)
    doc = await service.process_syllabus(doc_id, user)
    return {"success": True, "data": SyllabusDocumentResponse.model_validate(doc)}


@router.patch("/syllabus/{doc_id}/review", response_model=None)
def update_syllabus_review(
    doc_id: str,
    review_data: SyllabusReviewUpdate,
    user: User = Depends(require_admin_or_faculty),
    db: Session = Depends(get_db)
):
    service = SyllabusService(db)
    doc = service.update_syllabus_review(doc_id, review_data, user)
    return {"success": True, "data": SyllabusDocumentResponse.model_validate(doc)}


@router.post("/syllabus/{doc_id}/approve", response_model=None)
def approve_syllabus_document(
    doc_id: str,
    user: User = Depends(require_admin_or_faculty),
    db: Session = Depends(get_db)
):
    service = SyllabusService(db)
    doc = service.approve_syllabus(doc_id, user)
    return {"success": True, "data": SyllabusDocumentResponse.model_validate(doc)}


@router.get("/syllabus/{doc_id}/download")
async def download_syllabus_file(
    doc_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = SyllabusService(db)
    doc = service.get_syllabus_by_id(doc_id, current_user)
    
    file_bytes = await service.storage_service.get_file(doc.file_asset.storage_path)
    return Response(
        content=file_bytes,
        media_type=doc.file_asset.mime_type,
        headers={"Content-Disposition": f'attachment; filename="{doc.file_asset.original_filename}"'}
    )
