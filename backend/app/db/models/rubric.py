from typing import Optional, List
from sqlalchemy import String, Text, Float, Integer, Boolean, ForeignKey, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base, TimestampMixin
from backend.app.db.guid import GUID, generate_uuid

class Rubric(Base, TimestampMixin):
    __tablename__ = "rubrics"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=generate_uuid)
    question_id: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("questions.id", ondelete="CASCADE"), nullable=True, index=True)
    question_paper_item_id: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("question_paper_items.id", ondelete="CASCADE"), nullable=True, index=True)
    subject_id: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True, index=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    question_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    total_marks: Mapped[float] = mapped_column(Float, nullable=False, default=10.0)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="DRAFT")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_by: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    question: Mapped[Optional["Question"]] = relationship("Question", back_populates="rubrics")
    question_paper_item: Mapped[Optional["QuestionPaperItem"]] = relationship("QuestionPaperItem")
    subject: Mapped[Optional["Subject"]] = relationship("Subject")
    criteria: Mapped[List["RubricCriterion"]] = relationship("RubricCriterion", back_populates="rubric", cascade="all, delete-orphan", order_by="RubricCriterion.order_index")


class RubricCriterion(Base, TimestampMixin):
    __tablename__ = "rubric_criteria"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=generate_uuid)
    rubric_id: Mapped[str] = mapped_column(GUID, ForeignKey("rubrics.id", ondelete="CASCADE"), nullable=False, index=True)
    criterion: Mapped[str] = mapped_column(String(255), nullable=False) # e.g. "Definition", "Working Principle"
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    marks: Mapped[float] = mapped_column(Float, nullable=False, default=2.0)
    min_marks: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    partial_credit_rules: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    rubric: Mapped["Rubric"] = relationship("Rubric", back_populates="criteria")

