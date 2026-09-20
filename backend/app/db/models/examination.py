from typing import Optional, List
from sqlalchemy import String, Text, Float, Integer, ForeignKey, UniqueConstraint, Enum as SQLEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base, TimestampMixin
from backend.app.db.guid import GUID, generate_uuid
from backend.app.db.models.enums import ExamStatusEnum, AttendanceStatusEnum

class Examination(Base, TimestampMixin):
    __tablename__ = "examinations"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=generate_uuid)
    subject_id: Mapped[str] = mapped_column(GUID, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    question_paper_id: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("question_papers.id", ondelete="SET NULL"), nullable=True, index=True)
    question_paper_version_id: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("question_paper_versions.id", ondelete="SET NULL"), nullable=True, index=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False) # e.g. "Mid-Semester Examination Spring 2026"
    examination_type: Mapped[str] = mapped_column(String(50), default="REGULAR", nullable=False) # REGULAR, REEXAM, INTERNAL
    exam_date: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    start_time: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=180, nullable=False)
    total_marks: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    status: Mapped[ExamStatusEnum] = mapped_column(SQLEnum(ExamStatusEnum), nullable=False, default=ExamStatusEnum.DRAFT, index=True)
    created_by: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    subject: Mapped["Subject"] = relationship("Subject", back_populates="examinations")
    question_paper: Mapped[Optional["QuestionPaper"]] = relationship("QuestionPaper", back_populates="examinations")
    question_paper_version: Mapped[Optional["QuestionPaperVersion"]] = relationship("QuestionPaperVersion", back_populates="examinations")

    participating_students: Mapped[List["ExaminationStudent"]] = relationship("ExaminationStudent", back_populates="examination", cascade="all, delete-orphan")
    answer_papers: Mapped[List["AnswerPaper"]] = relationship("AnswerPaper", back_populates="examination", cascade="all, delete-orphan")
    evaluations: Mapped[List["Evaluation"]] = relationship("Evaluation", back_populates="examination", cascade="all, delete-orphan")
    analytics_records: Mapped[List["ExaminationAnalytics"]] = relationship("ExaminationAnalytics", back_populates="examination", cascade="all, delete-orphan")


class ExaminationStudent(Base, TimestampMixin):
    __tablename__ = "examination_students"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=generate_uuid)
    examination_id: Mapped[str] = mapped_column(GUID, ForeignKey("examinations.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id: Mapped[str] = mapped_column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    registration_number_snapshot: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    attendance_status: Mapped[AttendanceStatusEnum] = mapped_column(SQLEnum(AttendanceStatusEnum), nullable=False, default=AttendanceStatusEnum.PRESENT)
    final_marks: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    result_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # PASS, FAIL, PENDING

    examination: Mapped["Examination"] = relationship("Examination", back_populates="participating_students")
    student: Mapped["User"] = relationship("User")

    __table_args__ = (
        UniqueConstraint("examination_id", "student_id", name="uq_exam_student_unique"),
    )
