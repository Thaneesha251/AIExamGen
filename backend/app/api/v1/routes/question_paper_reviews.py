from typing import Optional
from fastapi import APIRouter, Depends, Query, Response, HTTPException, status
from sqlalchemy.orm import Session

try:
    from app.api.deps import get_db, get_current_user, require_admin_or_faculty
    from app.services.question_paper_review_service import QuestionPaperReviewService
    from app.services.question_paper_export_service import QuestionPaperExportService
    from app.db.models import User
    from app.schemas.question_paper import QuestionPaperResponse
    from app.schemas.question_paper_review import (
        PaperReviewChecklistResponse,
        PaperApprovalRequest,
        PaperPublishRequest
    )
except ImportError:
    from backend.app.api.deps import get_db, get_current_user, require_admin_or_faculty
    from backend.app.services.question_paper_review_service import QuestionPaperReviewService
    from backend.app.services.question_paper_export_service import QuestionPaperExportService
    from backend.app.db.models import User
    from backend.app.schemas.question_paper import QuestionPaperResponse
    from backend.app.schemas.question_paper_review import (
        PaperReviewChecklistResponse,
        PaperApprovalRequest,
        PaperPublishRequest
    )

router = APIRouter(tags=["Question Paper Review & Export"])

@router.get("/question-papers/{paper_id}/review", response_model=None)
def get_paper_review_checklist(
    paper_id: str,
    user: User = Depends(require_admin_or_faculty),
    db: Session = Depends(get_db)
):
    service = QuestionPaperReviewService(db)
    checklist = service.get_review_checklist(paper_id)
    return {
        "success": True,
        "data": checklist.model_dump()
    }

@router.post("/question-papers/{paper_id}/approve", response_model=None)
def approve_question_paper(
    paper_id: str,
    req: PaperApprovalRequest,
    user: User = Depends(require_admin_or_faculty),
    db: Session = Depends(get_db)
):
    service = QuestionPaperReviewService(db)
    paper = service.approve_paper(paper_id, req, user)
    return {
        "success": True,
        "data": QuestionPaperResponse.model_validate(paper),
        "message": "Question paper and answer key approved successfully."
    }

@router.post("/question-papers/{paper_id}/publish", response_model=None)
def publish_question_paper(
    paper_id: str,
    req: PaperPublishRequest,
    user: User = Depends(require_admin_or_faculty),
    db: Session = Depends(get_db)
):
    service = QuestionPaperReviewService(db)
    paper = service.publish_paper(paper_id, req, user)
    return {
        "success": True,
        "data": QuestionPaperResponse.model_validate(paper),
        "message": "Question paper published successfully."
    }

@router.get("/question-papers/{paper_id}/export/pdf")
def export_question_paper_pdf(
    paper_id: str,
    version_number: Optional[int] = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = QuestionPaperExportService(db)
    pdf_bytes = service.generate_question_paper_pdf(paper_id, version_number=version_number)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=question_paper_{paper_id[:8]}.pdf"
        }
    )

@router.get("/question-papers/{paper_id}/answer-key/export/pdf")
def export_answer_key_pdf(
    paper_id: str,
    version_number: Optional[int] = Query(None),
    user: User = Depends(require_admin_or_faculty), # Strictly Faculty/Admin!
    db: Session = Depends(get_db)
):
    service = QuestionPaperExportService(db)
    pdf_bytes = service.generate_answer_key_pdf(paper_id, version_number=version_number)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=answer_key_{paper_id[:8]}.pdf"
        }
    )
