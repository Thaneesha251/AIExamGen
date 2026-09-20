from typing import Optional, List
from sqlalchemy import String, Text, Integer, Boolean, ForeignKey, UniqueConstraint, Enum as SQLEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base, TimestampMixin
from backend.app.db.guid import GUID, generate_uuid
from backend.app.db.models.enums import BloomLevelEnum

class Department(Base, TimestampMixin):
    __tablename__ = "departments"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    users: Mapped[List["User"]] = relationship("User", back_populates="department")
    courses: Mapped[List["Course"]] = relationship("Course", back_populates="department", cascade="all, delete-orphan")
    subjects: Mapped[List["Subject"]] = relationship("Subject", back_populates="department")


class Course(Base, TimestampMixin):
    __tablename__ = "courses"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=generate_uuid)
    department_id: Mapped[str] = mapped_column(GUID, ForeignKey("departments.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_years: Mapped[int] = mapped_column(Integer, default=4, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    department: Mapped["Department"] = relationship("Department", back_populates="courses")
    subjects: Mapped[List["Subject"]] = relationship("Subject", back_populates="course", cascade="all, delete-orphan")


class Semester(Base, TimestampMixin):
    __tablename__ = "semesters"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=generate_uuid)
    number: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)

    subjects: Mapped[List["Subject"]] = relationship("Subject", back_populates="semester")


class AcademicYear(Base, TimestampMixin):
    __tablename__ = "academic_years"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True) # e.g. "2026-2027"
    start_date: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    end_date: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    subjects: Mapped[List["Subject"]] = relationship("Subject", back_populates="academic_year")


class Subject(Base, TimestampMixin):
    __tablename__ = "subjects"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=generate_uuid)
    course_id: Mapped[str] = mapped_column(GUID, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    department_id: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    semester_id: Mapped[str] = mapped_column(GUID, ForeignKey("semesters.id", ondelete="RESTRICT"), nullable=False, index=True)
    academic_year_id: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("academic_years.id", ondelete="SET NULL"), nullable=True, index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    credits: Mapped[int] = mapped_column(Integer, default=4, nullable=False)
    total_units: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    course: Mapped["Course"] = relationship("Course", back_populates="subjects")
    department: Mapped[Optional["Department"]] = relationship("Department", back_populates="subjects")
    semester: Mapped["Semester"] = relationship("Semester", back_populates="subjects")
    academic_year: Mapped[Optional["AcademicYear"]] = relationship("AcademicYear", back_populates="subjects")

    units: Mapped[List["Unit"]] = relationship("Unit", back_populates="subject", cascade="all, delete-orphan", order_by="Unit.unit_number")
    learning_outcomes: Mapped[List["LearningOutcome"]] = relationship("LearningOutcome", back_populates="subject", cascade="all, delete-orphan")
    questions: Mapped[List["Question"]] = relationship("Question", back_populates="subject")
    question_banks: Mapped[List["QuestionBank"]] = relationship("QuestionBank", back_populates="subject")
    blueprints: Mapped[List["Blueprint"]] = relationship("Blueprint", back_populates="subject")
    question_papers: Mapped[List["QuestionPaper"]] = relationship("QuestionPaper", back_populates="subject")
    examinations: Mapped[List["Examination"]] = relationship("Examination", back_populates="subject")

    __table_args__ = (
        UniqueConstraint("code", "course_id", name="uq_subject_code_course"),
    )


class Unit(Base, TimestampMixin):
    __tablename__ = "units"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=generate_uuid)
    subject_id: Mapped[str] = mapped_column(GUID, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    unit_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    weightage: Mapped[Optional[float]] = mapped_column(nullable=True)

    subject: Mapped["Subject"] = relationship("Subject", back_populates="units")
    topics: Mapped[List["Topic"]] = relationship("Topic", back_populates="unit", cascade="all, delete-orphan")
    questions: Mapped[List["Question"]] = relationship("Question", back_populates="unit")

    __table_args__ = (
        UniqueConstraint("subject_id", "unit_number", name="uq_unit_subject_number"),
    )


class Topic(Base, TimestampMixin):
    __tablename__ = "topics"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=generate_uuid)
    unit_id: Mapped[str] = mapped_column(GUID, ForeignKey("units.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    keywords: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # Comma-separated or JSON string
    importance: Mapped[Optional[str]] = mapped_column(String(50), default="MEDIUM", nullable=True)

    unit: Mapped["Unit"] = relationship("Unit", back_populates="topics")
    questions: Mapped[List["Question"]] = relationship("Question", back_populates="topic")


class LearningOutcome(Base, TimestampMixin):
    __tablename__ = "learning_outcomes"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=generate_uuid)
    subject_id: Mapped[str] = mapped_column(GUID, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False) # e.g. "CO1"
    description: Mapped[str] = mapped_column(Text, nullable=False)
    bloom_level: Mapped[BloomLevelEnum] = mapped_column(SQLEnum(BloomLevelEnum), nullable=False, default=BloomLevelEnum.UNDERSTAND)

    subject: Mapped["Subject"] = relationship("Subject", back_populates="learning_outcomes")
    questions: Mapped[List["Question"]] = relationship("Question", back_populates="learning_outcome")

    __table_args__ = (
        UniqueConstraint("subject_id", "code", name="uq_co_subject_code"),
    )


class FacultySubjectAssignment(Base, TimestampMixin):
    __tablename__ = "faculty_subject_assignments"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=generate_uuid)
    faculty_id: Mapped[str] = mapped_column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id: Mapped[str] = mapped_column(GUID, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year_id: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("academic_years.id", ondelete="SET NULL"), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    faculty: Mapped["User"] = relationship("User")
    subject: Mapped["Subject"] = relationship("Subject")
    academic_year: Mapped[Optional["AcademicYear"]] = relationship("AcademicYear")

    __table_args__ = (
        UniqueConstraint("faculty_id", "subject_id", "academic_year_id", name="uq_faculty_subject_year"),
    )

