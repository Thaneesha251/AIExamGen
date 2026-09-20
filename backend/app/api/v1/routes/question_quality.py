from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

try:
    from app.api.deps import get_db, get_current_user, require_admin_or_faculty
    from app.db.models import User, Examination, RoleEnum
except ImportError:
    from backend.app.api.deps import get_db, get_current_user, require_admin_or_faculty
    from backend.app.db.models import User, Examination, RoleEnum

from backend.app.schemas.question_quality import (
    ExamQualityDashboardResponse,
    QuestionPerformanceResponse,
    DifficultyAnalysisResponse,
    DiscriminationAnalysisResponse,
    BlueprintBalanceResponse,
    QuestionBankInsightsResponse,
    WeakCoverageResponse,
    QuestionQualityReviewRequest,
    QuestionQualityReviewResponse,
    QuestionQualityItemResponse
)
from backend.app.services.question_quality_service import QuestionQualityService

router = APIRouter(prefix="/analytics", tags=["Question Quality & Exam Quality Intelligence"])


def verify_exam_access(db: Session, examination_id: str, current_user: User) -> Examination:
    exam = db.query(Examination).filter(Examination.id == examination_id).first()
    if not exam:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Examination not found")

    user_role = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
    if user_role == RoleEnum.STUDENT.value or user_role == "STUDENT":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Students are not authorized to view quality analytics")

    return exam


@router.get(
    "/exams/{examination_id}/quality",
    response_model=ExamQualityDashboardResponse,
    dependencies=[Depends(require_admin_or_faculty)]
)
def get_exam_quality_dashboard(
    examination_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves full Exam Quality Dashboard analysis for an examination."""
    verify_exam_access(db, examination_id, current_user)
    service = QuestionQualityService(db)
    return service.get_exam_quality_dashboard(examination_id)


@router.get(
    "/exams/{examination_id}/questions",
    response_model=List[QuestionQualityItemResponse],
    dependencies=[Depends(require_admin_or_faculty)]
)
def get_exam_questions_quality_list(
    examination_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves question quality analysis rows for all questions in an examination."""
    verify_exam_access(db, examination_id, current_user)
    service = QuestionQualityService(db)
    dashboard = service.get_exam_quality_dashboard(examination_id)
    return dashboard["questions"]


@router.get(
    "/exams/{examination_id}/questions/{question_id}",
    response_model=Dict[str, Any],
    dependencies=[Depends(require_admin_or_faculty)]
)
def get_single_question_quality_detail(
    examination_id: str,
    question_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves comprehensive quality detail (performance, difficulty, discrimination, similarity) for a single question."""
    verify_exam_access(db, examination_id, current_user)
    service = QuestionQualityService(db)

    perf = service.get_question_performance_analysis(examination_id, question_id)
    diff = service.get_difficulty_analysis(examination_id, question_id)
    disc = service.get_discrimination_analysis(examination_id, question_id)
    sim = service.get_question_similarity_integration(examination_id, question_id)
    qual = service.get_question_quality_classification(examination_id, question_id)

    return {
        "performance": perf,
        "difficulty": diff,
        "discrimination": disc,
        "similarity": sim,
        "classification": qual
    }


@router.get(
    "/exams/{examination_id}/difficulty",
    response_model=Dict[str, Any],
    dependencies=[Depends(require_admin_or_faculty)]
)
def get_exam_difficulty_breakdown(
    examination_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves difficulty distribution analysis for an examination."""
    verify_exam_access(db, examination_id, current_user)
    service = QuestionQualityService(db)
    dashboard = service.get_exam_quality_dashboard(examination_id)
    return {
        "examination_id": examination_id,
        "difficulty_distribution": dashboard["difficulty_distribution"]
    }


@router.get(
    "/exams/{examination_id}/discrimination",
    response_model=Dict[str, Any],
    dependencies=[Depends(require_admin_or_faculty)]
)
def get_exam_discrimination_breakdown(
    examination_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves discrimination index distribution analysis for an examination."""
    verify_exam_access(db, examination_id, current_user)
    service = QuestionQualityService(db)
    dashboard = service.get_exam_quality_dashboard(examination_id)
    return {
        "examination_id": examination_id,
        "discrimination_distribution": dashboard["discrimination_distribution"]
    }


@router.get(
    "/exams/{examination_id}/blueprint",
    response_model=BlueprintBalanceResponse,
    dependencies=[Depends(require_admin_or_faculty)]
)
def get_exam_blueprint_balance_analysis(
    examination_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves blueprint balance and mark variance analysis for an examination."""
    verify_exam_access(db, examination_id, current_user)
    service = QuestionQualityService(db)
    return service.get_exam_blueprint_balance(examination_id)


@router.get(
    "/question-bank/insights",
    response_model=QuestionBankInsightsResponse,
    dependencies=[Depends(require_admin_or_faculty)]
)
def get_question_bank_insights(
    subject_id: str = Query(..., description="Subject ID to analyze question bank usage and performance"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves multi-exam empirical question bank performance and usage insights."""
    service = QuestionQualityService(db)
    return service.get_question_bank_insights(subject_id)


@router.get(
    "/question-bank/weak-coverage",
    response_model=WeakCoverageResponse,
    dependencies=[Depends(require_admin_or_faculty)]
)
def get_weak_assessment_coverage(
    subject_id: str = Query(..., description="Subject ID to analyze assessment coverage"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Identifies syllabus units with low historical assessment coverage."""
    service = QuestionQualityService(db)
    return service.get_weak_assessment_coverage(subject_id)


@router.post(
    "/questions/{question_id}/review",
    response_model=QuestionQualityReviewResponse,
    dependencies=[Depends(require_admin_or_faculty)]
)
def record_question_quality_review(
    question_id: str,
    payload: QuestionQualityReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Records faculty quality review status and optional notes for a question."""
    service = QuestionQualityService(db)
    review = service.record_question_quality_review(
        question_id=question_id,
        examination_id=payload.examination_id,
        reviewer_id=current_user.id,
        status_val=payload.status,
        note=payload.note
    )
    return review
