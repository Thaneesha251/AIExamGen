from typing import Optional, List
from sqlalchemy import String, Text, Float, Integer, ForeignKey, UniqueConstraint, Enum as SQLEnum, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base, TimestampMixin
from backend.app.db.guid import GUID, generate_uuid
from backend.app.db.models.enums import QuestionPaperStatusEnum, PaperGenerationMethodEnum

class QuestionPaper(Base, TimestampMixin):
    __tablename__ = "question_papers"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=generate_uuid)
    subject_id: Mapped[str] = mapped_column(GUID, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    blueprint_id: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("blueprints.id", ondelete="SET NULL"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    paper_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    total_marks: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=180)
    status: Mapped[QuestionPaperStatusEnum] = mapped_column(SQLEnum(QuestionPaperStatusEnum), nullable=False, default=QuestionPaperStatusEnum.DRAFT, index=True)
    created_by: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    subject: Mapped["Subject"] = relationship("Subject", back_populates="question_papers")
    blueprint: Mapped[Optional["Blueprint"]] = relationship("Blueprint", back_populates="question_papers")
    versions: Mapped[List["QuestionPaperVersion"]] = relationship("QuestionPaperVersion", back_populates="question_paper", cascade="all, delete-orphan", order_by="QuestionPaperVersion.version_number.desc()")
    examinations: Mapped[List["Examination"]] = relationship("Examination", back_populates="question_paper")


class QuestionPaperVersion(Base, TimestampMixin):
    __tablename__ = "question_paper_versions"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=generate_uuid)
    question_paper_id: Mapped[str] = mapped_column(GUID, ForeignKey("question_papers.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    generation_method: Mapped[PaperGenerationMethodEnum] = mapped_column(SQLEnum(PaperGenerationMethodEnum), nullable=False, default=PaperGenerationMethodEnum.HYBRID)
    generated_by: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    generation_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True) # AI model, timestamp, parameters

    question_paper: Mapped["QuestionPaper"] = relationship("QuestionPaper", back_populates="versions")
    items: Mapped[List["QuestionPaperItem"]] = relationship("QuestionPaperItem", back_populates="version", cascade="all, delete-orphan", order_by="QuestionPaperItem.order_index")
    answer_keys: Mapped[List["AnswerKey"]] = relationship("AnswerKey", back_populates="question_paper_version", cascade="all, delete-orphan")
    examinations: Mapped[List["Examination"]] = relationship("Examination", back_populates="question_paper_version")

    __table_args__ = (
        UniqueConstraint("question_paper_id", "version_number", name="uq_paper_version_number"),
    )


class QuestionPaperItem(Base, TimestampMixin):
    __tablename__ = "question_paper_items"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=generate_uuid)
    question_paper_version_id: Mapped[str] = mapped_column(GUID, ForeignKey("question_paper_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("questions.id", ondelete="SET NULL"), nullable=True, index=True)

    section: Mapped[str] = mapped_column(String(50), nullable=False, default="Section A")
    question_number: Mapped[str] = mapped_column(String(20), nullable=False) # e.g. "1a", "2", "Q15"
    marks: Mapped[float] = mapped_column(Float, nullable=False)

    # CRITICAL: Snapshot of actual question text & properties used in the historical exam paper
    question_text_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    options_snapshot: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    question_type_snapshot: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    difficulty_snapshot: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    bloom_snapshot: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    version: Mapped["QuestionPaperVersion"] = relationship("QuestionPaperVersion", back_populates="items")
    question: Mapped[Optional["Question"]] = relationship("Question")
    answer_key_items: Mapped[List["AnswerKeyItem"]] = relationship("AnswerKeyItem", back_populates="question_paper_item")
    extracted_answers: Mapped[List["ExtractedAnswer"]] = relationship("ExtractedAnswer", back_populates="question_paper_item")
    evaluation_items: Mapped[List["EvaluationItem"]] = relationship("EvaluationItem", back_populates="question_paper_item")

    __table_args__ = (
        UniqueConstraint("question_paper_version_id", "question_number", name="uq_paper_version_qnumber"),
    )
