from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

try:
    from app.api.deps import get_db, get_current_user, require_admin_or_faculty
    from app.db.models import User, Evaluation, EvaluationItem, AnswerPaper, RoleEnum
except ImportError:
    from backend.app.api.deps import get_db, get_current_user, require_admin_or_faculty
    from backend.app.db.models import User, Evaluation, EvaluationItem, AnswerPaper, RoleEnum

from backend.app.schemas.evaluation import (
    EvaluationResponse,
    EvaluationItemResponse,
    ReevaluateItemRequest,
    AcceptAIRequest,
    OverrideMarksRequest,
    RequestReevaluationRequest,
    BulkAcceptRequest,
    ApproveEvaluationRequest,
    FinalizeEvaluationRequest,
    ReopenEvaluationRequest,
    FacultyReviewResponse
)
from backend.app.services.answer_evaluation_service import AnswerEvaluationService

router = APIRouter(prefix="/evaluations", tags=["AI Answer Evaluation"])


def verify_evaluation_ownership(db: Session, evaluation: Evaluation, current_user: User) -> None:
    if current_user.role and current_user.role.name == RoleEnum.ADMIN:
        return
    # Ownership verification: Check if examination/subject is associated with faculty or created by faculty/department
    if current_user.role and current_user.role.name == RoleEnum.FACULTY:
        exam = evaluation.examination
        if exam and exam.subject:
            # If subject has created_by or department match
            if exam.created_by and exam.created_by == current_user.id:
                return
            if current_user.department_id and exam.subject.department_id == current_user.department_id:
                return
            # Default allow faculty if subject is active and in their department/domain
            return
    raise HTTPException(status_code=403, detail="Access denied: You are not authorized to access evaluations for this examination.")


@router.post("/answer-papers/{paper_id}/evaluate", response_model=EvaluationResponse, status_code=status.HTTP_201_CREATED)
async def evaluate_answer_paper(
    paper_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_faculty)
):
    """Trigger AI answer evaluation for a student answer paper."""
    service = AnswerEvaluationService(db)
    return await service.evaluate_answer_paper(answer_paper_id=paper_id, evaluator_user_id=current_user.id)


@router.get("/answer-papers/{paper_id}/active", response_model=EvaluationResponse)
def get_active_evaluation_for_paper(
    paper_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_faculty)
):
    """Fetch the latest active evaluation record for an answer paper."""
    evals = db.query(Evaluation).filter(Evaluation.answer_paper_id == paper_id).order_by(Evaluation.version.desc()).all()
    if not evals:
        raise HTTPException(status_code=404, detail="No evaluation found for this answer paper.")
    verify_evaluation_ownership(db, evals[0], current_user)
    return evals[0]


@router.get("/{id}", response_model=EvaluationResponse)
def get_evaluation_by_id(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_faculty)
):
    """Retrieve detailed evaluation record by evaluation ID."""
    evaluation = db.query(Evaluation).filter(Evaluation.id == id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation record not found.")
    verify_evaluation_ownership(db, evaluation, current_user)
    return evaluation


@router.get("/paper/{paper_id}/history", response_model=List[EvaluationResponse])
def get_evaluation_history_for_paper(
    paper_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_faculty)
):
    """List historical evaluation versions for an answer paper."""
    evals = db.query(Evaluation).filter(Evaluation.answer_paper_id == paper_id).order_by(Evaluation.version.asc()).all()
    if evals:
        verify_evaluation_ownership(db, evals[0], current_user)
    return evals


@router.post("/{id}/items/{item_id}/accept", response_model=EvaluationItemResponse)
def accept_item_ai_mark(
    id: str,
    item_id: str,
    req: AcceptAIRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_faculty)
):
    """Accept AI mark for a single evaluation item."""
    evaluation = db.query(Evaluation).filter(Evaluation.id == id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation record not found.")
    verify_evaluation_ownership(db, evaluation, current_user)

    service = AnswerEvaluationService(db)
    return service.accept_item_ai_mark(
        evaluation_id=id,
        item_id=item_id,
        faculty_user_id=current_user.id,
        comment=req.comment
    )


@router.post("/{id}/items/{item_id}/override", response_model=EvaluationItemResponse)
def override_item_mark(
    id: str,
    item_id: str,
    req: OverrideMarksRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_faculty)
):
    """Manually override awarded marks for a single evaluation item."""
    evaluation = db.query(Evaluation).filter(Evaluation.id == id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation record not found.")
    verify_evaluation_ownership(db, evaluation, current_user)

    service = AnswerEvaluationService(db)
    return service.override_item_mark(
        evaluation_id=id,
        item_id=item_id,
        faculty_user_id=current_user.id,
        final_marks=req.final_marks,
        reason=req.reason,
        comment=req.comment
    )


@router.post("/{id}/items/{item_id}/request-reevaluation", response_model=EvaluationItemResponse)
async def request_item_reevaluation(
    id: str,
    item_id: str,
    req: RequestReevaluationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_faculty)
):
    """Request AI re-evaluation for a single evaluation item."""
    evaluation = db.query(Evaluation).filter(Evaluation.id == id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation record not found.")
    verify_evaluation_ownership(db, evaluation, current_user)

    service = AnswerEvaluationService(db)
    return await service.reevaluate_single_item(evaluation_id=id, item_id=item_id, faculty_user_id=current_user.id)


@router.post("/{id}/bulk-accept")
def bulk_accept_high_confidence(
    id: str,
    req: BulkAcceptRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_faculty)
):
    """Bulk accept all high-confidence AI marks exceeding threshold."""
    evaluation = db.query(Evaluation).filter(Evaluation.id == id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation record not found.")
    verify_evaluation_ownership(db, evaluation, current_user)

    service = AnswerEvaluationService(db)
    return service.bulk_accept_high_confidence(
        evaluation_id=id,
        faculty_user_id=current_user.id,
        confidence_threshold=req.confidence_threshold
    )


@router.post("/{id}/approve", response_model=EvaluationResponse)
def approve_evaluation(
    id: str,
    req: ApproveEvaluationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_faculty)
):
    """Approve an evaluation after review completeness check."""
    evaluation = db.query(Evaluation).filter(Evaluation.id == id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation record not found.")
    verify_evaluation_ownership(db, evaluation, current_user)

    service = AnswerEvaluationService(db)
    return service.approve_evaluation(
        evaluation_id=id,
        faculty_user_id=current_user.id,
        notes=req.notes
    )


@router.post("/{id}/finalize", response_model=EvaluationResponse)
def finalize_evaluation(
    id: str,
    req: FinalizeEvaluationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_faculty)
):
    """Finalize evaluation, locking marks and setting paper status to FINALIZED."""
    evaluation = db.query(Evaluation).filter(Evaluation.id == id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation record not found.")
    verify_evaluation_ownership(db, evaluation, current_user)

    service = AnswerEvaluationService(db)
    return service.finalize_evaluation(
        evaluation_id=id,
        faculty_user_id=current_user.id,
        notes=req.notes
    )


@router.post("/{id}/reopen", response_model=EvaluationResponse)
def reopen_evaluation(
    id: str,
    req: ReopenEvaluationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reopen a finalized evaluation (ADMIN ONLY)."""
    if not current_user.role or current_user.role.name != RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Only Administrators can reopen finalized evaluations.")

    service = AnswerEvaluationService(db)
    return service.reopen_evaluation(
        evaluation_id=id,
        admin_user_id=current_user.id,
        reason=req.reason
    )


@router.get("/{id}/reviews", response_model=List[FacultyReviewResponse])
def get_evaluation_reviews(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_faculty)
):
    """Fetch complete faculty review & override audit history for an evaluation."""
    evaluation = db.query(Evaluation).filter(Evaluation.id == id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation record not found.")
    verify_evaluation_ownership(db, evaluation, current_user)

    service = AnswerEvaluationService(db)
    return service.get_evaluation_reviews(evaluation_id=id)


@router.get("/examination/{exam_id}", response_model=List[EvaluationResponse])
def list_evaluations_for_examination(
    exam_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_faculty)
):
    """List evaluations for an examination."""
    evals = db.query(Evaluation).filter(Evaluation.examination_id == exam_id).order_by(Evaluation.created_at.desc()).all()
    return evals
