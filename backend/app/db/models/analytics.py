from typing import Optional
from sqlalchemy import String, Float, Integer, ForeignKey, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base, TimestampMixin
from backend.app.db.guid import GUID, generate_uuid

class ExaminationAnalytics(Base, TimestampMixin):
    __tablename__ = "examination_analytics"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=generate_uuid)
    examination_id: Mapped[str] = mapped_column(GUID, ForeignKey("examinations.id", ondelete="CASCADE"), nullable=False, index=True)

    average_marks: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    median_marks: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    highest_marks: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    lowest_marks: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    pass_percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    total_students: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    evaluated_students: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    question_statistics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    unit_statistics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    difficulty_statistics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    bloom_statistics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    generated_at: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    examination: Mapped["Examination"] = relationship("Examination", back_populates="analytics_records")


class StudentPerformance(Base, TimestampMixin):
    __tablename__ = "student_performances"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=generate_uuid)
    student_id: Mapped[str] = mapped_column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    examination_id: Mapped[str] = mapped_column(GUID, ForeignKey("examinations.id", ondelete="CASCADE"), nullable=False, index=True)

    total_marks: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) # Optional institutional rank

    topic_statistics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    unit_statistics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    difficulty_statistics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    strong_topics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    weak_topics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    generated_at: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    student: Mapped["User"] = relationship("User")
    examination: Mapped["Examination"] = relationship("Examination")
