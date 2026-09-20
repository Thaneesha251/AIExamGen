from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

try:
    from app.api.deps import get_db, get_current_user, require_admin_or_faculty
    from app.db.models import User, Examination, RoleEnum
except ImportError:
    from backend.app.api.deps import get_db, get_current_user, require_admin_or_faculty
    from backend.app.db.models import User, Examination, RoleEnum

from backend.app.schemas.analytics import (
    ExamAnalyticsOverviewResponse,
    StudentPerformanceResponse,
    QuestionAnalyticsResponse,
    UnitAnalyticsResponse,
    TopicAnalyticsResponse,
    COAnalyticsResponse,
    BloomAnalyticsResponse,
    DifficultyAnalyticsResponse,
    WeakTopicResponse
)
from backend.app.services.performance_analytics_service import PerformanceAnalyticsService
from backend.app.services.weak_topic_service import WeakTopicService

router = APIRouter(prefix="/analytics", tags=["Student Performance Analytics & Weak Topics"])


def verify_analytics_access(db: Session, examination_id: str, current_user: User) -> Examination:
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
        return exam

    raise HTTPException(status_code=403, detail="Access denied: Students cannot access internal faculty analytics endpoints")


@router.get("/examinations/{exam_id}", response_model=ExamAnalyticsOverviewResponse)
def get_examination_analytics_overview(
    exam_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_faculty)
):
    """Retrieves overview performance metrics for an examination based strictly on FINALIZED evaluations."""
    verify_analytics_access(db, exam_id, current_user)
    service = PerformanceAnalyticsService(db)
    return service.get_examination_overview(exam_id)


@router.get("/examinations/{exam_id}/students", response_model=List[StudentPerformanceResponse])
def get_examination_student_performance(
    exam_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_faculty)
):
    """Retrieves student-level performance list for an examination."""
    verify_analytics_access(db, exam_id, current_user)
    service = PerformanceAnalyticsService(db)
    return service.get_students_performance(exam_id)


@router.get("/examinations/{exam_id}/questions", response_model=List[QuestionAnalyticsResponse])
def get_examination_question_analytics(
    exam_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_faculty)
):
    """Retrieves question-wise performance metrics for an examination."""
    verify_analytics_access(db, exam_id, current_user)
    service = PerformanceAnalyticsService(db)
    return service.get_question_analytics(exam_id)


@router.get("/examinations/{exam_id}/units", response_model=List[UnitAnalyticsResponse])
def get_examination_unit_analytics(
    exam_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_faculty)
):
    """Retrieves unit-wise performance breakdown for an examination."""
    verify_analytics_access(db, exam_id, current_user)
    service = PerformanceAnalyticsService(db)
    return service.get_dimension_analytics(exam_id, "unit")


@router.get("/examinations/{exam_id}/topics", response_model=List[TopicAnalyticsResponse])
def get_examination_topic_analytics(
    exam_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_faculty)
):
    """Retrieves topic-wise performance breakdown for an examination."""
    verify_analytics_access(db, exam_id, current_user)
    service = PerformanceAnalyticsService(db)
    return service.get_dimension_analytics(exam_id, "topic")


@router.get("/examinations/{exam_id}/learning-outcomes", response_model=List[COAnalyticsResponse])
def get_examination_co_analytics(
    exam_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_faculty)
):
    """Retrieves learning outcome (CO) attainment analytics for an examination."""
    verify_analytics_access(db, exam_id, current_user)
    service = PerformanceAnalyticsService(db)
    return service.get_dimension_analytics(exam_id, "learning_outcome")


@router.get("/examinations/{exam_id}/bloom", response_model=List[BloomAnalyticsResponse])
def get_examination_bloom_analytics(
    exam_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_faculty)
):
    """Retrieves Bloom's taxonomy performance breakdown for an examination."""
    verify_analytics_access(db, exam_id, current_user)
    service = PerformanceAnalyticsService(db)
    return service.get_dimension_analytics(exam_id, "bloom")


@router.get("/examinations/{exam_id}/difficulty", response_model=List[DifficultyAnalyticsResponse])
def get_examination_difficulty_analytics(
    exam_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_faculty)
):
    """Retrieves question difficulty level performance breakdown for an examination."""
    verify_analytics_access(db, exam_id, current_user)
    service = PerformanceAnalyticsService(db)
    return service.get_dimension_analytics(exam_id, "difficulty")


@router.get("/examinations/{exam_id}/weak-topics", response_model=WeakTopicResponse)
def get_examination_weak_topics(
    exam_id: str,
    threshold: float = Query(50.0, ge=0.0, le=100.0, description="Percentage threshold below which topic is flagged weak"),
    min_responses: int = Query(3, ge=1, description="Minimum student responses required to analyze topic"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_faculty)
):
    """Identifies weak topics for an examination cohort with evidence and supporting questions."""
    verify_analytics_access(db, exam_id, current_user)
    service = WeakTopicService(db)
    return service.detect_weak_topics_for_examination(
        examination_id=exam_id,
        threshold_percentage=threshold,
        minimum_responses=min_responses
    )


@router.get("/students/{student_id}", response_model=Dict[str, Any])
def get_student_performance_summary(
    student_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_faculty)
):
    """Retrieves performance metrics across all finalized examinations for a single student."""
    service = PerformanceAnalyticsService(db)
    return service.get_single_student_performance(student_id)


@router.get("/students/{student_id}/weak-topics", response_model=WeakTopicResponse)
def get_student_weak_topics(
    student_id: str,
    threshold: float = Query(50.0, ge=0.0, le=100.0),
    min_responses: int = Query(1, ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_faculty)
):
    """Identifies weak topics for a specific student across finalized examinations."""
    service = WeakTopicService(db)
    return service.detect_weak_topics_for_student(
        student_id=student_id,
        threshold_percentage=threshold,
        minimum_responses=min_responses
    )
