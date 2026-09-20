from typing import Optional, List
from sqlalchemy import String, Text, Float, Integer, ForeignKey, UniqueConstraint, Enum as SQLEnum, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base, TimestampMixin
from backend.app.db.guid import GUID, generate_uuid
from backend.app.db.models.enums import QuestionTypeEnum, DifficultyLevelEnum, BloomLevelEnum, QuestionStatusEnum

class Question(Base, TimestampMixin):
    __tablename__ = "questions"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=generate_uuid)
    subject_id: Mapped[str] = mapped_column(GUID, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    unit_id: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("units.id", ondelete="SET NULL"), nullable=True, index=True)
    topic_id: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("topics.id", ondelete="SET NULL"), nullable=True, index=True)
    learning_outcome_id: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("learning_outcomes.id", ondelete="SET NULL"), nullable=True, index=True)

    generation_run_id: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("question_generation_runs.id", ondelete="SET NULL"), nullable=True, index=True)

    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[QuestionTypeEnum] = mapped_column(SQLEnum(QuestionTypeEnum), nullable=False, index=True)
    marks: Mapped[float] = mapped_column(Float, nullable=False, default=2.0)
    difficulty: Mapped[DifficultyLevelEnum] = mapped_column(SQLEnum(DifficultyLevelEnum), nullable=False, default=DifficultyLevelEnum.MEDIUM, index=True)
    bloom_level: Mapped[BloomLevelEnum] = mapped_column(SQLEnum(BloomLevelEnum), nullable=False, default=BloomLevelEnum.UNDERSTAND, index=True)

    expected_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    options: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True) # e.g. {"options": ["A", "B", "C", "D"], "correct_option": "A"}
    keywords: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True) # e.g. ["binary search", "O(log n)"]
    concepts: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True) # e.g. ["divide and conquer", "sorted array"]
    validation_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True) # e.g. alignment_score, duplicate_score, warnings

    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    source: Mapped[Optional[str]] = mapped_column(String(100), default="MANUAL", nullable=True) # AI_GENERATED, MANUAL, IMPORTED
    status: Mapped[QuestionStatusEnum] = mapped_column(SQLEnum(QuestionStatusEnum), nullable=False, default=QuestionStatusEnum.ACTIVE, index=True)
    created_by: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    subject: Mapped["Subject"] = relationship("Subject", back_populates="questions")
    unit: Mapped[Optional["Unit"]] = relationship("Unit", back_populates="questions")
    topic: Mapped[Optional["Topic"]] = relationship("Topic", back_populates="questions")
    learning_outcome: Mapped[Optional["LearningOutcome"]] = relationship("LearningOutcome", back_populates="questions")
    generation_run: Mapped[Optional["QuestionGenerationRun"]] = relationship("QuestionGenerationRun", back_populates="questions")

    bank_items: Mapped[List["QuestionBankItem"]] = relationship("QuestionBankItem", back_populates="question", cascade="all, delete-orphan")
    versions: Mapped[List["QuestionVersion"]] = relationship("QuestionVersion", back_populates="question", cascade="all, delete-orphan", order_by="QuestionVersion.version_number.desc()")
    rubrics: Mapped[List["Rubric"]] = relationship("Rubric", back_populates="question", cascade="all, delete-orphan")



class QuestionBank(Base, TimestampMixin):
    __tablename__ = "question_banks"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=generate_uuid)
    subject_id: Mapped[str] = mapped_column(GUID, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    subject: Mapped["Subject"] = relationship("Subject", back_populates="question_banks")
    items: Mapped[List["QuestionBankItem"]] = relationship("QuestionBankItem", back_populates="question_bank", cascade="all, delete-orphan")


class QuestionBankItem(Base, TimestampMixin):
    __tablename__ = "question_bank_items"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=generate_uuid)
    question_bank_id: Mapped[str] = mapped_column(GUID, ForeignKey("question_banks.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id: Mapped[str] = mapped_column(GUID, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    added_by: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    question_bank: Mapped["QuestionBank"] = relationship("QuestionBank", back_populates="items")
    question: Mapped["Question"] = relationship("Question", back_populates="bank_items")

    __table_args__ = (
        UniqueConstraint("question_bank_id", "question_id", name="uq_bank_question_unique"),
    )


class QuestionVersion(Base, TimestampMixin):
    __tablename__ = "question_versions"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=generate_uuid)
    question_id: Mapped[str] = mapped_column(GUID, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    marks: Mapped[float] = mapped_column(Float, nullable=False)
    difficulty: Mapped[DifficultyLevelEnum] = mapped_column(SQLEnum(DifficultyLevelEnum), nullable=False)
    bloom_level: Mapped[BloomLevelEnum] = mapped_column(SQLEnum(BloomLevelEnum), nullable=False)
    expected_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    options: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    keywords: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    concepts: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    changed_by: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    change_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    question: Mapped["Question"] = relationship("Question", back_populates="versions")

    __table_args__ = (
        UniqueConstraint("question_id", "version_number", name="uq_question_version_number"),
    )
