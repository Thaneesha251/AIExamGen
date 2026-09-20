from typing import Optional
from sqlalchemy import String, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base, TimestampMixin
from backend.app.db.guid import GUID, generate_uuid

class QuestionQualityReview(Base, TimestampMixin):
    __tablename__ = "question_quality_reviews"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=generate_uuid)
    question_id: Mapped[str] = mapped_column(GUID, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    examination_id: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("examinations.id", ondelete="CASCADE"), nullable=True, index=True)
    reviewer_id: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    status: Mapped[str] = mapped_column(String(50), nullable=False, default="REVIEWED")  # REVIEWED, KEEP, REVIEW_BEFORE_REUSE
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    question: Mapped["Question"] = relationship("Question")
    examination: Mapped[Optional["Examination"]] = relationship("Examination")
    reviewer: Mapped[Optional["User"]] = relationship("User")

    __table_args__ = (
        Index("idx_question_quality_reviews_q_exam", "question_id", "examination_id"),
    )
