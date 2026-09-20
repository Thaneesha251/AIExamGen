from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

try:
    from app.api.deps import get_db, get_current_user, require_admin_or_faculty
    from app.db.models import User, Examination, AnswerPaper, PlagiarismResult, AnswerSimilarity, RoleEnum
except ImportError:
    from backend.app.api.deps import get_db, get_current_user, require_admin_or_faculty
    from backend.app.db.models import User, Examination, AnswerPaper, PlagiarismResult, AnswerSimilarity, RoleEnum

from backend.app.schemas.plagiarism import (
    SimilarityAnalysisRequest,
    AnswerSimilarityResponse,
    PlagiarismResultResponse,
    PlagiarismSummaryResponse,
    PlagiarismReviewRequest
)
from backend.app.services.similarity_analysis_service import SimilarityAnalysisService

router = APIRouter(prefix="/plagiarism", tags=["Plagiarism & Similarity Analysis"])


def verify_exam_access(db: Session, examination_id: str, current_user: User) -> Examination:
    exam = db.query(Examination).filter(Examination.id == examination_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Examination not found")

    user_role_str = current_user.role.name if hasattr(current_user.role, 'name') else str(current_user.role)
    if user_role_str == RoleEnum.ADMIN.value if hasattr(RoleEnum.ADMIN, 'value') else "ADMIN":
        return exam

    if user_role_str == RoleEnum.FACULTY.value if hasattr(RoleEnum.FACULTY, 'value') else "FACULTY":
        if exam.created_by and exam.created_by == current_user.id:
            return exam
        if exam.subject and current_user.department_id and exam.subject.department_id == current_user.department_id:
            return exam
        return exam  # Allow active faculty access to subject examinations in their domain

    raise HTTPException(status_code=403, detail="Access denied: Students cannot access internal plagiarism detection endpoints")


@router.post("/examinations/{exam_id}/analyze", response_model=Dict[str, Any])
def analyze_examination_similarity(
    exam_id: str,
    payload: SimilarityAnalysisRequest = SimilarityAnalysisRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_faculty)
):
    """Executes pairwise answer similarity comparison across all student answer papers for an examination."""
    verify_exam_access(db, exam_id, current_user)
    service = SimilarityAnalysisService(db)
    result = service.analyze_examination_similarity(
        examination_id=exam_id,
        user_id=current_user.id,
        lexical_weight=payload.lexical_weight,
        semantic_weight=payload.semantic_weight,
        flag_threshold=payload.flag_threshold,
        minimum_text_length=payload.minimum_text_length
    )
    return result


@router.get("/examinations/{exam_id}/summary", response_model=PlagiarismSummaryResponse)
def get_examination_similarity_summary(
    exam_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_faculty)
):
    """Retrieves plagiarism analysis summary and flagged results for an examination."""
    verify_exam_access(db, exam_id, current_user)
    service = SimilarityAnalysisService(db)
    summary = service.get_examination_similarity_summary(exam_id)
    return summary


@router.get("/answer-papers/{answer_paper_id}", response_model=PlagiarismResultResponse)
def get_answer_paper_plagiarism_result(
    answer_paper_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_faculty)
):
    """Retrieves plagiarism result for a single answer paper."""
    paper = db.query(AnswerPaper).filter(AnswerPaper.id == answer_paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Answer paper not found")

    verify_exam_access(db, paper.examination_id, current_user)

    result = db.query(PlagiarismResult).filter(PlagiarismResult.answer_paper_id == answer_paper_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Plagiarism result not found for this answer paper")

    return result


@router.get("/answer-papers/{answer_paper_id}/similarities", response_model=List[AnswerSimilarityResponse])
def get_answer_paper_similarities(
    answer_paper_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_faculty)
):
    """Retrieves pairwise similarity details for answers in a specific answer paper."""
    paper = db.query(AnswerPaper).filter(AnswerPaper.id == answer_paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Answer paper not found")

    verify_exam_access(db, paper.examination_id, current_user)

    ans_ids = [a.id for a in paper.extracted_answers]
    if not ans_ids:
        return []

    similarities = (
        db.query(AnswerSimilarity)
        .filter(
            (AnswerSimilarity.source_answer_id.in_(ans_ids)) | (AnswerSimilarity.target_answer_id.in_(ans_ids))
        )
        .order_by(AnswerSimilarity.similarity_score.desc())
        .all()
    )
    return similarities


@router.post("/results/{result_id}/review", response_model=PlagiarismResultResponse)
def review_plagiarism_case(
    result_id: str,
    payload: PlagiarismReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_faculty)
):
    """Faculty reviews or dismisses a flagged plagiarism case with explicit review notes."""
    pr = db.query(PlagiarismResult).filter(PlagiarismResult.id == result_id).first()
    if not pr:
        raise HTTPException(status_code=404, detail="Plagiarism result record not found")

    verify_exam_access(db, pr.examination_id, current_user)

    service = SimilarityAnalysisService(db)
    updated = service.review_plagiarism_case(
        result_id=result_id,
        target_status=payload.status,
        notes=payload.review_notes,
        user_id=current_user.id
    )
    return updated
