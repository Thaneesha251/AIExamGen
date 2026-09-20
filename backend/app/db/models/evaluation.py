from typing import Optional, List
from sqlalchemy import String, Text, Float, Integer, Boolean, ForeignKey, Enum as SQLEnum, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base, TimestampMixin
from backend.app.db.guid import GUID, generate_uuid
from backend.app.db.models.enums import EvaluatorTypeEnum, EvaluationStatusEnum, FeedbackTypeEnum, ReviewActionEnum

class Evaluation(Base, TimestampMixin):
    __tablename__ = "evaluations"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=generate_uuid)
    examination_id: Mapped[str] = mapped_column(GUID, ForeignKey("examinations.id", ondelete="CASCADE"), nullable=False, index=True)
    answer_paper_id: Mapped[str] = mapped_column(GUID, ForeignKey("answer_papers.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id: Mapped[str] = mapped_column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    evaluator_type: Mapped[EvaluatorTypeEnum] = mapped_column(SQLEnum(EvaluatorTypeEnum), nullable=False, default=EvaluatorTypeEnum.AI)
    status: Mapped[EvaluationStatusEnum] = mapped_column(SQLEnum(EvaluationStatusEnum), nullable=False, default=EvaluationStatusEnum.PENDING, index=True)
    requires_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    total_ai_marks: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_final_marks: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    overall_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    started_at: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    completed_at: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    reviewed_at: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    reviewed_by: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    approved_by: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    finalized_by: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    finalized_at: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    finalization_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    examination: Mapped["Examination"] = relationship("Examination", back_populates="evaluations")
    answer_paper: Mapped["AnswerPaper"] = relationship("AnswerPaper", back_populates="evaluations")
    student: Mapped["User"] = relationship("User", foreign_keys=[student_id])

    items: Mapped[List["EvaluationItem"]] = relationship("EvaluationItem", back_populates="evaluation", cascade="all, delete-orphan")
    faculty_reviews: Mapped[List["FacultyReview"]] = relationship("FacultyReview", back_populates="evaluation", cascade="all, delete-orphan")


class EvaluationItem(Base, TimestampMixin):
    __tablename__ = "evaluation_items"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=generate_uuid)
    evaluation_id: Mapped[str] = mapped_column(GUID, ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False, index=True)
    question_paper_item_id: Mapped[str] = mapped_column(GUID, ForeignKey("question_paper_items.id", ondelete="CASCADE"), nullable=False, index=True)
    extracted_answer_id: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("extracted_answers.id", ondelete="SET NULL"), nullable=True, index=True)

    maximum_marks: Mapped[float] = mapped_column(Float, nullable=False)
    keyword_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    concept_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    semantic_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pattern_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rubric_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    ai_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True) # Normalized score 0.0 - 1.0
    ai_marks: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    final_marks: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    matched_keywords: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    missing_keywords: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    matched_concepts: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    missing_concepts: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    strengths: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    missing_points: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    criterion_scores: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    requires_faculty_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    review_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    prompt_version: Mapped[Optional[str]] = mapped_column(String(50), default="v1", nullable=True)
    evaluation_explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    review_status: Mapped[Optional[str]] = mapped_column(String(50), default="PENDING", nullable=True)
    override_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    faculty_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    evaluation: Mapped["Evaluation"] = relationship("Evaluation", back_populates="items")
    question_paper_item: Mapped["QuestionPaperItem"] = relationship("QuestionPaperItem", back_populates="evaluation_items")
    extracted_answer: Mapped[Optional["ExtractedAnswer"]] = relationship("ExtractedAnswer", back_populates="evaluation_items")

    feedback_entries: Mapped[List["EvaluationFeedback"]] = relationship("EvaluationFeedback", back_populates="evaluation_item", cascade="all, delete-orphan")
    faculty_reviews: Mapped[List["FacultyReview"]] = relationship("FacultyReview", back_populates="evaluation_item", cascade="all, delete-orphan")



class EvaluationFeedback(Base, TimestampMixin):
    __tablename__ = "evaluation_feedbacks"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=generate_uuid)
    evaluation_item_id: Mapped[str] = mapped_column(GUID, ForeignKey("evaluation_items.id", ondelete="CASCADE"), nullable=False, index=True)
    feedback_type: Mapped[FeedbackTypeEnum] = mapped_column(SQLEnum(FeedbackTypeEnum), nullable=False, default=FeedbackTypeEnum.IMPROVEMENT)
    feedback_text: Mapped[str] = mapped_column(Text, nullable=False)

    evaluation_item: Mapped["EvaluationItem"] = relationship("EvaluationItem", back_populates="feedback_entries")


class FacultyReview(Base, TimestampMixin):
    __tablename__ = "faculty_reviews"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=generate_uuid)
    evaluation_id: Mapped[str] = mapped_column(GUID, ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False, index=True)
    evaluation_item_id: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("evaluation_items.id", ondelete="SET NULL"), nullable=True, index=True)
    faculty_id: Mapped[str] = mapped_column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    original_ai_marks: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    revised_marks: Mapped[float] = mapped_column(Float, nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    action: Mapped[ReviewActionEnum] = mapped_column(SQLEnum(ReviewActionEnum), nullable=False, default=ReviewActionEnum.APPROVED)
    reviewed_at: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    evaluation: Mapped["Evaluation"] = relationship("Evaluation", back_populates="faculty_reviews")
    evaluation_item: Mapped[Optional["EvaluationItem"]] = relationship("EvaluationItem", back_populates="faculty_reviews")
    faculty: Mapped["User"] = relationship("User")
