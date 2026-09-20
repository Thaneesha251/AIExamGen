from typing import Optional, List
from sqlalchemy import String, Text, Float, Integer, Boolean, ForeignKey, UniqueConstraint, Enum as SQLEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base, TimestampMixin
from backend.app.db.guid import GUID, generate_uuid
from backend.app.db.models.enums import AnswerPaperStatusEnum, ExtractionMethodEnum

class AnswerPaper(Base, TimestampMixin):
    __tablename__ = "answer_papers"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=generate_uuid)
    examination_id: Mapped[str] = mapped_column(GUID, ForeignKey("examinations.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id: Mapped[str] = mapped_column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    file_asset_id: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("file_assets.id", ondelete="SET NULL"), nullable=True, index=True)

    submission_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[AnswerPaperStatusEnum] = mapped_column(SQLEnum(AnswerPaperStatusEnum), nullable=False, default=AnswerPaperStatusEnum.UPLOADED, index=True)
    uploaded_at: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    processed_at: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    examination: Mapped["Examination"] = relationship("Examination", back_populates="answer_papers")
    student: Mapped["User"] = relationship("User")
    file_asset: Mapped[Optional["FileAsset"]] = relationship("FileAsset")

    pages: Mapped[List["AnswerPage"]] = relationship("AnswerPage", back_populates="answer_paper", cascade="all, delete-orphan", order_by="AnswerPage.page_number")
    extracted_answers: Mapped[List["ExtractedAnswer"]] = relationship("ExtractedAnswer", back_populates="answer_paper", cascade="all, delete-orphan")
    evaluations: Mapped[List["Evaluation"]] = relationship("Evaluation", back_populates="answer_paper", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("examination_id", "student_id", "submission_number", name="uq_answer_paper_student_exam_sub"),
    )


class AnswerPage(Base, TimestampMixin):
    __tablename__ = "answer_pages"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=generate_uuid)
    answer_paper_id: Mapped[str] = mapped_column(GUID, ForeignKey("answer_papers.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    file_asset_id: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("file_assets.id", ondelete="SET NULL"), nullable=True)

    ocr_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ocr_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ocr_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    processing_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    processing_status: Mapped[str] = mapped_column(String(50), default="COMPLETED", nullable=False)

    answer_paper: Mapped["AnswerPaper"] = relationship("AnswerPaper", back_populates="pages")
    file_asset: Mapped[Optional["FileAsset"]] = relationship("FileAsset")
    extracted_answers: Mapped[List["ExtractedAnswer"]] = relationship("ExtractedAnswer", back_populates="answer_page")

    __table_args__ = (
        UniqueConstraint("answer_paper_id", "page_number", name="uq_answer_page_number"),
    )


class ExtractedAnswer(Base, TimestampMixin):
    __tablename__ = "extracted_answers"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=generate_uuid)
    answer_paper_id: Mapped[str] = mapped_column(GUID, ForeignKey("answer_papers.id", ondelete="CASCADE"), nullable=False, index=True)
    question_paper_item_id: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("question_paper_items.id", ondelete="SET NULL"), nullable=True, index=True)
    answer_page_id: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("answer_pages.id", ondelete="SET NULL"), nullable=True)

    question_number: Mapped[str] = mapped_column(String(20), nullable=False) # e.g. "1a", "Q2"
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False)
    extraction_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ocr_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    segmentation_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    page_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    page_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    extraction_method: Mapped[ExtractionMethodEnum] = mapped_column(SQLEnum(ExtractionMethodEnum), nullable=False, default=ExtractionMethodEnum.OCR)
    manually_corrected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)

    answer_paper: Mapped["AnswerPaper"] = relationship("AnswerPaper", back_populates="extracted_answers")
    question_paper_item: Mapped[Optional["QuestionPaperItem"]] = relationship("QuestionPaperItem", back_populates="extracted_answers")
    answer_page: Mapped[Optional["AnswerPage"]] = relationship("AnswerPage", back_populates="extracted_answers")
    evaluation_items: Mapped[List["EvaluationItem"]] = relationship("EvaluationItem", back_populates="extracted_answer")

