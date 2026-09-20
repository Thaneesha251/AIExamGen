from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

try:
    from app.api.deps import get_db, get_current_user, require_admin_or_faculty
    from app.services.question_paper_generation_service import QuestionPaperGenerationService
    from app.db.models import User
    from app.schemas.question_paper import (
        PaperGenerationRequest,
        QuestionReplacementRequest,
        SectionRegenerateRequest,
        PaperRegenerateRequest,
        QuestionPaperResponse,
        PaperValidationResult
    )
except ImportError:
    from backend.app.api.deps import get_db, get_current_user, require_admin_or_faculty
    from backend.app.services.question_paper_generation_service import QuestionPaperGenerationService
    from backend.app.db.models import User
    from backend.app.schemas.question_paper import (
        PaperGenerationRequest,
        QuestionReplacementRequest,
        SectionRegenerateRequest,
        PaperRegenerateRequest,
        QuestionPaperResponse,
        PaperValidationResult
    )

router = APIRouter(tags=["Question Papers & Generation"])

@router.post("/question-papers/generate", response_model=None)
def generate_question_paper(
    req: PaperGenerationRequest,
    user: User = Depends(require_admin_or_faculty),
    db: Session = Depends(get_db)
):
    service = QuestionPaperGenerationService(db)
    paper = service.generate_paper(req, user)
    val_res = service.validate_paper_by_id(paper.id)
    return {
        "success": True,
        "data": QuestionPaperResponse.model_validate(paper),
        "validation": val_res.model_dump()
    }

@router.get("/question-papers", response_model=None)
def list_question_papers(
    subject_id: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = QuestionPaperGenerationService(db)
    papers = service.list_papers(subject_id=subject_id, current_user=user)
    return {
        "success": True,
        "data": [QuestionPaperResponse.model_validate(p) for p in papers]
    }

@router.get("/question-papers/{paper_id}", response_model=None)
def get_question_paper(
    paper_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = QuestionPaperGenerationService(db)
    paper = service.get_paper(paper_id)
    val_res = service.validate_paper_by_id(paper_id)
    return {
        "success": True,
        "data": QuestionPaperResponse.model_validate(paper),
        "validation": val_res.model_dump()
    }

@router.post("/question-papers/{paper_id}/replace-question", response_model=None)
def replace_question(
    paper_id: str,
    req: QuestionReplacementRequest,
    user: User = Depends(require_admin_or_faculty),
    db: Session = Depends(get_db)
):
    service = QuestionPaperGenerationService(db)
    paper = service.replace_question_in_paper(paper_id, req, user)
    val_res = service.validate_paper_by_id(paper.id)
    return {
        "success": True,
        "data": QuestionPaperResponse.model_validate(paper),
        "validation": val_res.model_dump()
    }

@router.post("/question-papers/{paper_id}/regenerate-section", response_model=None)
def regenerate_section(
    paper_id: str,
    req: SectionRegenerateRequest,
    user: User = Depends(require_admin_or_faculty),
    db: Session = Depends(get_db)
):
    service = QuestionPaperGenerationService(db)
    paper = service.regenerate_section(paper_id, req, user)
    val_res = service.validate_paper_by_id(paper.id)
    return {
        "success": True,
        "data": QuestionPaperResponse.model_validate(paper),
        "validation": val_res.model_dump()
    }

@router.post("/question-papers/{paper_id}/regenerate", response_model=None)
def regenerate_full_paper(
    paper_id: str,
    req: PaperRegenerateRequest,
    user: User = Depends(require_admin_or_faculty),
    db: Session = Depends(get_db)
):
    service = QuestionPaperGenerationService(db)
    paper = service.regenerate_full_paper(paper_id, req, user)
    val_res = service.validate_paper_by_id(paper.id)
    return {
        "success": True,
        "data": QuestionPaperResponse.model_validate(paper),
        "validation": val_res.model_dump()
    }

@router.post("/question-papers/{paper_id}/validate", response_model=None)
def validate_question_paper(
    paper_id: str,
    version_number: Optional[int] = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = QuestionPaperGenerationService(db)
    val_res = service.validate_paper_by_id(paper_id, version_number=version_number)
    return {
        "success": True,
        "data": val_res.model_dump()
    }
