from typing import Optional
from sqlalchemy import String, Text, Float, ForeignKey, Index, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base, TimestampMixin
from backend.app.db.guid import GUID, generate_uuid

class PlagiarismResult(Base, TimestampMixin):
    __tablename__ = "plagiarism_results"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=generate_uuid)
    examination_id: Mapped[str] = mapped_column(GUID, ForeignKey("examinations.id", ondelete="CASCADE"), nullable=False, index=True)
    answer_paper_id: Mapped[str] = mapped_column(GUID, ForeignKey("answer_papers.id", ondelete="CASCADE"), nullable=False, index=True)

    answer_a_id: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("extracted_answers.id", ondelete="CASCADE"), nullable=True)
    answer_b_id: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("extracted_answers.id", ondelete="CASCADE"), nullable=True)

    similarity_score: Mapped[float] = mapped_column(Float, nullable=False) # e.g. 0.85 (85%)
    lexical_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    semantic_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    combined_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    threshold_used: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    analysis_version: Mapped[Optional[str]] = mapped_column(String(50), default="v1.0", nullable=True)

    matching_segments: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True) # Matching phrases array
    detection_method: Mapped[str] = mapped_column(String(50), default="COMBINED_LEXICAL_SEMANTIC", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="FLAGGED", nullable=False) # FLAGGED, REVIEWED, DISMISSED

    reviewed_by: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    examination: Mapped["Examination"] = relationship("Examination")
    answer_paper: Mapped["AnswerPaper"] = relationship("AnswerPaper")
    answer_a: Mapped[Optional["ExtractedAnswer"]] = relationship("ExtractedAnswer", foreign_keys=[answer_a_id])
    answer_b: Mapped[Optional["ExtractedAnswer"]] = relationship("ExtractedAnswer", foreign_keys=[answer_b_id])
    reviewer: Mapped[Optional["User"]] = relationship("User", foreign_keys=[reviewed_by])


class AnswerSimilarity(Base, TimestampMixin):
    __tablename__ = "answer_similarities"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=generate_uuid)
    examination_id: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("examinations.id", ondelete="CASCADE"), nullable=True, index=True)
    question_id: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("questions.id", ondelete="CASCADE"), nullable=True, index=True)
    source_answer_id: Mapped[str] = mapped_column(GUID, ForeignKey("extracted_answers.id", ondelete="CASCADE"), nullable=False, index=True)
    target_answer_id: Mapped[str] = mapped_column(GUID, ForeignKey("extracted_answers.id", ondelete="CASCADE"), nullable=False, index=True)

    similarity_score: Mapped[float] = mapped_column(Float, nullable=False)
    lexical_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    semantic_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    combined_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    flagged_for_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    method: Mapped[str] = mapped_column(String(50), default="COMBINED", nullable=False) # TFIDF, COSINE, EMBEDDING, COMBINED
    model_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    source_answer: Mapped["ExtractedAnswer"] = relationship("ExtractedAnswer", foreign_keys=[source_answer_id])
    target_answer: Mapped["ExtractedAnswer"] = relationship("ExtractedAnswer", foreign_keys=[target_answer_id])
    examination: Mapped[Optional["Examination"]] = relationship("Examination", foreign_keys=[examination_id])
    question: Mapped[Optional["Question"]] = relationship("Question", foreign_keys=[question_id])

