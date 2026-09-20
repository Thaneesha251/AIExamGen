from typing import Optional, List
from sqlalchemy import String, Text, Float, Integer, ForeignKey, UniqueConstraint, Enum as SQLEnum, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base, TimestampMixin
from backend.app.db.guid import GUID, generate_uuid
from backend.app.db.models.enums import AnswerKeyStatusEnum

class AnswerKey(Base, TimestampMixin):
    __tablename__ = "answer_keys"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=generate_uuid)
    question_paper_version_id: Mapped[str] = mapped_column(GUID, ForeignKey("question_paper_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[AnswerKeyStatusEnum] = mapped_column(SQLEnum(AnswerKeyStatusEnum), nullable=False, default=AnswerKeyStatusEnum.DRAFT, index=True)

    generated_by: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    question_paper_version: Mapped["QuestionPaperVersion"] = relationship("QuestionPaperVersion", back_populates="answer_keys")
    items: Mapped[List["AnswerKeyItem"]] = relationship("AnswerKeyItem", back_populates="answer_key", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("question_paper_version_id", "version_number", name="uq_answer_key_paper_version"),
    )


class AnswerKeyItem(Base, TimestampMixin):
    __tablename__ = "answer_key_items"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=generate_uuid)
    answer_key_id: Mapped[str] = mapped_column(GUID, ForeignKey("answer_keys.id", ondelete="CASCADE"), nullable=False, index=True)
    question_paper_item_id: Mapped[str] = mapped_column(GUID, ForeignKey("question_paper_items.id", ondelete="CASCADE"), nullable=False, index=True)

    model_answer: Mapped[str] = mapped_column(Text, nullable=False)
    keywords: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True) # Expected keywords array / weights
    concepts: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True) # Expected concepts array / weights
    acceptable_answers: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True) # Alternative acceptable answers
    marking_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    maximum_marks: Mapped[float] = mapped_column(Float, nullable=False)

    rubric_id: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("rubrics.id", ondelete="SET NULL"), nullable=True, index=True)

    answer_key: Mapped["AnswerKey"] = relationship("AnswerKey", back_populates="items")
    question_paper_item: Mapped["QuestionPaperItem"] = relationship("QuestionPaperItem", back_populates="answer_key_items")
    rubric: Mapped[Optional["Rubric"]] = relationship("Rubric")

    __table_args__ = (
        UniqueConstraint("answer_key_id", "question_paper_item_id", name="uq_answer_key_qitem_unique"),
    )
