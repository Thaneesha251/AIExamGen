from typing import Optional, List
from sqlalchemy import String, Text, Integer, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base, TimestampMixin
from backend.app.db.guid import GUID, generate_uuid

class QuestionGenerationRun(Base, TimestampMixin):
    __tablename__ = "question_generation_runs"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=generate_uuid)
    subject_id: Mapped[str] = mapped_column(GUID, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    unit_id: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("units.id", ondelete="SET NULL"), nullable=True, index=True)
    topic_id: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("topics.id", ondelete="SET NULL"), nullable=True, index=True)
    learning_outcome_id: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("learning_outcomes.id", ondelete="SET NULL"), nullable=True, index=True)
    created_by: Mapped[str] = mapped_column(GUID, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    provider: Mapped[str] = mapped_column(String(50), default="mock", nullable=False)
    model: Mapped[str] = mapped_column(String(100), default="mock-model", nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(50), default="v1", nullable=False)
    configuration_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    status: Mapped[str] = mapped_column(String(50), default="COMPLETED", nullable=False, index=True) # PENDING, PROCESSING, COMPLETED, FAILED
    requested_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    generated_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    accepted_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rejected_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    subject: Mapped["Subject"] = relationship("Subject")
    creator: Mapped["User"] = relationship("User")
    questions: Mapped[List["Question"]] = relationship("Question", back_populates="generation_run")
