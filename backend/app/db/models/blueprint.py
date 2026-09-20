from typing import Optional, List
from sqlalchemy import String, Text, Float, Integer, ForeignKey, Enum as SQLEnum, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base, TimestampMixin
from backend.app.db.guid import GUID, generate_uuid
from backend.app.db.models.enums import BlueprintStatusEnum, QuestionTypeEnum, DifficultyLevelEnum, BloomLevelEnum

class Blueprint(Base, TimestampMixin):
    __tablename__ = "blueprints"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=generate_uuid)
    subject_id: Mapped[str] = mapped_column(GUID, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    total_marks: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=180)
    status: Mapped[BlueprintStatusEnum] = mapped_column(SQLEnum(BlueprintStatusEnum), nullable=False, default=BlueprintStatusEnum.DRAFT, index=True)
    created_by: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    subject: Mapped["Subject"] = relationship("Subject", back_populates="blueprints")
    rules: Mapped[List["BlueprintRule"]] = relationship("BlueprintRule", back_populates="blueprint", cascade="all, delete-orphan", order_by="BlueprintRule.section, BlueprintRule.order_index")
    question_papers: Mapped[List["QuestionPaper"]] = relationship("QuestionPaper", back_populates="blueprint")


class BlueprintRule(Base, TimestampMixin):
    __tablename__ = "blueprint_rules"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=generate_uuid)
    blueprint_id: Mapped[str] = mapped_column(GUID, ForeignKey("blueprints.id", ondelete="CASCADE"), nullable=False, index=True)
    section: Mapped[str] = mapped_column(String(50), nullable=False, default="Section A") # e.g. "Section A", "Part B"
    question_count: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    marks_per_question: Mapped[float] = mapped_column(Float, nullable=False, default=2.0)
    total_marks: Mapped[float] = mapped_column(Float, nullable=False, default=20.0)

    unit_id: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("units.id", ondelete="SET NULL"), nullable=True)
    difficulty: Mapped[Optional[DifficultyLevelEnum]] = mapped_column(SQLEnum(DifficultyLevelEnum), nullable=True)
    bloom_level: Mapped[Optional[BloomLevelEnum]] = mapped_column(SQLEnum(BloomLevelEnum), nullable=True)
    question_type: Mapped[Optional[QuestionTypeEnum]] = mapped_column(SQLEnum(QuestionTypeEnum), nullable=True)

    distribution_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True) # Detailed per-unit, per-bloom, per-difficulty, per-type distributions
    minimum_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    maximum_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    blueprint: Mapped["Blueprint"] = relationship("Blueprint", back_populates="rules")
    unit: Mapped[Optional["Unit"]] = relationship("Unit")
